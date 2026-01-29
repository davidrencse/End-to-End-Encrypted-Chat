import asyncio
import json
import os
from typing import Dict, Optional, Tuple

import websockets


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8765"))


clients: Dict[str, websockets.WebSocketServerProtocol] = {}


async def send_json(ws, data):
    await ws.send(json.dumps(data))


def health_check(path, request_headers) -> Optional[Tuple[int, list, bytes]]:
    # Render sends regular HTTP health checks (often HEAD). Respond to them.
    if path in ("/", "/health"):
        body = b"ok"
        return 200, [("Content-Type", "text/plain")], body
    # Any other non-WebSocket HTTP request should still get a simple response.
    body = b"websocket only"
    return 200, [("Content-Type", "text/plain")], body


async def handler(ws):
    username = None
    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_json(ws, {"type": "error", "message": "invalid json"})
                continue

            msg_type = data.get("type")
            if msg_type == "register":
                requested = data.get("username")
                if not requested:
                    await send_json(ws, {"type": "error", "message": "username required"})
                    continue
                if requested in clients:
                    await send_json(ws, {"type": "error", "message": "username taken"})
                    await ws.close()
                    return
                username = requested
                clients[username] = ws
                await send_json(ws, {"type": "registered", "username": username})
                continue

            if not username:
                await send_json(ws, {"type": "error", "message": "not registered"})
                continue

            recipient = data.get("to")
            if not recipient:
                await send_json(ws, {"type": "error", "message": "missing 'to'"})
                continue

            target = clients.get(recipient)
            if not target:
                await send_json(ws, {"type": "error", "message": "user not online"})
                continue

            data["from"] = username
            await send_json(target, data)
    finally:
        if username and clients.get(username) is ws:
            del clients[username]


async def main():
    async with websockets.serve(handler, HOST, PORT, process_request=health_check):
        print(f"Server running on ws://{HOST}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
