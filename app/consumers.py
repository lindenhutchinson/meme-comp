from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import Competition, Participant

class CompetitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the competition name from the URL
        self.comp_name = self.scope["url_route"]["kwargs"]["competition_name"]
        self.participant_id = self.scope["url_route"]["kwargs"]["participant_id"]
        
        # Join the competition group
        await self.channel_layer.group_add(self.comp_name, self.channel_name)
        await self.channel_layer.group_send(self.comp_name, {"type":"update_active","data":{"id":self.participant_id, "active":True}})
        await self.toggle_active_participant(True)

        # Accept the WebSocket connection
        await self.accept()
       
    async def disconnect(self, close_code):
        await self.channel_layer.group_send(self.comp_name, {"type":"update_active","data":{"id":self.participant_id, "active":False}})
        await self.toggle_active_participant(False)
        # Leave the competition group
        await self.channel_layer.group_discard(self.comp_name, self.channel_name)

    @database_sync_to_async
    def toggle_active_participant(self, active):
        part = Participant.objects.get(id=self.participant_id)
        if part:
            part.active = active
            part.save()

    async def next_meme(self, event):
        # Send a message to all users in the competition that the competition has started
        await self.send(text_data=json.dumps({
            'command': 'next_meme',
            'data': event['data']
        }))

    async def cancel_competition(self, event):
        await self.send(text_data=json.dumps({
            'command': 'competition_cancelled',
        }))
        
    async def update_active(self, event):
        await self.send(text_data=json.dumps({
            'command': 'user_active',
            'data':event['data']
        }))

    async def update_joined(self, event):
        await self.send(text_data=json.dumps({
            'command': 'user_joined',
            'data':event['data']
        }))

    async def update_uploaded(self, event):
        await self.send(text_data=json.dumps({
            'command': 'meme_uploaded',
            'data':event['data']
        }))
        
    async def update_voted(self, event):
        await self.send(text_data=json.dumps({
            'command': 'meme_voted',
            'data':event['data']
        }))

    async def competition_results(self, event):
        await self.send(text_data=json.dumps({
            'command': 'competition_results',
            'data':event['data']
        }))

    async def update_emoji(self, event):
        await self.send(text_data=json.dumps({
            'command': 'update_emoji',
            'data':event['data']
        }))

    async def update_shame(self, event):
        await self.send(text_data=json.dumps({
            'command': 'update_shame',
            'data':event['data']
        }))