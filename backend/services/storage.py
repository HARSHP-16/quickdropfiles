import io
import logging
import os
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)


class LocalStorage:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def save(self, file_storage):
        name = f"{uuid4().hex}{Path(file_storage.filename or '').suffix.lower()}"
        path = self.folder / name
        file_storage.save(path)
        return name

    def open(self, blob_name):
        return open(self.folder / blob_name, "rb")

    def delete(self, blob_name):
        try:
            os.remove(self.folder / blob_name)
        except FileNotFoundError:
            pass


class AzureBlobStorage:
    """Private Azure Blob Storage authenticated through DefaultAzureCredential."""

    def __init__(self, account_name, container):
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        account_url = f"https://{account_name}.blob.core.windows.net"
        self.container = BlobServiceClient(
            account_url=account_url,
            credential=DefaultAzureCredential(),
        ).get_container_client(container)

    def save(self, file_storage):
        # Blob names are generated internally; no user-controlled filename is used as a path.
        name = f"uploads/{uuid4().hex}{Path(file_storage.filename or '').suffix.lower()}"
        self.container.upload_blob(name, file_storage.stream, overwrite=False)
        return name

    def open(self, blob_name):
        return io.BytesIO(self.container.download_blob(blob_name).readall())

    def delete(self, blob_name):
        from azure.core.exceptions import ResourceNotFoundError

        try:
            self.container.delete_blob(blob_name, delete_snapshots="include")
        except ResourceNotFoundError:
            # Deletion is idempotent, matching the existing local backend semantics.
            logger.info("Blob %s was already absent during cleanup", blob_name)


def create_storage(config):
    if config["STORAGE_BACKEND"].lower() == "azure":
        account_name = config.get("AZURE_STORAGE_ACCOUNT_NAME")
        if not account_name:
            raise RuntimeError("Azure storage selected but AZURE_STORAGE_ACCOUNT_NAME is not configured")
        return AzureBlobStorage(account_name, config["AZURE_STORAGE_CONTAINER"])
    return LocalStorage(config["UPLOAD_FOLDER"])
