from io import BytesIO
from uuid import uuid4

from django.conf import settings
from google.cloud import storage
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel


class VertexImagenService:
    def __init__(self):
        self.project_id = (getattr(settings, "GCP_PROJECT_ID", "") or "").strip()
        self.bucket_name = (getattr(settings, "GCP_BUCKET_NAME", "") or "").strip()
        self.location = (
            getattr(settings, "VERTEX_IMAGE_LOCATION", "asia-southeast1")
            or "asia-southeast1"
        ).strip()
        self.model_name = (
            getattr(settings, "VERTEX_IMAGE_MODEL", "imagen-4.0-generate-001")
            or "imagen-4.0-generate-001"
        ).strip()

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID is missing.")

        if not self.bucket_name:
            raise ValueError("GCP_BUCKET_NAME is missing.")

        print("VERTEX IMAGE SERVICE INITIALIZING...")
        print("VERTEX PROJECT:", self.project_id)
        print("VERTEX LOCATION:", self.location)
        print("VERTEX MODEL:", self.model_name)
        print("VERTEX BUCKET:", self.bucket_name)

        vertexai.init(project=self.project_id, location=self.location)
        self.storage_client = storage.Client(project=self.project_id)

    def _upload_image_bytes_to_gcs(
        self,
        image_bytes: bytes,
        filename_prefix: str = "scene",
        extension: str = "png",
    ) -> str:
        if not image_bytes:
            raise ValueError("Generated image bytes are empty.")

        object_name = f"story-images/{filename_prefix}-{uuid4().hex}.{extension}"

        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(object_name)

        content_type = "image/png" if extension.lower() == "png" else "image/jpeg"

        blob.upload_from_file(
            BytesIO(image_bytes),
            content_type=content_type,
        )

        exists = blob.exists(self.storage_client)
        print("GCS OBJECT NAME:", object_name)
        print("BLOB EXISTS AFTER UPLOAD:", exists)

        if not exists:
            raise ValueError("Image upload failed: blob does not exist after upload.")

        # Return normal public URL
        # Bucket/object must be readable via IAM for browser access.
        public_url = f"https://storage.googleapis.com/{self.bucket_name}/{object_name}"
        print("IMAGE PUBLIC URL:", public_url)
        return public_url

    def generate_image(self, prompt: str, filename_prefix: str = "scene") -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt is empty.")

        print("VERTEX IMAGEN REQUEST STARTED")
        print("VERTEX PROMPT:", prompt)

        model = ImageGenerationModel.from_pretrained(self.model_name)

        result = model.generate_images(
            prompt=prompt,
            number_of_images=1,
        )

        if not result or not result.images:
            raise ValueError("Vertex Imagen returned no images.")

        generated_image = result.images[0]
        image_bytes = getattr(generated_image, "_image_bytes", None)

        if not image_bytes:
            raise ValueError("Generated image bytes are empty.")

        return self._upload_image_bytes_to_gcs(
            image_bytes=image_bytes,
            filename_prefix=filename_prefix,
            extension="png",
        )

    # backward-compatible method name
    def generate_image_from_prompt(self, prompt: str, filename_prefix: str = "scene") -> str:
        return self.generate_image(prompt=prompt, filename_prefix=filename_prefix)