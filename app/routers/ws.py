import json
import traceback
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Request
from fastapi.responses import HTMLResponse
from app.models.scheme import WsMessage
from app.exception_handler import *
from app.utils.redis import MetadataRedisPool
from app.config import settings
from typing import List

router = APIRouter(
    tags=["websocket"],
    responses={404: {"description": "Not found"}},
)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <label> message </label>
            <input type="text" id="message" autocomplete="off"/>
            <label> data </label>
            <input type="text" id="data" autocomplete="off"/>
            
            <button>Send</button>
        </form>
        <button id="close">close</button>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            const hostname = window.location.hostname
            const port = window.location.port
            const protocol = (window.location.protocol === 'https:') ? 'wss' : 'ws'
            var ws = new WebSocket(`${protocol}://${hostname}:${port}/ws/${client_id}`);
            console.log(`${protocol}://${hostname}:${port}/ws/${client_id}`)
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            ws.onclose = function(event){
                console.log(event)
            }
            function sendMessage(event) {
                event.preventDefault()
                var message = document.getElementById("message")
                var data = document.getElementById("data")
                console.log(message.value, data.value)
                console.log(JSON.stringify({message: message.value, data: JSON.parse(data.value)}))
                ws.send(JSON.stringify({message: message.value, data: JSON.parse(data.value)}))
            }
            
            document.querySelector("#close").addEventListener("click", ()=>{
                console.log("here")
                ws.close()
            })

        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        msg = {"message": "connected"}
        await websocket.send_text(json.dumps(msg))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    @staticmethod
    async def send_personal_message(message: WsMessage, websocket: WebSocket):
        await websocket.send_text(message.json())

    async def broadcast(self, message: WsMessage):
        if not isinstance(self.active_connections, list):
            return

        for connection in self.active_connections:
            try:
                await connection.send_text(message.json())
            except Exception as e:
                traceback.print_exc()
                self.disconnect(connection)

    async def broadcast_debug(self, message: str):
        if not isinstance(self.active_connections, list):
            return

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                # traceback.print_exc()
                self.disconnect(connection)


connection_manager = ConnectionManager()

if settings.runtime_env not in ['test', 'production', 'rc']:
    @router.get("/ws")
    async def get():
        return HTMLResponse(html)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = await ws_handle_request(data, websocket.app.redis)
            await connection_manager.send_personal_message(message, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        traceback.print_exc()
        connection_manager.disconnect(websocket)


async def ws_handle_request(data: str, redis: MetadataRedisPool) -> WsMessage:
    try:
        data = json.loads(data)
        message = data.get('message')
        request_data = data.get('data')
        if message == "message":
            wsm = {"message": "message", "data": [request_data]}
        else:
            wsm = {"message": "Unknown request", "data": []}
        return WsMessage(**wsm)
    except json.decoder.JSONDecodeError:
        return WsMessage(message="Invalid Json Format", data=[])
    except WsRequestError:
        return WsMessage(message="Request Error", data=[])
    except Exception:
        traceback.print_exc()
        return WsMessage(message="Server Error.", data=[])
