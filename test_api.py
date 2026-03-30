import os
import django
import streamlit as st

# Setup Django environment so we can import from our existing apps without errors
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "loltracker.settings")
django.setup()

import summoners.riot_service as rs

st.set_page_config(page_title="Riot API Tester", layout="wide")
st.title("🎮 Riot API Tester")
st.write("Use this quick dashboard to test the output of your `summoners/riot_service.py` logic directly!")

username = st.text_input("Enter a Riot ID (e.g. Faker#KR1, nothing#17777)")

if st.button("Fetch Summoner"):
    if username:
        with st.spinner(f"Fetching data for {username}..."):
            parts = username.split("#", 1)  # split on first # only
            name, tag = parts[0], parts[1] if len(parts) > 1 else "NA1"
            puuid = rs.get_summoner_puuid_america(name, tag)
            matches = rs.get_summoner_matches(puuid, count=1)
            match_details = rs.get_match_details(matches[0])
            st.success("Fetched Successfully!")
            st.subheader("First Participant (you) — full JSON")
            # Find the searched player
            target = None
            for p in match_details["info"]["participants"]:
                if p.get("riotIdGameName", "").lower() == name.lower():
                    target = p
                    break
            if target:
                st.json(target)
            else:
                st.warning("Could not find you in participants — showing all:")
                st.json(match_details["info"]["participants"][0])
    else:
        st.error("Please enter a username.")
