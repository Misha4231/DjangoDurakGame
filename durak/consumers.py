import json
import asyncio

from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
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
class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs): # define all later used fields
        super().__init__(args, kwargs)
        self.player = None
        self.player_id = None
        self.room_id = None
        self.game_group_name = None
        self.room = None
        self.players = None
        self.table = None

    async def connect(self):
        self.player = self.scope['user']  # get player data (see middleware.PlayerAuthMiddleware)
        self.player_id = str(self.player.id) # convert uuid to string
        # extract related to player data for later use
        self.room = self.player.room
        self.room_id = self.room.id
        self.game_group_name = f'game_{self.room_id}'
        self.players = await sync_to_async(Player.objects.filter(room=self.room).all)()

        self.table = EngineTable.Table.from_json(self.room.game_state) # get initial state of the game

        # add to group and accent connection
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        # every user will have unique group to send sensible data to everyone
        await self.channel_layer.group_add(
            f'player_{self.player_id}',
            self.channel_name
        )
        await self.accept()

        self.player.is_connected = True # marks that user has established connection with game socket
        await sync_to_async(self.player.save)()

        # send initial state of game
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            "state": self.table.to_safejson(self.player_id),
            "player_id": self.player_id
        }))

    async def disconnect(self, close_code):
        # disconnect from groups
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            f'player_{self.player_id}',
            self.channel_name
        )

        self.player.is_connected = False # marks that user is not connected to game socket
        await sync_to_async(self.player.save)()

        # Start background task to check if user reconnects
        asyncio.create_task(self.wait_until_reconnect(5))

    async def wait_until_reconnect(self, time_to_reconnect):
        for _ in range(time_to_reconnect):
            await asyncio.sleep(1)

            await sync_to_async(self.player.refresh_from_db)() # refresh data from database about connection
            is_connected = self.player.is_connected

            if is_connected: # if player reconnects, stop task
                return

        # player wants to left room, remove him
        self.table.remove_player(self.player_id)
        await sync_to_async(self.player.delete, thread_sensitive=True)() #delete player from database

        if len(self.table.players) == 0 and len(self.table.winners) == 0: # everyone left game
            await sync_to_async(self.room.delete, thread_sensitive=True)() # delete room
        else:
            await self.save_and_send_all_state({'type': 'player_removed', 'player_id': self.player_id})

    async def receive(self, text_data = None, **kwargs):
        await sync_to_async(self.room.refresh_from_db, thread_sensitive=True)() # reload latest state from the database
        self.table = EngineTable.Table.from_json(self.room.game_state)  # get updates from database

        data = json.loads(text_data)
        action = data['action']

        try:
            if action == 'play_turn':
                card_name = data['card']

                self.table.play_turn(EngineCard.Card.from_string(card_name)) # make move in engine side
                await self.save_and_send_all_state({'type': 'play_turn'}) # send updates to front end

            elif action == 'throw_additional':
                card_name = data['card']

                self.table.throw_additional(self.player_id, EngineCard.Card.from_string(card_name)) # call engine method to throw additional card
                await self.save_and_send_all_state({'type': 'throw_additional', 'player_id': self.player_id}) # mark what action was made and by who

            elif action == 'defend':
                bottom_card = data['bottom_card']
                defender_card = data['top_card']

                self.table.defend(EngineCard.Card.from_string(bottom_card), EngineCard.Card.from_string(defender_card))  # call engine method to defend bottom card
                await self.save_and_send_all_state({'type': 'defend', 'player_id': self.player_id}) # save
            elif action == 'take_cards':
                if self.player_id != self.table.players[self.table.get_next_turn()].get_id(): # validate if user is defender
                    raise ValueError("Only defender can take cards")

                self.table.defender_take_cards()
                await self.save_and_send_all_state({'type': 'defender_take_cards'})  # save
            elif action == 'finished':
                self.table.player_finished(self.player_id)
                await self.save_and_send_all_state({'type': 'finished', 'player_id': self.player_id})  # save

        except Exception as e: # if some error in validation occurred
            msg = str(e)

            await self.send(text_data=json.dumps({
                'type': 'player_mistake',
                "state": self.table.to_safejson(self.player_id),
                "player_id": self.player_id,
                'message': msg
            }))


    # save and send table state to everyone in group
    async def save_and_send_all_state(self, last_action):
        self.room.game_state = self.table.to_json()
        await sync_to_async(self.room.save, thread_sensitive=True)()

        players = await sync_to_async(list, thread_sensitive=True)(self.players)
        for p in self.players: # sends state to users one-by-one to avoid sensitive data leak to other players
            player_group_name = f'player_{p.id}'

            await self.channel_layer.group_send(
                player_group_name,
                {
                    'type': 'game_state',
                    "state": self.table.to_safejson(str(p.id)),
                    "player_id": str(p.id), # current player
                    'last_action': last_action # action made by some player
                }
            )

    async def game_state(self, event):
        await self.send(text_data=json.dumps(event))