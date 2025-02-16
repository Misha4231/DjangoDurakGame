import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Player

import engine.Table as EngineTable
import engine.Card as EngineCard

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


# game consumer managing everything in game
class GameConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs): # define all later used fields
        super().__init__(args, kwargs)
        self.player = None
        self.room_id = None
        self.game_group_name = None
        self.room = None
        self.players = None
        self.table = None

    def connect(self):
        self.player = self.scope['user']  # get player data (see middleware.PlayerAuthMiddleware)
        # extract related to player data for later use
        self.room = self.player.room
        self.room_id = self.room.id
        self.game_group_name = f'game_{self.room_id}'
        self.players = Player.objects.filter(room=self.room).all()

        self.table = EngineTable.Table.from_json(self.room.game_state) # get initial state of the game

        # add to group and accent connection
        async_to_sync(self.channel_layer.group_add)(
            self.game_group_name,
            self.channel_name
        )
        # every user will have unique group to send sensible data to everyone
        async_to_sync(self.channel_layer.group_add)(
            f'player_{self.player.id}',
            self.channel_name
        )
        self.accept()

        # send initial state of game
        self.send(text_data=json.dumps({
            'type': 'game_state',
            "state": self.table.to_safejson(str(self.player.id)),
            "player_id": str(self.player.id)
        }))

    def disconnect(self, close_code):
        # disconnect from groups
        async_to_sync(self.channel_layer.group_discard)(
            self.game_group_name,
            self.channel_name
        )
        async_to_sync(self.channel_layer.group_discard)(
            f'player_{self.player.id}',
            self.channel_name
        )

    def receive(self, text_data = None, **kwargs):
        self.room.refresh_from_db() # reload latest state from the database
        self.table = EngineTable.Table.from_json(self.room.game_state)  # get updates from database

        data = json.loads(text_data)
        action = data['action']

        print(data)
        try:
            if action == 'play_turn':
                card_name = data['card']

                self.table.play_turn(EngineCard.Card.from_string(card_name)) # make move in engine side
                self.save_and_send_all_state({'type': 'play_turn'}) # send updates to front end

            elif action == 'throw_additional':
                card_name = data['card']

                self.table.throw_additional(str(self.player.id), EngineCard.Card.from_string(card_name)) # call engine method to throw additional card
                self.save_and_send_all_state({'type': 'throw_additional', 'player_id': str(self.player.id)}) # mark what action was made and by who

            elif action == 'defend':
                bottom_card = data['bottom_card']
                defender_card = data['top_card']

                self.table.defend(EngineCard.Card.from_string(bottom_card), EngineCard.Card.from_string(defender_card))  # call engine method to defend bottom card
                self.save_and_send_all_state({'type': 'defend', 'player_id': str(self.player.id)}) # save
            elif action == 'take_cards':
                if str(self.player.id) != self.table.players[self.table.get_next_turn()].get_id(): # validate if user is defender
                    raise ValueError("Only defender can take cards")

                self.table.defender_take_cards()
                self.save_and_send_all_state({'type': 'defender_take_cards'})  # save
            elif action == 'finished':
                self.table.player_finished(str(self.player.id))
                self.save_and_send_all_state({'type': 'finished', 'player_id': str(self.player.id)})  # save

        except Exception as e: # if some error in validation occurred
            msg = str(e)

            self.send(text_data=json.dumps({
                'type': 'player_mistake',
                "state": self.table.to_safejson(str(self.player.id)),
                "player_id": str(self.player.id),
                'message': msg
            }))

    # save and send table state to everyone in group
    def save_and_send_all_state(self, last_action):
        self.room.game_state = self.table.to_json()
        self.room.save()

        for p in self.players: # sends state to users one-by-one to avoid sensitive data leak to other players
            player_group_name = f'player_{p.id}'

            async_to_sync(self.channel_layer.group_send)(
                player_group_name,
                {
                    'type': 'game_state',
                    "state": self.table.to_safejson(str(p.id)),
                    "player_id": str(p.id), # current player
                    'last_action': last_action # action made by some player
                }
            )

    def game_state(self, event):
        self.send(text_data=json.dumps(event))