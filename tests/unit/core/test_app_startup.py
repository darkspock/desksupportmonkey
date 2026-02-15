from unittest.mock import MagicMock, patch


class TestEnsureStorageBucket:
    @patch("core.storage.S3StorageService")
    def test_ensure_bucket_called(self, mock_storage_cls):
        mock_storage = MagicMock()
        mock_storage.ensure_bucket.return_value = True
        mock_storage_cls.return_value = mock_storage

        from app import _ensure_storage_bucket
        _ensure_storage_bucket()

        mock_storage.ensure_bucket.assert_called_once_with("dsm-reports")

    @patch("core.storage.S3StorageService")
    def test_ensure_bucket_handles_failure(self, mock_storage_cls):
        mock_storage = MagicMock()
        mock_storage.ensure_bucket.return_value = False
        mock_storage_cls.return_value = mock_storage

        from app import _ensure_storage_bucket
        _ensure_storage_bucket()

    @patch("core.storage.S3StorageService", side_effect=Exception("No MinIO"))
    def test_ensure_bucket_handles_exception(self, mock_storage_cls):
        from app import _ensure_storage_bucket
        _ensure_storage_bucket()
