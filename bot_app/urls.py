from django.urls import path
from . import views

urlpatterns = [
    path('', views.anime_list, name='anime_list'),
    path('anime/<int:pk>/', views.anime_detail, name='anime_detail'),
    path('anime/add/', views.add_anime, name='add_anime'),
]