from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.conf import settings
from . import riot_service
from .models import Summoner, Match, Champion
import requests

# Shared spell/rune mapping used by both profile and match detail views
SPELL_MAP = {
    1: "SummonerBoost", 3: "SummonerExhaust", 4: "SummonerFlash",
    6: "SummonerHaste", 7: "SummonerHeal", 11: "SummonerSmite",
    12: "SummonerTeleport", 13: "SummonerMana", 14: "SummonerDot",
    21: "SummonerBarrier", 32: "SummonerSnowball"
}
STYLE_MAP = {
    8000: "7201_Precision", 8100: "7200_Domination", 8200: "7202_Sorcery",
    8300: "7203_Whimsy", 8400: "7204_Resolve"
}

def enrich_participant(p):
    """Adds spell1_img, spell2_img, primary_style, sub_style, keystone_img, rune_pages."""
    p['spell1_img'] = SPELL_MAP.get(p.get('summoner1Id'), 'SummonerFlash')
    p['spell2_img'] = SPELL_MAP.get(p.get('summoner2Id'), 'SummonerDot')
    styles = p.get('perks', {}).get('styles', [])
    rune_lookup = riot_service.get_rune_lookup()

    if styles:
        p['primary_style'] = STYLE_MAP.get(styles[0].get('style'), '7201_Precision')
        p['sub_style'] = STYLE_MAP.get(styles[1].get('style'), '7204_Resolve') if len(styles) > 1 else '7204_Resolve'

        # Keystone = first selection of first style
        try:
            keystone_id = styles[0]['selections'][0]['perk']
            p['keystone_img'] = rune_lookup.get(keystone_id, '')
        except (IndexError, KeyError):
            p['keystone_img'] = ''

        # Build full rune tree for the detail panel
        rune_pages = []
        for style in styles:
            page = {
                'style_img': STYLE_MAP.get(style.get('style'), ''),
                'selections': []
            }
            for sel in style.get('selections', []):
                perk_id = sel.get('perk')
                img = rune_lookup.get(perk_id, '')
                page['selections'].append({'perk': perk_id, 'img': img})
            rune_pages.append(page)
        p['rune_pages'] = rune_pages
    else:
        p['primary_style'] = '7201_Precision'
        p['sub_style'] = '7204_Resolve'
        p['keystone_img'] = ''
        p['rune_pages'] = []


def profile_view(request, summoner_name):
    try:
        if '-' not in summoner_name:
            return redirect('home')
        
        # Get match count from URL, default to 10
        count = int(request.GET.get('count', 10))
            
        name, tagline = summoner_name.split('-', 1)
        
        # 1. Get or create Summoner in DB
        puuid = riot_service.get_summoner_puuid_america(name, tagline)
        print(f"DEBUG: Found PUUID for {name}#{tagline}: {puuid}")
        
        summoner_obj, created = Summoner.objects.get_or_create(puuid=puuid)
        
        # Update details if new or not recently updated
        summoner_info = riot_service.get_summoner_info(puuid)
        league_entries = riot_service.get_summoner_entries(puuid)
        print(f"DEBUG: Fetched summoner info and league entries.")
        
        summoner_obj.name = name
        summoner_obj.tagline = tagline
        summoner_obj.profile_icon_id = summoner_info.get('profileIconId', 0)
        summoner_obj.level = summoner_info.get('summonerLevel', 1)
        
        if league_entries:
            entry = league_entries[0]
            summoner_obj.tier = entry.get('tier', 'Unranked').capitalize()
            summoner_obj.rank = entry.get('rank', '')
            summoner_obj.lp = entry.get('leaguePoints', 0)
            summoner_obj.wins = entry.get('wins', 0)
            summoner_obj.losses = entry.get('losses', 0)
        
        summoner_obj.save()

        # 2. Get Matches
        match_ids = riot_service.get_summoner_matches(puuid, count=count)
        print(f"DEBUG: Received {len(match_ids)} match IDs from Riot: {match_ids}")
        
        matches = []
        for mid in match_ids:
            # Check DB for match first
            match_record, m_created = Match.objects.get_or_create(match_id=mid)
            
            # Use raw JSON if we have it, otherwise fetch
            if m_created or not match_record.json_data or 'info' not in match_record.json_data:
                m_data = riot_service.get_match_details(mid)
                if m_data and 'info' in m_data:
                    match_record.json_data = m_data
                    match_record.save()
                    print(f"DEBUG: Fetched and saved match {mid} from API.")
                else:
                    print(f"DEBUG: Failed to fetch data for match {mid}.")
                    continue
            else:
                m_data = match_record.json_data
                print(f"DEBUG: Loaded match {mid} from DB.")

            # 2. Enrich and calculate stats for ALL participants
            duration_sec = m_data['info'].get('gameDuration', 0)
            duration_min = max(duration_sec / 60.0, 1.0)
            
            # Formatted duration string (e.g., 25m 12s)
            m_data['info']['duration_str'] = f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s"
            
            # Formatted timestamp (Basic date for now)
            import datetime
            ts = m_data['info'].get('gameEndTimestamp', 0) / 1000
            m_data['info']['date_str'] = datetime.datetime.fromtimestamp(ts).strftime('%b %d, %Y')
            
            for p in m_data['info']['participants']:
                enrich_participant(p)
                # Calculate the 1-10 performance score
                p['performance_score'] = riot_service.calculate_performance_score(p)
                
                total_cs = p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0)
                p['cs_per_min'] = total_cs / duration_min
            
            # Add to matches list
            matches.append(m_data)

        print(f"DEBUG: Final count of matches in context: {len(matches)}")

        # 3. Build the final context
        version = riot_service.get_latest_version()
        profile_icon_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{summoner_obj.profile_icon_id}.png"
        
        total_g = summoner_obj.wins + summoner_obj.losses
        win_rate = (summoner_obj.wins / total_g * 100) if total_g > 0 else 0

        context = {
            'username': summoner_obj.name,
            'tagline': summoner_obj.tagline,
            'profileIconUrl': profile_icon_url,
            'summonerLevel': summoner_obj.level,
            'tier': summoner_obj.tier,
            'rank': summoner_obj.rank,
            'lp': summoner_obj.lp,
            'wins': summoner_obj.wins,
            'losses': summoner_obj.losses,
            'win_rate': win_rate,
            'matches': matches,
            'puuid': puuid,
            'version': version,
            'current_count': count,
            'next_count': count + 5,
            'riot_id': summoner_name
        }
        return render(request, 'summoners/profile.html', context)
    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'summoners/profile.html', {"error": str(e)})

def search_summoner(request):
    query = request.GET.get('q')
    if query and '#' in query:
        # Sanitize query: remove all spaces and then swap # for -
        # This fixes "nothing # 17777" -> "nothing-17777"
        sanitized_query = query.strip().replace(' ', '').replace('#', '-')
        return redirect('profile_view', summoner_name=sanitized_query)
    return redirect('home')

def match_detail_view(request, match_id):
    try:
        print(f"DEBUG Scoreboard: Loading match {match_id}")
        # 1. Fetch from DB or API
        match_record, created = Match.objects.get_or_create(match_id=match_id)
        if created or not match_record.json_data or 'info' not in match_record.json_data:
            match_detail = riot_service.get_match_details(match_id)
            if match_detail and 'info' in match_detail:
                match_record.json_data = match_detail
                match_record.save()
            else:
                print(f"DEBUG Scoreboard: API Failed to return info for {match_id}")
                return redirect('home')
        else:
            match_detail = match_record.json_data
        
        print(f"DEBUG Scoreboard: Match data contains 'info': {'info' in match_detail}")
        
        # 2. Prepare Match-wide Info
        version = riot_service.get_latest_version()
        duration_sec = match_detail['info'].get('gameDuration', 0)
        mins, secs = divmod(duration_sec, 60)
        match_detail['info']['formatted_duration'] = f"{mins}m {secs}s"
        
        blue_win = False
        red_win = False

        participants = match_detail['info'].get('participants', [])
        print(f"DEBUG Scoreboard: Found {len(participants)} participants")

        # 3. Process every player
        duration_min = max(duration_sec / 60.0, 1.0) # Avoid division by zero
        mvp_score = -1
        mvp_puuid = None

        for p in participants:
            # CS calculation
            total_cs = p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0)
            p['cs_per_min'] = total_cs / duration_min

            # Calculate the 1-10 performance score for ALL
            p['performance_score'] = riot_service.calculate_performance_score(p)

            # Track MVP (Highest total score)
            if p['performance_score'] > mvp_score:
                mvp_score = p['performance_score']
                mvp_puuid = p['puuid']

            # Determine team wins
            if p['teamId'] == 100 and p['win']: blue_win = True
            if p['teamId'] == 200 and p['win']: red_win = True
            
            # Add spell/rune icons
            enrich_participant(p)

            # Add Rank data
            p_puuid = p['puuid']
            s_obj, s_created = Summoner.objects.get_or_create(puuid=p_puuid)
            
            if s_created or not s_obj.tier or s_obj.tier == "Unranked":
                try:
                    entries = riot_service.get_summoner_entries(puuid)
                    if entries:
                        entry = entries[0]
                        s_obj.tier = entry.get('tier', 'Unranked').capitalize()
                        s_obj.rank = entry.get('rank', '')
                        s_obj.lp = entry.get('leaguePoints', 0)
                        s_obj.wins = entry.get('wins', 0)
                        s_obj.losses = entry.get('losses', 0)
                        s_obj.name = p.get('riotIdGameName', '')
                        s_obj.tagline = p.get('riotIdTagline', '')
                        s_obj.save()
                except:
                    pass
            
            p['tier'] = s_obj.tier
            p['rank'] = s_obj.rank
            p['wins'] = s_obj.wins
            p['losses'] = s_obj.losses
            p['lp'] = s_obj.lp
            total_g = s_obj.wins + s_obj.losses
            p['win_rate'] = (s_obj.wins / total_g * 100) if total_g > 0 else 0

        # 4. Find the Peaks for scaling bars
        max_dmg = max((p.get('totalDamageDealtToChampions', 0) for p in participants), default=1)
        max_tank = max((p.get('totalDamageTaken', 0) for p in participants), default=1)
        if max_dmg == 0: max_dmg = 1
        if max_tank == 0: max_tank = 1

        context = {
            'match': match_detail,
            'info': match_detail['info'],
            'participants': participants,
            'blue_win': blue_win,
            'red_win': red_win,
            'version': version,
            'max_dmg': max_dmg,
            'max_tank': max_tank
        }
        return render(request, 'summoners/match_detail.html', context)
    except Exception as e:
        print(f"Match Detail Error: {e}")
        return redirect('home')

from .models import Champion, Augment, ChampionAugmentRating

def aram_mayhem_view(request):
    query = request.GET.get('q', '').strip()
    selected_class = request.GET.get('class', '').strip()
    
    champions = Champion.objects.all()
    
    # Filter by name
    if query:
        champions = champions.filter(name__icontains=query)
    
    # Filter by class (Assassin, Mage, Tank, etc.)
    if selected_class and selected_class != 'All':
        champions = champions.filter(champion_class__icontains=selected_class)
    
    champions = champions.order_by('name')
    
    # Get all unique classes for the filter buttons
    all_classes = Champion.objects.values_list('champion_class', flat=True).distinct().order_by('champion_class')
    
    return render(request, 'summoners/aram_mayhem.html', {
        'champions': champions,
        'query': query,
        'selected_class': selected_class,
        'all_classes': all_classes
    })

def champion_detail_view(request, champion_name):
    # Use name-based lookup
    champion = get_object_or_404(Champion, name=champion_name)
    
    # Get all synergies we've scraped
    synergies = champion.augment_ratings.all().select_related('augment')
    
    context = {
        'champion': champion,
        's_tier': synergies.filter(rating__icontains='S'),
        'a_tier': synergies.filter(rating__icontains='A'),
        'b_tier': synergies.filter(rating__icontains='B'),
        'c_tier': synergies.filter(rating__icontains='C'),
        'baits': synergies.filter(Q(rating__icontains='Bait') | Q(rating__icontains='D')),
        'version': riot_service.get_latest_version(),
    }
    return render(request, 'summoners/champion_detail.html', context)

def aram_mayhem_search(request):
    query = request.GET.get('q')