import pytest
from starlette.testclient import TestClient

from app import app
from core.jwt import JWTService


jwt_service = JWTService()


class TestWebSocketEndpoint:
    def test_connect_with_valid_token(self):
        token = jwt_service.create_token(
            user_id="user1", company_id="comp1", role="employee"
        )
        with TestClient(app) as client:
            with client.websocket_connect(f"/ws?token={token}") as ws:
                ws.send_text("ping")

    def test_reject_without_token(self):
        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/ws") as ws:
                    pass

    def test_reject_with_invalid_token(self):
        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/ws?token=invalidtoken") as ws:
                    pass

    def test_reject_with_empty_token(self):
        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/ws?token=") as ws:
                    pass
