import base64
import uuid
from pathlib import Path
from typing import Optional

import requests
from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from .storage_service import GCSStorageService


class VertexImagenService:
    def __init__(self):
        self.project_id = getattr(settings, "GCP_PROJECT_ID", "").strip()
        self.location = getattr(settings, "VERTEX_IMAGE_LOCATION", "us-central1").strip()
        self.model = getattr(settings, "VERTEX_IMAGE_MODEL", "imagen-4.0-generate-001").strip()
        self.credentials_path = getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", "").strip()

        self.use_gcs_for_images = getattr(settings, "USE_GCS_FOR_IMAGES", False)
        self.storage_service = GCSStorageService() if self.use_gcs_for_images else None

        self.output_dir = Path(settings.MEDIA_ROOT) / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID is missing.")
        if not self.credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is missing.")

    def _get_access_token(self) -> str:
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=scopes,
        )
        credentials.refresh(Request())
        return credentials.token

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

    def generate_image_from_prompt(self, prompt: str) -> str:
        token = self._get_access_token()

        url = (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project_id}/locations/{self.location}/"
            f"publishers/google/models/{self.model}:predict"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "addWatermark": True,
                "enhancePrompt": True,
                "outputOptions": {
                    "mimeType": "image/png"
                }
            },
        }

        response = requests.post(url, headers=headers, json=payload, timeout=180)

        if response.status_code >= 400:
            raise ValueError(
                f"Vertex Imagen failed: {response.status_code} - {response.text[:1000]}"
            )

        data = response.json()
        predictions = data.get("predictions", [])

        if not predictions:
            raise ValueError(f"Vertex Imagen returned no predictions: {str(data)[:1000]}")

        first = predictions[0]
        image_b64 = first.get("bytesBase64Encoded")

        if not image_b64:
            rai_reason = first.get("raiFilteredReason", "")
            raise ValueError(
                f"Vertex Imagen returned no image bytes. RAI reason: {rai_reason or 'unknown'}"
            )

        image_bytes = base64.b64decode(image_b64)
        return self._store_image(image_bytes, extension="png")