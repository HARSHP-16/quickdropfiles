import io
import os
from pathlib import Path
from uuid import uuid4


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
    def __init__(self, connection_string, container):
        from azure.storage.blob import BlobServiceClient
        self.container = BlobServiceClient.from_connection_string(connection_string).get_container_client(container)
        try:
            self.container.create_container()
        except Exception:
            pass

    def save(self, file_storage):
        name = uuid4().hex
        self.container.upload_blob(name, file_storage.stream, overwrite=False)
        return name

    def open(self, blob_name):
        return io.BytesIO(self.container.download_blob(blob_name).readall())

    def delete(self, blob_name):
        self.container.delete_blob(blob_name, delete_snapshots="include")


def create_storage(config):
    if config["STORAGE_BACKEND"].lower() == "azure":
        if not config.get("AZURE_STORAGE_CONNECTION_STRING"):
            raise RuntimeError("Azure storage selected but AZURE_STORAGE_CONNECTION_STRING is not configured")
        return AzureBlobStorage(config["AZURE_STORAGE_CONNECTION_STRING"], config["AZURE_STORAGE_CONTAINER"])
    return LocalStorage(config["UPLOAD_FOLDER"])
