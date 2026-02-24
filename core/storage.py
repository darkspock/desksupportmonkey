import logging
from abc import ABC, abstractmethod

import boto3
from botocore.exceptions import ClientError

from core.config import settings

logger = logging.getLogger(__name__)


class StorageServiceInterface(ABC):
    @abstractmethod
    def upload(
        self, key: str, data: bytes, content_type: str | None = None
    ) -> str:
        """Upload data to storage. Returns the object key."""
        ...

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Download object from storage. Returns bytes."""
        ...

    @abstractmethod
    def get_signed_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a pre-signed URL for downloading an object."""
        ...

    @abstractmethod
    def ensure_bucket(self, bucket_name: str) -> bool:
        """Ensure bucket exists, create if not. Returns True on success."""
        ...


class S3StorageService(StorageServiceInterface):
    def __init__(
        self,
        bucket: str = settings.s3.S3_REPORTS_BUCKET,
        endpoint_url: str = settings.s3.S3_ENDPOINT_URL,
        aws_access_key_id: str = settings.s3.AWS_ACCESS_KEY_ID,
        aws_secret_access_key: str = settings.s3.AWS_SECRET_ACCESS_KEY,
        region_name: str = settings.s3.AWS_REGION,
    ):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def upload(
        self, key: str, data: bytes, content_type: str | None = None
    ) -> str:
        extra: dict = {}
        if content_type:
            extra["ContentType"] = content_type
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=data, **extra
        )
        logger.info("Uploaded %s to %s", key, self.bucket)
        return key

    def download(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return bytes(response["Body"].read())

    def get_signed_url(self, key: str, expiration: int = 3600) -> str:
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expiration,
        )
        return str(url)

    def ensure_bucket(self, bucket_name: str) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket_name)
            logger.info("Bucket already exists: %s", bucket_name)
            return True
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                try:
                    self.client.create_bucket(Bucket=bucket_name)
                    logger.info("Bucket created: %s", bucket_name)
                    return True
                except ClientError as create_err:
                    logger.error("Failed to create bucket %s: %s", bucket_name, str(create_err))
                    return False
            logger.error("Error checking bucket %s: %s", bucket_name, str(e))
            return False
