"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from durak.middleware import PlayerAuthMiddleware
import durak.routing


application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': PlayerAuthMiddleware( # custom auth middleware to know what user is connecting
        URLRouter(
           durak.routing.websocket_urlpatterns
        )
    ),
})