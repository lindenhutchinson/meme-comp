from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import Competition, Participant
from .utils import check_emoji_text
class CompetitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the competition name from the URL
        self.comp_name = self.scope["url_route"]["kwargs"]["competition_name"]
        self.participant_id = self.scope["url_route"]["kwargs"]["participant_id"]
        
        # Join the competition group
        await self.channel_layer.group_add(self.comp_name, self.channel_name)

        # this is causing problems - disabling user activity for now
        # await self.channel_layer.group_send(self.comp_name, {"type":"update_active","data":{"id":self.participant_id, "active":True}})
        # await self.toggle_active_participant(True)

        # Accept the WebSocket connection
        await self.accept()
       
    async def disconnect(self, close_code):

        # this is causing problems - disabling user activity for now
        # await self.channel_layer.group_send(self.comp_name, {"type":"update_active","data":{"id":self.participant_id, "active":False}})
        # await self.toggle_active_participant(False)
        # Leave the competition group
        await self.channel_layer.group_discard(self.comp_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        command = text_data_json['command']

        if command == 'send_emoji':
            emoji_text = check_emoji_text(message)
            if emoji_text:
                await self.channel_layer.group_send(
                    self.comp_name,
                    {
                        "type": "send_update",
                        "data": emoji_text,
                        "command": "update_emoji"
                    },
                )
        elif command == 'the_button':
            user = message
            await self.channel_layer.group_send(
                self.comp_name,
                {
                    "type": "send_update",
                    "data": user,
                    "command": "update_button"
                },
            )



    # this is causing problems - disabling for now
    # @database_sync_to_async
    # def toggle_active_participant(self, active):
    #     part = Participant.objects.get(id=self.participant_id)
    #     if part:
    #         part.active = active
    #         part.save()

    async def send_update(self, event):
        await self.send(text_data=json.dumps({
            'command': event['command'],
            'data': event['data']
        }))