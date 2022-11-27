import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.ws import *


@pytest.mark.asyncio
async def test_connection_manager(test_client_factory):
    manager = ConnectionManager()

    def app(scope):
        async def asgi(receive, send):
            websocket = WebSocket(scope, receive=receive, send=send)

            await manager.connect(websocket)
            assert websocket in manager.active_connections
            with pytest.raises(WebSocketDisconnect):
                data = await websocket.receive_text()
                assert data == json.dumps({"message": "land"})

                wsm = WsMessage(**{"message": "land", "data": []})
                await manager.send_personal_message(wsm, websocket)
                await manager.broadcast(wsm)
                await websocket.receive_text()

            manager.disconnect(websocket)
            assert websocket not in manager.active_connections

        return asgi

    client = test_client_factory(app)
    with client.websocket_connect("/ws/1234567") as websocket:
        websocket.send_text(json.dumps({"message": "land"}))
        websocket.receive_text()
        websocket.receive_text()
        websocket.close()


def test_websocket_endpoint():
    client = TestClient(app)
    with client.websocket_connect("/ws/1234567") as websocket:
        data = websocket.receive_text()
        data = json.loads(data)
        assert data['message'] == 'connected'


@pytest.mark.asyncio
async def test_ws_handle_request():
    redis = MetadataRedisPool()

    data = {"message": "message"}
    data = json.dumps(data)
    wsm = await ws_handle_request(data, redis)
    assert wsm.message == 'message'

    data = {"message": "asd", 'data': ['4193', "0"]}
    data = json.dumps(data)

    wsm = await ws_handle_request(data, redis)
    assert wsm.message == 'Unknown request'

    wsm = await ws_handle_request("data", redis)
    assert wsm.message == "Invalid Json Format"

    await redis.close()
