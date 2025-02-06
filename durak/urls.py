from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('waiting_room/', views.waiting_room, name='waiting_room'),
    path('durak/', views.start_durakgame, name='start_durak'),
]