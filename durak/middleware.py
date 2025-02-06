from http.cookies import SimpleCookie

from channels.db import database_sync_to_async

from .models import Player

@database_sync_to_async # django ORM work synchronously, hence decorator is used
def get_player(id):
    # get player with all related field
    return Player.objects.select_related("user").select_related('anonymous_user').select_related("room").filter(id=id).first()

# custom auth middleware to know what user is connecting
class PlayerAuthMiddleware:
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        headers = scope['headers'] # get all headers
        cookies_str = next((header[1] for header in headers if header[0] == b'cookie'), b'') # search cookies header (key-value pairs)
        
        cookies = SimpleCookie() # cookie parsing object
        cookies.load(cookies_str.decode()) # load cookies
        
        if 'player_id' not in cookies: # if player_id is not assigned (assigned to every user on the index page after starting game)
            await self.unauthorized(send) #close connection
            return
        
        player_id = cookies.get('player_id').value #get uuid cookie
        player = await get_player(player_id)
        
        if not player: # check if user exists
            await self.unauthorized(send)
            return
        
        scope['user'] = player # add player to scope
        return await self.app(scope, receive, send)

    @staticmethod
    async def unauthorized(send): # static method to close connection with undefined user
        await send({
            "type":  'websocket.close',
            'code': 4401
        })