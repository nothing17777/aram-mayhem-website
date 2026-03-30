from django.db import models

class Summoner(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=100)
    puuid = models.CharField(max_length=120, unique=True, db_index=True)
    profile_icon_id = models.IntegerField(default=0)
    profile_icon_url = models.URLField(blank=True, null=True)
    level = models.IntegerField(default=1)
    
    # Rank details (these change often)
    tier = models.CharField(max_length=100, default="Unranked")
    rank = models.CharField(max_length=20, blank=True, null=True)
    lp = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}#{self.tagline}"

class Match(models.Model):
    # match_id from Riot (e.g., NA1_5522181306)
    match_id = models.CharField(max_length=100, unique=True, db_index=True)
    json_data = models.JSONField(null=True, blank=True)
    mvp_puuid = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.match_id

class Champion(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)
    champion_class = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Augment(models.Model):
    name = models.CharField(max_length=200)
    tier = models.CharField(max_length=50) # Silver, Gold, Prismatic
    description = models.TextField()
    image_url = models.URLField()

    def __str__(self):
        return f"{self.tier} - {self.name}"

class ChampionAugmentRating(models.Model):
    champion = models.ForeignKey(Champion, on_delete=models.CASCADE, related_name='augment_ratings')
    augment = models.ForeignKey(Augment, on_delete=models.CASCADE, related_name='champion_ratings')
    rating = models.CharField(max_length=50) # S Tier, A Tier, Bait, etc.
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.champion.name} - {self.augment.name} ({self.rating})"