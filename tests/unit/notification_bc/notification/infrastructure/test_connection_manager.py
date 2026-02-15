import asyncio
from unittest.mock import AsyncMock

import pytest

from src.notification_bc.notification.infrastructure.connection_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_ws():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


def _run(coro):
    """Helper to run async code in sync tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestConnectionManager:
    def test_connect_adds_user(self, manager, mock_ws):
        _run(manager.connect("user1", mock_ws))
        assert manager.is_connected("user1")
        mock_ws.accept.assert_called_once()

    def test_disconnect_removes_user(self, manager, mock_ws):
        _run(manager.connect("user1", mock_ws))
        manager.disconnect("user1", mock_ws)
        assert not manager.is_connected("user1")

    def test_disconnect_nonexistent_user(self, manager, mock_ws):
        manager.disconnect("user1", mock_ws)

    def test_multiple_connections_per_user(self, manager):
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        _run(manager.connect("user1", ws1))
        _run(manager.connect("user1", ws2))

        assert manager.is_connected("user1")
        assert manager.active_connections_count == 2

    def test_disconnect_one_of_multiple(self, manager):
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        _run(manager.connect("user1", ws1))
        _run(manager.connect("user1", ws2))

        manager.disconnect("user1", ws1)
        assert manager.is_connected("user1")
        assert manager.active_connections_count == 1

    def test_send_to_user(self, manager, mock_ws):
        _run(manager.connect("user1", mock_ws))
        _run(manager.send_to_user("user1", {"type": "test"}))
        mock_ws.send_json.assert_called_once_with({"type": "test"})

    def test_send_to_user_multiple_connections(self, manager):
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        _run(manager.connect("user1", ws1))
        _run(manager.connect("user1", ws2))
        _run(manager.send_to_user("user1", {"type": "test"}))

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    def test_send_to_disconnected_user(self, manager):
        _run(manager.send_to_user("nobody", {"type": "test"}))

    def test_broken_connection_removed_on_send(self, manager):
        ws_good = AsyncMock()
        ws_good.accept = AsyncMock()
        ws_good.send_json = AsyncMock()
        ws_broken = AsyncMock()
        ws_broken.accept = AsyncMock()
        ws_broken.send_json = AsyncMock(side_effect=RuntimeError("broken"))

        _run(manager.connect("user1", ws_good))
        _run(manager.connect("user1", ws_broken))
        assert manager.active_connections_count == 2

        _run(manager.send_to_user("user1", {"type": "test"}))

        assert manager.active_connections_count == 1
        ws_good.send_json.assert_called_once()

    def test_send_to_users(self, manager):
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        _run(manager.connect("user1", ws1))
        _run(manager.connect("user2", ws2))
        _run(manager.send_to_users(["user1", "user2"], {"type": "broadcast"}))

        ws1.send_json.assert_called_once_with({"type": "broadcast"})
        ws2.send_json.assert_called_once_with({"type": "broadcast"})

    def test_is_connected_false_for_unknown(self, manager):
        assert not manager.is_connected("unknown")

    def test_active_connections_count_empty(self, manager):
        assert manager.active_connections_count == 0
