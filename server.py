import asyncio
import json
import os
from typing import Dict

from aiohttp import web


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8765"))


clients: Dict[str, web.WebSocketResponse] = {}


async def send_json(ws: web.WebSocketResponse, data: dict) -> None:
    await ws.send_str(json.dumps(data))


async def root(request: web.Request) -> web.StreamResponse:
    ws = web.WebSocketResponse()
    if ws.can_prepare(request).ok:
        await ws.prepare(request)
        await websocket_handler(ws)
        return ws
    return web.Response(text="ok")


async def health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def websocket_handler(ws: web.WebSocketResponse) -> None:
    username = None
    try:
        async for msg in ws:
            if msg.type != web.WSMsgType.TEXT:
                continue
            try:
                data = json.loads(msg.data)
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


def main() -> None:
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
