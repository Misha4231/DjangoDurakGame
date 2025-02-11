from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse
from .models import *

# home page where user can choose players count and join appropriate waiting room
def index(request: HttpRequest):
    # If the request method is GET, render the homepage
    if request.method == 'GET':
        return render(request, 'index.html', {})
    else:
        players_count_room = request.POST['players_count']
        
        # Validate that the players count is provided and is either 2, 3, or 4
        if not players_count_room or (players_count_room not in ['2','3','4']):
            return render(request, 'index.html', {'error_msg': 'Options available are: 2, 3 or 4'}, status=400)
        # If the user is not authenticated and no username is provided, return an error
        if not request.user.is_authenticated and not request.POST['username']:
            return render(request, 'index.html', {'error_msg': 'Either sign in or provide a name'}, status=400)
        
        players_count_room = int(players_count_room)
        
        # Try to find an available room that matches the player count and is still waiting for players
        available_room = Room.objects.filter(max_players_count=players_count_room, is_waiting=True).first()
        if not available_room: # If no such room exists, create a new one
            available_room = Room(max_players_count=players_count_room, is_waiting=True)
            available_room.save()
            
        player = None
        if request.user.is_authenticated:  # If the user is authenticated, create a Player entry linked to their user account
            player = Player(user=request.user, anonymous_user=None, room=available_room)
        else: # If the user is anonymous, create an temporary AnonymousUser profile
            anonymus_profile = AnonymousUser(name=request.POST['username'])
            anonymus_profile.save()
            
            player = Player(user=None, anonymous_user=anonymus_profile, room=available_room)
            
        player.save()
        
        # Redirect the player to the waiting room
        response = redirect('waiting_room')
        response.set_cookie('player_id', player.id, max_age=7200, httponly=True) # Store the player's ID in a secure cookie (valid for 2 hours)
        
        return response
    
def waiting_room(request: HttpRequest):
    player_id = request.COOKIES.get('player_id') # Retrieve the player's id from cookies
    if not player_id: # If no player ID is found in cookies, redirect to the index page
        return redirect('index')
    
    player = Player.objects.select_related("room").filter(id=player_id).first() # Fetch the player from the database using the stored ID
    if not player: # redirect to index if the player doesn't exist or is not in the correct room
        return redirect('index')
    
    return render(request, 'waiting_room.html', {'max_players_count': player.room.max_players_count})


def start_durakgame(request):
    return render(request, 'durak_game.html')