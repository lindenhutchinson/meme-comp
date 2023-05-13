from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import Competition


class CompetitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the competition name from the URL
        self.comp_name = self.scope["url_route"]["kwargs"]["competition_name"]
        
        # Join the competition group
        await self.channel_layer.group_add(self.comp_name, self.channel_name)
        
        # Accept the WebSocket connection
        await self.accept()

        # # Send a message to all users in the competition that a new user has joined
        # await self.channel_layer.group_send(
        #     self.comp_name,
        #     {
        #         'type': 'user_joined',
        #         'name': self.scope['user'].username
        #     }
        # )

    async def disconnect(self, close_code):
        # Leave the competition group
        await self.channel_layer.group_discard(self.comp_name, self.channel_name)

    # async def user_joined(self, event):
    #     # Send a message to all users in the competition that a new user has joined
    #     await self.send(text_data=json.dumps({
    #         'command': 'user_joined',
    #         'name': event['name']
    #     }))

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json['command']

        if command == 'start_competition':
            print('received start_competition command')
            # Mark the competition as started
            # Send a message to all users in the competition that the competition has started
            await self.channel_layer.group_send(
                self.comp_name,
                {
                    'type': 'competition_started',
                }
            )

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
        
    @database_sync_to_async
    def toggle_competition_started(self):
        competition = Competition.objects.get(name=self.comp_name)
        competition.started = True
        competition.save()
        
    @database_sync_to_async
    def get_num_memes(self):
        competition = Competition.objects.get(name=self.comp_name)
        return competition.num_memes

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