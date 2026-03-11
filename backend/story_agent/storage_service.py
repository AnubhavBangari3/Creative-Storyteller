import uuid
from google.cloud import storage
from django.conf import settings


class GCSStorageService:
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.bucket_name = settings.GCP_BUCKET_NAME
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_bytes(self, file_bytes, destination_blob_name, content_type=None):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)
        blob.make_public()
        return blob.public_url

    def upload_file(self, local_file_path, destination_blob_name, content_type=None):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_file_path, content_type=content_type)
        blob.make_public()
        return blob.public_url

    def generate_unique_filename(self, prefix="files", extension="bin"):
        unique_id = uuid.uuid4().hex
        return f"{prefix}/{unique_id}.{extension}"