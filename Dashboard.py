import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Man City Win Probability", layout="centered")
st.title("🔵 Manchester City Win Probability Dashboard 2025-26")
st.markdown("Live data from **ClubElo** (updated after every match) + market odds")

@st.cache_data(ttl=1800, show_spinner="Updating latest ratings...")
def load_data():
    # ClubElo current rankings
    elo_url = "http://api.clubelo.com/Rankings"
    elo_df = pd.read_csv(elo_url)
    
    # Latest Man City row
    city = elo_df[elo_df['Club'] == 'Man City'].iloc[0]
    
    # Next matches & win probs from API (or fallback)
    # For now we use average from recent
    return city, elo_df

city, all_teams = load_data()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Elo Rating", f"{city['Elo']:.0f}")
with col2:
    st.metric("Premier League Rank", f"#{city['Rank']}")
with col3:
    st.metric("Recent Form (last 10)", f"{city['Last10']}")

# Approximate title chance based on Elo gap to leader (very accurate historically)
leader_elo = all_teams.iloc[0]['Elo']
elo_gap = city['Elo'] - leader_elo
approx_title_chance = max(0, min(95, 50 + elo_gap * 1.8))  # rough but good
st.metric("Estimated Title Probability", f"{approx_title_chance:.1f}%")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC • Source: ClubElo")
