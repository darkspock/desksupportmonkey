from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from core.storage import S3StorageService


class TestS3StorageService:
    def setup_method(self):
        with patch("core.storage.boto3.client") as mock_boto:
            self.mock_client = MagicMock()
            mock_boto.return_value = self.mock_client
            self.service = S3StorageService(
                bucket="test-bucket",
                endpoint_url="http://localhost:9000",
                aws_access_key_id="test",
                aws_secret_access_key="test",
                region_name="us-east-1",
            )

    def test_upload(self):
        result = self.service.upload("test.txt", b"hello")
        self.mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket", Key="test.txt", Body=b"hello"
        )
        assert result == "test.txt"

    def test_download(self):
        mock_body = MagicMock()
        mock_body.read.return_value = b"file content"
        self.mock_client.get_object.return_value = {"Body": mock_body}

        result = self.service.download("test.txt")
        assert result == b"file content"
        self.mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test.txt"
        )

    def test_get_signed_url(self):
        self.mock_client.generate_presigned_url.return_value = "https://signed-url"
        result = self.service.get_signed_url("test.txt", expiration=600)
        assert result == "https://signed-url"
        self.mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test.txt"},
            ExpiresIn=600,
        )

    def test_ensure_bucket_exists(self):
        result = self.service.ensure_bucket("test-bucket")
        assert result is True
        self.mock_client.head_bucket.assert_called_once_with(Bucket="test-bucket")

    def test_ensure_bucket_creates_if_not_exists(self):
        error_response = {"Error": {"Code": "404"}}
        self.mock_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        result = self.service.ensure_bucket("new-bucket")
        assert result is True
        self.mock_client.create_bucket.assert_called_once_with(Bucket="new-bucket")

    def test_ensure_bucket_returns_false_on_create_error(self):
        head_error = {"Error": {"Code": "404"}}
        create_error = {"Error": {"Code": "500", "Message": "Internal"}}
        self.mock_client.head_bucket.side_effect = ClientError(head_error, "HeadBucket")
        self.mock_client.create_bucket.side_effect = ClientError(create_error, "CreateBucket")

        result = self.service.ensure_bucket("fail-bucket")
        assert result is False
