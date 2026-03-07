import base64
import uuid
from pathlib import Path
from typing import List, Dict, Any

from django.conf import settings
from google import genai
from google.genai import types


class GeminiImageService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing in .env")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = getattr(settings, "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

        self.output_dir = Path(settings.MEDIA_ROOT) / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_image_bytes(self, image_bytes: bytes, extension: str = ".png") -> str:
        filename = f"{uuid.uuid4().hex}{extension}"
        filepath = self.output_dir / filename

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return f"{settings.MEDIA_URL}generated_images/{filename}"

    def _extract_image_bytes(self, generated_image) -> bytes:
        # Most common current SDK shape:
        # generated_image.image.image_bytes
        nested_image = getattr(generated_image, "image", None)
        if nested_image is not None:
            nested_bytes = getattr(nested_image, "image_bytes", None)
            if nested_bytes:
                return nested_bytes

            nested_b64 = getattr(nested_image, "b64_json", None)
            if nested_b64:
                return base64.b64decode(nested_b64)

        # Fallbacks for other possible SDK shapes
        direct_bytes = getattr(generated_image, "image_bytes", None)
        if direct_bytes:
            return direct_bytes

        raw_bytes = getattr(generated_image, "bytes", None)
        if raw_bytes:
            return raw_bytes

        b64_data = getattr(generated_image, "b64_json", None)
        if b64_data:
            return base64.b64decode(b64_data)

        raise ValueError("Unsupported image response format from SDK.")

    def generate_image_from_prompt(self, prompt: str) -> str:
        print("IMAGE PROMPT:", prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": f"Generate a cinematic image for: {prompt}"}
                    ],
                }
            ],
        )

        print("RAW RESPONSE:", response)

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data"):
                image_bytes = part.inline_data.data
                return self._save_image_bytes(image_bytes)

        raise ValueError("No image returned from Gemini model.")

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

            except Exception as exc:
                error_text = str(exc)

                print("IMAGE GENERATION SKIPPED:", error_text)

                # graceful fallback
                scene_copy["image_url"] = ""
                scene_copy["image_generation_skipped"] = True

                if "quota" in error_text.lower():
                    scene_copy["image_generation_reason"] = "quota_exceeded"
                elif "not found" in error_text.lower():
                    scene_copy["image_generation_reason"] = "model_not_available"
                else:
                    scene_copy["image_generation_reason"] = "generation_failed"

            updated_scenes.append(scene_copy)

        return updated_scenes