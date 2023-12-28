from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .utils import check_emoji_text
import asyncio


class WebSocketManager:
    active_connections = {}  # A dictionary to store user WebSocket connections

    @classmethod
    async def add_connection(cls, user_id, websocket_instance):
        cls.active_connections[user_id] = websocket_instance

    @classmethod
    async def remove_connection(cls, user_id):
        if user_id in cls.active_connections:
            del cls.active_connections[user_id]

    @classmethod
    async def close_connection(cls, user_id):
        if user_id in cls.active_connections:
            websocket_instance = cls.active_connections[user_id]
            # Close the WebSocket connection gracefully
            asyncio.create_task(websocket_instance.close(code=3000))

            del cls.active_connections[user_id]


class CompetitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the competition name from the URL
        self.comp_name = self.scope["url_route"]["kwargs"]["competition_name"]
        self.user_id = self.scope["user"].id
        if self.user_id in WebSocketManager.active_connections:
            await WebSocketManager.close_connection(self.user_id)

        await self.channel_layer.group_add(self.comp_name, self.channel_name)
        await WebSocketManager.add_connection(self.user_id, self)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.comp_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        command = text_data_json["command"]

        if command == "send_emoji":
            emoji_text = check_emoji_text(message)
            if emoji_text:
                await self.channel_layer.group_send(
                    self.comp_name,
                    {
                        "type": "send_update",
                        "data": emoji_text,
                        "command": "updateEmoji",
                    },
                )
        elif command == "the_button":
            user = message
            await self.channel_layer.group_send(
                self.comp_name,
                {"type": "send_update", "data": user, "command": "update_button"},
            )

    async def send_update(self, event):
        await self.send(
            text_data=json.dumps(
                {"command": event["command"], "data": event["data"]}, default=str
            )
        )
