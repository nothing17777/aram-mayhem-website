import streamlit as st
import os
import django

# 1. Setup Django (Needed to use your models and services)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loltracker.settings')
django.setup()

from summoners import riot_service

# 2. Streamlit UI
st.set_page_config(page_title="League Champion Tool", layout="wide")

st.title("🏆 League of Legends Champion Data")
st.write("Fetching live data from Riot Data Dragon")

# 3. Fetch Data
if st.button("Fetch/Refresh All Champions"):
    with st.spinner("Talking to Riot..."):
        champs = riot_service.get_all_champions_data()
        
        # Display as a Grid
        cols = st.columns(6)
        for idx, (cid, cdata) in enumerate(champs.items()):
            with cols[idx % 6]:
                img_url = f"http://ddragon.leagueoflegends.com/cdn/{riot_service.get_latest_version()}/img/champion/{cid}.png"
                st.image(img_url, caption=f"{cdata['name']}\n({cdata['tags'][0]})")

st.info("Run this with: streamlit run test_streamlit.py")
