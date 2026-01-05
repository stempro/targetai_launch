"""Azure Blob Storage client wrapper."""
import json
import logging
from typing import Any, Optional, TypeVar

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContainerClient
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BlobStorageClient:
    """Azure Blob Storage client with JSON document support."""

    def __init__(self, connection_string: str, container_name: str):
        """Initialize blob storage client.

        Args:
            connection_string: Azure Storage connection string
            container_name: Container name for storing data
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = container_name
        self.container_client: ContainerClient = self.blob_service_client.get_container_client(
            container_name
        )

        # Ensure container exists
        self._ensure_container_exists()

    def _ensure_container_exists(self) -> None:
        """Create container if it doesn't exist."""
        try:
            self.container_client.create_container()
            logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                logger.debug(f"Container already exists: {self.container_name}")
            else:
                logger.error(f"Error creating container: {e}")
                raise

    async def read(self, path: str, model_class: type[T]) -> Optional[T]:
        """Read and deserialize a JSON blob.

        Args:
            path: Blob path (e.g., 'counselors/counsel-001.json')
            model_class: Pydantic model class to deserialize into

        Returns:
            Deserialized model instance or None if not found
        """
        try:
            blob_client = self.container_client.get_blob_client(path)
            download_stream = blob_client.download_blob()
            content = download_stream.readall().decode("utf-8")
            data = json.loads(content)

            # Get etag for optimistic concurrency
            properties = blob_client.get_blob_properties()
            if hasattr(model_class, "etag"):
                data["etag"] = properties.etag

            return model_class.model_validate(data)

        except ResourceNotFoundError:
            logger.debug(f"Blob not found: {path}")
            return None
        except Exception as e:
            logger.error(f"Error reading blob {path}: {e}")
            raise

    async def write(
        self, path: str, data: BaseModel, etag: Optional[str] = None
    ) -> None:
        """Write a Pydantic model to blob storage as JSON.

        Args:
            path: Blob path (e.g., 'counselors/counsel-001.json')
            data: Pydantic model instance to serialize
            etag: Optional etag for optimistic concurrency control

        Raises:
            Exception: If etag doesn't match (concurrent modification)
        """
        try:
            blob_client = self.container_client.get_blob_client(path)

            # Serialize to JSON
            json_data = data.model_dump_json(indent=2, exclude={"etag"})

            # Upload with optional etag check
            kwargs: dict[str, Any] = {"overwrite": True}
            if etag:
                kwargs["etag"] = etag
                kwargs["match_condition"] = "IfMatch"  # Only write if etag matches

            blob_client.upload_blob(json_data, **kwargs)
            logger.debug(f"Wrote blob: {path}")

        except Exception as e:
            if "ConditionNotMet" in str(e):
                logger.error(f"Concurrent modification detected for {path}")
                raise ValueError("Concurrent modification - please retry")
            logger.error(f"Error writing blob {path}: {e}")
            raise

    async def delete(self, path: str) -> bool:
        """Delete a blob.

        Args:
            path: Blob path to delete

        Returns:
            True if deleted, False if didn't exist
        """
        try:
            blob_client = self.container_client.get_blob_client(path)
            blob_client.delete_blob()
            logger.debug(f"Deleted blob: {path}")
            return True
        except ResourceNotFoundError:
            logger.debug(f"Blob not found for deletion: {path}")
            return False
        except Exception as e:
            logger.error(f"Error deleting blob {path}: {e}")
            raise

    async def list_blobs(self, prefix: str) -> list[str]:
        """List all blob names with a given prefix.

        Args:
            prefix: Prefix to filter blobs (e.g., 'counselors/')

        Returns:
            List of blob names (paths)
        """
        try:
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Error listing blobs with prefix {prefix}: {e}")
            raise

    async def blob_exists(self, path: str) -> bool:
        """Check if a blob exists.

        Args:
            path: Blob path to check

        Returns:
            True if exists, False otherwise
        """
        try:
            blob_client = self.container_client.get_blob_client(path)
            blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking blob existence {path}: {e}")
            raise

    async def read_raw(self, path: str) -> Optional[dict[str, Any]]:
        """Read blob as raw dictionary (without model validation).

        Args:
            path: Blob path to read

        Returns:
            Dictionary or None if not found
        """
        try:
            blob_client = self.container_client.get_blob_client(path)
            download_stream = blob_client.download_blob()
            content = download_stream.readall().decode("utf-8")
            return json.loads(content)
        except ResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error reading raw blob {path}: {e}")
            raise

    async def write_raw(self, path: str, data: dict[str, Any]) -> None:
        """Write raw dictionary to blob storage.

        Args:
            path: Blob path to write
            data: Dictionary to serialize as JSON
        """
        try:
            blob_client = self.container_client.get_blob_client(path)
            json_data = json.dumps(data, indent=2)
            blob_client.upload_blob(json_data, overwrite=True)
            logger.debug(f"Wrote raw blob: {path}")
        except Exception as e:
            logger.error(f"Error writing raw blob {path}: {e}")
            raise
