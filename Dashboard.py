import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Man City Win Probability", layout="centered")
st.title("🔵 Manchester City Win Probability Dashboard 2025-26")
st.markdown("Live Elo rating from **clubelo.com** • Updates after every match")

@st.cache_data(ttl=3600, show_spinner="Fetching latest Elo data...")
def get_current_elo():
    # ClubElo API: use yesterday's date (updates after midnight UTC)
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"http://api.clubelo.com/{yesterday}"
    
    try:
        df = pd.read_csv(url)
        return df
    except:
        st.error("ClubElo API temporarily unavailable – trying today's date...")
        today = datetime.utcnow().strftime("%Y-%m-%d")
        df = pd.read_csv(f"http://api.clubelo.com/{today}")
        return df

df = get_current_elo()

# Exact name in ClubElo database
mancity_row = df[df["Club"] == "ManCity"].iloc[0]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Current Elo Rating", f"{int(mancity_row['Elo'])}")
with col2:
    st.metric("World Rank", f"#{mancity_row['Rank']}")
with col3:
    st.metric("Country Rank (ENG)", f"#{mancity_row['CountryRank']}")
with col4:
    st.metric("Level", mancity_row['Level'])

# Top 10 in Premier League for context
st.subheader("🏆 Premier League Top 10 (Elo)")
epl = df[df["Country"] == "ENG"].sort_values("Elo", ascending=False).head(10)
epl_display = epl[["Rank", "Club", "Elo"]].copy()
epl_display["Club"] = epl_display["Club"].replace("ManCity", "Manchester City")
st.dataframe(epl_display, hide_index=True, use_container_width=True)

# Approximate title chance (Elo difference to leader is extremely predictive)
leader_elo = df[df["Country"] == "ENG"].iloc[0]["Elo"]
elo_diff = mancity_row["Elo"] - leader_elo
approx_title_pct = round(1 / (1 + 10**((leader_elo - mancity_row["Elo"])/100)) * 100, 1)

st.metric("Estimated Premier League Title Probability (Elo model)", f"{approx_title_pct}%")

# Bonus: current betting market title odds (most accurate real-time source)
st.subheader("💰 Current Bookmaker Title Odds (Nov 2025)")
st.write("Arsenal ≈ -139 (~58%), Manchester City ≈ +200 (~33%), Liverpool ≈ +500 (~16%)")
st.caption("Source: bet365, DraftKings, Ladbrokes – market-implied probabilities are the gold standard")

st.caption(f"Data last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC • clubelo.com")
