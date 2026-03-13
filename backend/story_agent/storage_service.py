import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from google.cloud import storage


class GCSStorageService:
    def __init__(self):
        self.project_id = getattr(settings, "GCP_PROJECT_ID", "").strip()
        self.bucket_name = getattr(settings, "GCP_BUCKET_NAME", "").strip()

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID is missing.")

        if not self.bucket_name:
            raise ValueError("GCP_BUCKET_NAME is missing.")

        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)

        print("GCS STORAGE SERVICE INITIALIZED")
        print("GCS PROJECT ID:", self.project_id)
        print("GCS BUCKET NAME:", self.bucket_name)

    def generate_unique_filename(self, prefix: str = "files", extension: str = "bin") -> str:
        extension = extension.lstrip(".")
        unique_id = uuid.uuid4().hex
        return f"{prefix}/{unique_id}.{extension}"

    def _generate_signed_url(self, blob) -> str:
        expiration_minutes = int(
            getattr(settings, "GCS_SIGNED_URL_EXPIRATION_MINUTES", 10080)  # 7 days
        )

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )

        return signed_url

    def upload_bytes(self, file_bytes: bytes, destination_blob_name: str, content_type: str = None) -> str:
        print("UPLOADING BYTES TO GCS...")
        print("DESTINATION BLOB:", destination_blob_name)
        print("CONTENT TYPE:", content_type)

        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)

        file_url = self._generate_signed_url(blob)

        print("GCS UPLOAD SUCCESSFUL")
        print("SIGNED URL GENERATED")
        return file_url

    def upload_file(self, local_file_path: str, destination_blob_name: str, content_type: str = None) -> str:
        print("UPLOADING FILE TO GCS...")
        print("LOCAL FILE PATH:", local_file_path)
        print("DESTINATION BLOB:", destination_blob_name)
        print("CONTENT TYPE:", content_type)

        local_path = Path(local_file_path)
        if not local_path.exists():
            raise ValueError(f"Local file does not exist: {local_file_path}")

        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(str(local_path), content_type=content_type)

        file_url = self._generate_signed_url(blob)

        print("GCS FILE UPLOAD SUCCESSFUL")
        print("SIGNED URL GENERATED")
        return file_url