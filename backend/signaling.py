# signaling.py

import asyncio
import json
import websockets
from aiortc import RTCSessionDescription, RTCIceCandidate

class WebSocketSignaling:
    def __init__(self, url):
        self.url = url
        self.websocket = None
        self.queue = asyncio.Queue()

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        asyncio.create_task(self.receive_loop())

    async def receive_loop(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.queue.put(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed.")

    async def send(self, message):
        await self.websocket.send(message)

    async def receive(self):
        return await self.queue.get()

    async def close(self):
        await self.websocket.close()