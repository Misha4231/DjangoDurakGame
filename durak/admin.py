from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(AnonymousUser)
admin.site.register(Player)
admin.site.register(Room)