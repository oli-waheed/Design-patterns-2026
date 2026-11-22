from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from composition import connection_manager


router = APIRouter(tags=["realtime"])


@router.websocket("/api/ws")
async def dashboard_websocket(websocket: WebSocket) -> None:
    """Dashboard-only push channel.

    Sends { "type", "payload" } frames for reading.created,
    actuator.state_changed and alert.created. Devices do not connect here;
    they use HTTP (GET .../sampling, POST .../readings) or the optional
    MQTT broker.
    """

    await connection_manager.connect(websocket)

    try:
        while True:
            # The dashboard does not send commands over this socket.
            # Reading keeps the connection open and detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(websocket)
