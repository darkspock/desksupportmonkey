from unittest.mock import MagicMock, patch

import pytest


class TestPingTask:
    def test_ping_returns_pong(self):
        from core.tasks.ping import ping
        result = ping()
        assert result == "pong"


class TestCleanupTask:
    @patch("core.database.SessionLocal")
    def test_cleanup_deletes_old_links(self, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_repo_instance = MagicMock()
        mock_repo_instance.delete_older_than.return_value = 5

        with patch("src.auth_bc.magic_link.infrastructure.repository.MagicLinkRepository", return_value=mock_repo_instance) as mock_repo_cls:
            # Need to re-import to pick up patched SessionLocal
            from core.tasks.cleanup import cleanup_magic_links
            result = cleanup_magic_links(days=7)

        assert result == 5
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("core.database.SessionLocal")
    def test_cleanup_rolls_back_on_error(self, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_repo_instance = MagicMock()
        mock_repo_instance.delete_older_than.side_effect = Exception("DB error")

        with patch("src.auth_bc.magic_link.infrastructure.repository.MagicLinkRepository", return_value=mock_repo_instance):
            from core.tasks.cleanup import cleanup_magic_links
            with pytest.raises(Exception, match="DB error"):
                cleanup_magic_links(days=7)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
