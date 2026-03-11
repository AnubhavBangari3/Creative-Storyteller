import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import quote

import requests
from PIL import Image
from django.conf import settings
from google import genai

from .storage_service import GCSStorageService


class GeminiImageService:
    def __init__(self):
        self.gemini_enabled = bool(getattr(settings, "GEMINI_API_KEY", ""))
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if self.gemini_enabled else None
        self.model = getattr(settings, "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

        self.pollinations_enabled = getattr(settings, "POLLINATIONS_ENABLED", True)
        self.pollinations_api_key = getattr(settings, "POLLINATIONS_API_KEY", "")
        self.pollinations_model = getattr(settings, "POLLINATIONS_IMAGE_MODEL", "flux")
        self.pollinations_width = getattr(settings, "POLLINATIONS_IMAGE_WIDTH", 1024)
        self.pollinations_height = getattr(settings, "POLLINATIONS_IMAGE_HEIGHT", 1024)

        print("USING IMAGE MODEL:", self.model)
        print("POLLINATIONS ENABLED:", self.pollinations_enabled)
        print("POLLINATIONS MODEL:", self.pollinations_model)

        self.use_gcs_for_images = getattr(settings, "USE_GCS_FOR_IMAGES", False)
        self.storage_service = GCSStorageService() if self.use_gcs_for_images else None

        self.output_dir = Path(settings.MEDIA_ROOT) / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_image_locally(self, image_bytes: bytes, extension: str = ".png") -> str:
        filename = f"{uuid.uuid4().hex}{extension}"
        filepath = self.output_dir / filename

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return f"{settings.MEDIA_URL}generated_images/{filename}"

    def _upload_image_to_gcs(self, image_bytes: bytes, extension: str = "png") -> str:
        if not self.storage_service:
            raise ValueError("GCS storage service is not initialized for images.")

        filename = self.storage_service.generate_unique_filename(
            prefix="generated_images",
            extension=extension
        )

        content_type = "image/png" if extension == "png" else "image/jpeg"

        return self.storage_service.upload_bytes(
            file_bytes=image_bytes,
            destination_blob_name=filename,
            content_type=content_type
        )

    def _store_image(self, image_bytes: bytes, extension: str = "png") -> str:
        if self.use_gcs_for_images:
            return self._upload_image_to_gcs(image_bytes, extension=extension)
        return self._save_image_locally(image_bytes, extension=f".{extension}")

    def _normalize_to_png(self, image_bytes: bytes) -> bytes:
        """
        Converts returned image bytes into PNG bytes for consistency.
        """
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            output = BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()
        except Exception:
            # If PIL cannot decode it, return original bytes as-is
            return image_bytes

    def _generate_with_gemini(self, prompt: str) -> str:
        if not self.client:
            raise ValueError("Gemini image client is not configured.")

        print("USING IMAGE MODEL:", self.model)
        print("IMAGE PROMPT:", prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_modalities": ["IMAGE", "TEXT"]
            },
        )

        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    image_bytes = inline_data.data
                    png_bytes = self._normalize_to_png(image_bytes)
                    return self._store_image(png_bytes, extension="png")

        raise ValueError("No image returned from Gemini model.")
    def _generate_with_pollinations(self, prompt: str) -> str:
        if not self.pollinations_enabled:
            raise ValueError("Pollinations fallback is disabled.")

        if not self.pollinations_api_key:
            raise ValueError("Pollinations API key is missing.")

        encoded_prompt = quote(prompt, safe="")
        url = f"https://gen.pollinations.ai/image/{encoded_prompt}"

        headers = {
            "Authorization": f"Bearer {self.pollinations_api_key}"
        }

        params = {
            "model": self.pollinations_model,
            "width": self.pollinations_width,
            "height": self.pollinations_height,
        }

        print("POLLINATIONS URL:", url)
        print("POLLINATIONS PARAMS:", params)

        response = requests.get(url, headers=headers, params=params, timeout=120)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if "image" not in content_type:
            raise ValueError(f"Pollinations returned non-image response: {response.text[:300]}")

        png_bytes = self._normalize_to_png(response.content)
        return self._store_image(png_bytes, extension="png")
   
    def generate_image_from_prompt(self, prompt: str) -> str:
        gemini_error = None

        # Try Gemini first
        if self.gemini_enabled:
            try:
                return self._generate_with_gemini(prompt)
            except Exception as exc:
                gemini_error = str(exc)
                print("GEMINI IMAGE FAILED:", gemini_error)

        # Fallback to Pollinations
        if self.pollinations_enabled:
            try:
                print("FALLING BACK TO POLLINATIONS...")
                return self._generate_with_pollinations(prompt)
            except Exception as exc:
                pollinations_error = str(exc)
                print("POLLINATIONS IMAGE FAILED:", pollinations_error)
                if gemini_error:
                    raise ValueError(
                        f"gemini_failed: {gemini_error} | pollinations_failed: {pollinations_error}"
                    )
                raise ValueError(f"pollinations_failed: {pollinations_error}")

        if gemini_error:
            raise ValueError(gemini_error)

        raise ValueError("No image provider is enabled.")

    def generate_images_for_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        updated_scenes = []

        for scene in scenes:
            scene_copy = dict(scene)
            visual_prompt = scene_copy.get("visual_prompt", "").strip()

            if not visual_prompt:
                scene_copy["image_url"] = ""
                scene_copy["image_generation_skipped"] = True
                scene_copy["image_generation_reason"] = "missing_prompt"
                updated_scenes.append(scene_copy)
                continue

            try:
                image_url = self.generate_image_from_prompt(visual_prompt)
                scene_copy["image_url"] = image_url
                scene_copy["image_generation_skipped"] = False
                scene_copy["image_generation_reason"] = ""
            except Exception as exc:
                error_text = str(exc)
                print("IMAGE GENERATION SKIPPED:", error_text)

                scene_copy["image_url"] = ""
                scene_copy["image_generation_skipped"] = True

                lowered = error_text.lower()
                if "quota" in lowered or "resource_exhausted" in lowered:
                    scene_copy["image_generation_reason"] = "quota_exceeded"
                elif "not found" in lowered:
                    scene_copy["image_generation_reason"] = "model_not_available"
                elif "pollinations_failed" in lowered:
                    scene_copy["image_generation_reason"] = "fallback_failed"
                else:
                    scene_copy["image_generation_reason"] = "generation_failed"

            updated_scenes.append(scene_copy)

        return updated_scenes