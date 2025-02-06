import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Player

# waiting room for players waiting until is full and game started
class WaitingRoomConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs): # define all later used fields
        super().__init__(args, kwargs)
        self.player = None
        self.room_id = None
        self.room_group_name = None
        self.room = None
        self.players = None
        
    def connect(self):
        self.player = self.scope['user'] # get player data (see middleware.PlayerAuthMiddleware)
        # extract related to player data for later use
        self.room = self.player.room
        self.room_id = self.room.id
        self.room_group_name = f'waiting_room_{self.room_id}'
        self.players = Player.objects.filter(room=self.room).all()

        if self.room.max_players_count < len(self.players): # in case something go wrong and more users than possible connected
            self.close(3003) # close connection
            return

        self.accept() # accept connection

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        if self.room.max_players_count == len(self.players): #room is full, start the game            
            self.room.is_waiting = False
            self.room.save()
            
            async_to_sync(self.channel_layer.group_send)( # signal to start game (js should redirect user)
                self.room_group_name,
                {
                    'type': 'start_game',
                    'redirect_url': '/durak/'
                }
            )
            
        else:
            async_to_sync(self.channel_layer.group_send)( # update the number of users waiting
                self.room_group_name,
                {
                    'type': 'players_count',
                    'connected_users_count': len(self.players)
                }
            )

    def start_game(self, event):
        self.send(text_data=json.dumps(event))
    def players_count(self, event):
        self.send(text_data=json.dumps(event))
        
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        if close_code != 1000: # if something go wrong and connection is closing not because game is starting, then delete player with related data
            self.player.delete()