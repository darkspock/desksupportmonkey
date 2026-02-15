import logging

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.jwt import JWTService, InvalidTokenError, ExpiredTokenError
from src.notification_bc.notification.infrastructure.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()

jwt_service = JWTService()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    try:
        payload = jwt_service.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except (InvalidTokenError, ExpiredTokenError):
        await websocket.close(code=4001, reason="Invalid token")
        return

    await connection_manager.connect(user_id, websocket)
    logger.info("WebSocket connected: user_id=%s", user_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id, websocket)
        logger.info("WebSocket disconnected: user_id=%s", user_id)
    except Exception:
        connection_manager.disconnect(user_id, websocket)
        logger.info("WebSocket error, disconnected: user_id=%s", user_id)
