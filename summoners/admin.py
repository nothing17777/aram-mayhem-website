from django.contrib import admin
from .models import Summoner, Match, Champion, Augment, ChampionAugmentRating

@admin.register(Summoner)
class SummonerAdmin(admin.ModelAdmin):
    list_display = ('name', 'tagline', 'tier', 'rank', 'lp', 'updated_at')
    search_fields = ('name', 'tagline', 'puuid')
    list_filter = ('tier',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_id', 'created_at')
    search_fields = ('match_id',)
    readonly_fields = ('created_at',)

@admin.register(Champion)
class ChampionAdmin(admin.ModelAdmin):
    list_display = ('name', 'champion_class', 'image_url')
    search_fields = ('name', 'champion_class')
    list_filter = ('champion_class',)
    readonly_fields = ('image_url',)

@admin.register(Augment)
class AugmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'image_url')
    search_fields = ('name', 'tier')
    list_filter = ('tier',)
    readonly_fields = ('image_url',)

@admin.register(ChampionAugmentRating)
class ChampionAugmentRatingAdmin(admin.ModelAdmin):
    list_display = ('champion', 'augment', 'rating')
    search_fields = ('champion__name', 'augment__name')
    list_filter = ('rating',)