import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image
from django.conf import settings
from google import genai

from .storage_service import GCSStorageService


class GeminiImageService:
    def __init__(self):
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
        self.gemini_enabled = bool(self.gemini_api_key)
        self.client = genai.Client(api_key=self.gemini_api_key) if self.gemini_enabled else None
        self.model = getattr(settings, "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

        self.use_gcs_for_images = getattr(settings, "USE_GCS_FOR_IMAGES", False)
        self.storage_service = GCSStorageService() if self.use_gcs_for_images else None

        self.output_dir = Path(settings.MEDIA_ROOT) / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("USING IMAGE MODEL:", self.model)

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

        content_type = "image/png" if extension.lower() == "png" else "image/jpeg"

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
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

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

    def generate_image_from_prompt(self, prompt: str) -> str:
        if not self.gemini_enabled:
            raise ValueError("Gemini image generation is not enabled.")

        try:
            return self._generate_with_gemini(prompt)
        except Exception as exc:
            gemini_error = str(exc)
            print("GEMINI IMAGE FAILED:", gemini_error)
            raise ValueError(gemini_error)

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
                elif "not configured" in lowered or "not enabled" in lowered:
                    scene_copy["image_generation_reason"] = "gemini_not_configured"
                elif "not found" in lowered:
                    scene_copy["image_generation_reason"] = "model_not_available"
                else:
                    scene_copy["image_generation_reason"] = "generation_failed"

            updated_scenes.append(scene_copy)

        return updated_scenes