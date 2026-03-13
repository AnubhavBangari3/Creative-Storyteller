import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image
from django.conf import settings
from google import genai

from .storage_service import GCSStorageService
from .vertex_imagen_service import VertexImagenService


class GeminiImageService:
    def __init__(self):
        self.gemini_api_key = (getattr(settings, "GEMINI_API_KEY", "") or "").strip()
        self.gemini_enabled = bool(self.gemini_api_key)
        self.client = genai.Client(api_key=self.gemini_api_key) if self.gemini_enabled else None
        self.model = getattr(settings, "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

        self.vertex_image_enabled = getattr(settings, "VERTEX_IMAGE_ENABLED", False)
        self.vertex_service = VertexImagenService() if self.vertex_image_enabled else None

        self.use_gcs_for_images = getattr(settings, "USE_GCS_FOR_IMAGES", False)
        self.storage_service = GCSStorageService() if self.use_gcs_for_images else None

        self.output_dir = Path(settings.MEDIA_ROOT) / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("USING IMAGE MODEL:", self.model)
        print("VERTEX IMAGE ENABLED:", self.vertex_image_enabled)

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
            extension=extension,
        )
        content_type = "image/png" if extension.lower() == "png" else "image/jpeg"
        return self.storage_service.upload_bytes(
            file_bytes=image_bytes,
            destination_blob_name=filename,
            content_type=content_type,
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

        print("GEMINI IMAGE REQUEST STARTED")
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"response_modalities": ["IMAGE", "TEXT"]},
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
        if self.vertex_image_enabled and self.vertex_service:
            return self.vertex_service.generate_image_from_prompt(prompt)

        if not self.gemini_enabled:
            raise ValueError("No image provider is enabled.")

        return self._generate_with_gemini(prompt)

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
                raw_error = str(exc)
                error_text = raw_error.lower()
                print("IMAGE GENERATION ERROR:", raw_error)

                scene_copy["image_url"] = ""
                scene_copy["image_generation_skipped"] = True
                scene_copy["image_generation_error"] = raw_error

                if "resource_exhausted" in error_text or "quota" in error_text:
                    reason = "quota_exceeded"
                elif "permission" in error_text or "403" in error_text:
                    reason = "permission_denied"
                elif "unauthenticated" in error_text or "401" in error_text:
                    reason = "auth_failed"
                elif "rai reason" in error_text:
                    reason = "rai_filtered"
                elif "file not found" in error_text or "credentials" in error_text:
                    reason = "provider_not_configured"
                elif "consumer invalid" in error_text or "account verification" in error_text:
                    reason = "billing_or_project_not_ready"
                elif "publisher model" in error_text or "not found" in error_text:
                    reason = "model_not_available"
                else:
                    reason = "generation_failed"

                scene_copy["image_generation_reason"] = reason

            updated_scenes.append(scene_copy)

        return updated_scenes
