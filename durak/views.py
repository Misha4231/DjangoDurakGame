from django.shortcuts import render


# home page where user can choose players count and join appropriate waiting room
def index(request):
    return render(request, 'index.html', {})