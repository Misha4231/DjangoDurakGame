from django.urls import path

from .consumers import WaitingRoomConsumer, GameConsumer


websocket_urlpatterns = [
    path('ws/waiting_room/', WaitingRoomConsumer.as_asgi()),
    path('ws/durak_game/', GameConsumer.as_asgi()),
]