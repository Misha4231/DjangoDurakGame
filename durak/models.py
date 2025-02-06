import uuid
import json

from django.db import models
from django.contrib.auth.models import User

# Model for an anonymous user
class AnonymousUser(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
    
class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) #uuid instead of integer to prevent random user joining the room
    max_players_count = models.IntegerField(default=2)
    is_waiting = models.BooleanField(default=True) # room waiting until it fulls and game starts
    
    
# Model to represent a player (either authenticated or anonymous)
class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    anonymous_user = models.ForeignKey(AnonymousUser, null=True, blank=True, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, null=False, blank=False, on_delete=models.CASCADE)
    
    def __str__(self):
        if self.user:
            return self.user.username
        elif self.anonymous_user:
            return self.anonymous_user.name
        
        return "Unknown Player"

    def group(self): # pack essential data to dictionary
        return {'name': str(self), 'id': str(self.id)}
        
    def delete(self, *args, **kwargs): # delete player with related data
        room_players = Player.objects.filter(room=self.room).all()
        if len(room_players) <= 1: # in case room is empty
            self.room.delete()
        
        if self.anonymous_user: # user don't have an account
            self.anonymous_user.delete()

        super().delete(*args, **kwargs)