from django.urls import path
from . import views

urlpatterns = [
    path('profile/<str:summoner_name>/', views.profile_view, name='profile_view'),
    path('search/', views.search_summoner, name='search_summoner'),
    path('match/<str:match_id>/', views.match_detail_view, name='match_detail_view'),
    path('aram-mayhem/', views.aram_mayhem_view, name='aram_mayhem'),
    path('aram-mayhem/<str:champion_name>/', views.champion_detail_view, name='champion_detail'),
]
