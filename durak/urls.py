from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('waiting_room/<uuid:room_id>/', views.waiting_room, name='waiting_room'),
]