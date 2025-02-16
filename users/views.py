from django.http import HttpResponse
from django.shortcuts import render


def login(request):
    return HttpResponse("<h1>Login</h1>")

def logout(request):
    return HttpResponse("<h1>Logout</h1>")

def register(request):
    return HttpResponse("<h1>Register</h1>")