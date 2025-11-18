import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Man City Win Probability", layout="centered")
st.title("🔵 Manchester City Win Probability Dashboard 2025-26")
st.markdown("Live Elo rating from **clubelo.com** • Updates after every match")

@st.cache_data(ttl=3600, show_spinner="Fetching latest Elo data...")
def get_latest_elo():
    # Try the last 5 days – ClubElo updates once per day after midnight UTC
    base = "http://api.clubelo.com/"
    for i in range(5):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        url = base + date
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and "Club" in response.text:
                return pd.read_csv(url)
        except:
            continue
    return None

df = get_latest_elo()

if df is None:
    st.error("ClubElo data temporarily unavailable – trying again in a few hours usually fixes it.")
    st.stop()

# Safe lookup – will never crash
mancity_row = df[df["Club"] == "Man City"]
if mancity_row.empty:
    st.error("Manchester City not found in latest data – ClubElo format may have changed.")
    st.stop()
else:
    mancity_row = mancity_row.iloc[0]

# Display metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Current Elo Rating", f"{int(mancity_row['Elo'])}")
with col2:
    st.metric("World Rank", f"#{mancity_row['Rank']}")
with col3:
    st.metric("England Rank", f"#{mancity_row['CountryRank']}")
with col4:
    st.metric("Competition", mancity_row['Level'])

# Premier League top 10
st.subheader("Premier League Top 10 (Elo)")
epl = df[df["Country"] == "ENG"].sort_values("Elo", ascending=False).head(10)
epl_display = epl[["Rank", "Club", "Elo"]].copy()
epl_display["Club"] = epl_display["Club"].replace("ManCity", "Manchester City")
st.dataframe(epl_display.reset_index(drop=True), hide_index=True, use_container_width=True)

# Estimated title probability using classic Elo formula
leader_elo = df[df["Country"] == "ENG"].iloc[0]["Elo"]
title_prob = 1 / (1 + 10 ** ((leader_elo - mancity_row["Elo"]) / 100))
st.metric("Estimated Premier League Title Probability", f"{title_prob:.1%}")

st.caption(f"Data from { (datetime.utcnow() - timedelta(days=4)).strftime('%Y-%m-%d') } → today • Source: clubelo.com")
