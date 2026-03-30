import requests
import os
from django.conf import settings
from django.core.cache import cache
from urllib.parse import unquote

riot_api = os.getenv("RIOT_API_KEY")

# Cache durations (in seconds)
CACHE_1H = 3600
CACHE_24H = 86400

_latest_version = None
_rune_lookup = None

def get_latest_version():
    global _latest_version
    if _latest_version: return _latest_version
    
    cache_key = "ddragon_version"
    val = cache.get(cache_key)
    if val: 
        _latest_version = val
        return val

    try:
        response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
        versions = response.json()
        _latest_version = versions[0]
        cache.set(cache_key, _latest_version, CACHE_24H)
        return _latest_version
    except:
        return "13.24.1"

def get_all_champions_data():
    v = get_latest_version()
    url = f"http://ddragon.leagueoflegends.com/cdn/{v}/data/en_US/champion.json"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json().get('data', {})
    return {}

def get_rune_lookup():
    global _rune_lookup
    if _rune_lookup is not None: return _rune_lookup
    
    cache_key = "rune_lookup_data"
    val = cache.get(cache_key)
    if val:
        _rune_lookup = val
        return val

    try:
        version = get_latest_version()
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/runesReforged.json"
        data = requests.get(url).json()
        lookup = {}
        for tree in data:
            for slot in tree.get('slots', []):
                for rune in slot.get('runes', []):
                    lookup[rune['id']] = rune['icon']
        _rune_lookup = lookup
        cache.set(cache_key, lookup, CACHE_24H)
        return _rune_lookup
    except Exception as e:
        return {}

def get_summoner_puuid_america(username, tagline):
    username = username.strip()
    tagline = tagline.strip()
    cache_key = f"puuid_{username}_{tagline}".replace(" ", "_").lower()
    
    cached = cache.get(cache_key)
    if cached: return cached

    account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tagline}?api_key={riot_api}"
    response = requests.get(account_url)
    
    if response.status_code != 200:
        raise ValueError(f"Player '{username}#{tagline}' not found.")
        
    puuid = response.json().get("puuid")
    cache.set(cache_key, puuid, CACHE_24H)
    return puuid

def get_summoner_matches(puuid, count=10):
    cache_key = f"matches_{puuid}_{count}"
    cached = cache.get(cache_key)
    if cached: return cached

    match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}&api_key={riot_api}"
    res = requests.get(match_url).json()
    cache.set(cache_key, res, 120) # Match list changes often, cache only 2 mins
    return res
    
def get_match_details(match_id):
    cache_key = f"match_detail_{match_id}"
    cached = cache.get(cache_key)
    if cached: return cached

    match_detail_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={riot_api}"
    res = requests.get(match_detail_url).json()
    cache.set(cache_key, res, CACHE_24H) # Match details NEVER change, cache long!
    return res

def get_summoner_entries(puuid):
    cache_key = f"league_entries_{puuid}"
    cached = cache.get(cache_key)
    if cached: return cached

    url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}?api_key={riot_api}"
    res = requests.get(url).json()
    cache.set(cache_key, res, CACHE_1H) # Cache rank for 1 hour
    return res

def get_summoner_info(puuid):
    cache_key = f"summoner_info_{puuid}"
    cached = cache.get(cache_key)
    if cached: return cached

    url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={riot_api}"
    res = requests.get(url).json()
    cache.set(cache_key, res, CACHE_24H)
    return res

def _get_mock_data(username):
    # Just to return a clean username in UI
    display_name = username.split('#')[0] if '#' in username else username
    return {
        "summonerName": display_name + " (MOCK DATA)",
        "profileIconId": 6334,
        "summonerLevel": 420,
        "tier": "CHALLENGER",
        "rank": "I",
        "lp": 1054,
        "wins": 345,
        "losses": 280,
        "matches": [
            { "result": "Victory", "champion": "Azir", "kda": "12 / 2 / 8", "time": "35m", "champImg": "https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/Azir.png" },
            { "result": "Defeat", "champion": "Orianna", "kda": "4 / 5 / 6", "time": "28m", "champImg": "https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/Orianna.png" },
            { "result": "Victory", "champion": "LeBlanc", "kda": "9 / 1 / 11", "time": "22m", "champImg": "https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/Leblanc.png" }
        ]
    }

def calculate_performance_score(p):
    """
    Calculates a 1-10 performance score based on participant stats.
    Focuses on KDA, Damage, and Gold (The ARAM Trifecta).
    """
    try:
        kills = p.get('kills', 0)
        deaths = max(1, p.get('deaths', 0))
        assists = p.get('assists', 0)
        damage = p.get('totalDamageDealtToChampions', 0)
        gold = p.get('goldEarned', 0)
        
        # 1. KDA Component (0-4 points)
        kda = (kills * 2 + assists) / deaths
        kda_score = min(4, kda / 2) # Caps at 8.0 KDA for max points
        
        # 2. Damage Component (0-4 points)
        # Assuming average ARAM damage is ~20k. 40k+ is a carry.
        damage_score = min(4, damage / 10000)
        
        # 3. Gold Component (0-2 points)
        # Efficiency/Farm check
        gold_score = min(2, gold / 8000)
        
        total = kda_score + damage_score + gold_score
        return round(max(1, total), 1)
    except:
        return 5.0
