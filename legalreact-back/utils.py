from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
import datetime
import os

class Utils:

    def __init__(self):
        self.AZURE_BLOB_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.AZURE_BLOB_CONTAINER = os.getenv("AZURE_CONTAINER_NAME")
        self.AZURE_BLOB_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

    def generate_sas_url(self, blob_name):
        sas_token = generate_blob_sas(
            account_name=self.AZURE_BLOB_ACCOUNT,
            container_name=self.AZURE_BLOB_CONTAINER,
            blob_name=blob_name,
            account_key=self.AZURE_BLOB_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        )
        return f"https://{self.AZURE_BLOB_ACCOUNT}.blob.core.windows.net/{self.AZURE_BLOB_CONTAINER}/{blob_name}?{sas_token}"

    def upload_pdf_to_blob(self, file_path, file_name):
        blob_service_client = BlobServiceClient(
            account_url=f"https://{self.AZURE_BLOB_ACCOUNT}.blob.core.windows.net",
            credential=self.AZURE_BLOB_KEY
        )
        blob_client = blob_service_client.get_blob_client(
            container=self.AZURE_BLOB_CONTAINER,
            blob=file_name
        )
        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/pdf")
            )
        return f"File {file_name} uploaded successfully."

    def get_most_recent_blob(self):
        blob_service_client = BlobServiceClient(
            account_url=f"https://{self.AZURE_BLOB_ACCOUNT}.blob.core.windows.net",
            credential=self.AZURE_BLOB_KEY
        )
        container_client = blob_service_client.get_container_client(self.AZURE_BLOB_CONTAINER)
        blobs = container_client.list_blobs()
        most_recent_blob = max(blobs, key=lambda b: b['last_modified'])
        return most_recent_blob['name']
