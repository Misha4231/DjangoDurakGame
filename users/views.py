from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout

def login(request):
    if request.method == 'POST':
        # Retrieve username, password, and migration preference from the form
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate the user against the database
        user = authenticate(request, username=username, password=password)

        if user is not None:  # If authentication is successful
            # Log the user in
            auth_login(request, user)
            return redirect('index')  # Redirect to the index page

    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout(request):
    auth_logout(request)

    return redirect('login')

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            # Save the new user instance
            user = form.save()

            return redirect('login')  # Redirect to login page after registration
    else:  # If the form is not submitted, display an empty registration form
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})