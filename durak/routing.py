from django.urls import path

from .consumers import WaitingRoomConsumer


websocket_urlpatterns = [
    path('ws/waiting_room/', WaitingRoomConsumer.as_asgi())
]