import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Man City Win Probability", layout="centered")
st.title("🔵 Manchester City Win Probability Dashboard 2025-26")
st.markdown("Live Elo rating from **clubelo.com** • Updates after every match")

@st.cache_data(ttl=3600, show_spinner="Fetching latest Elo data...")
def get_latest_elo():
    base = "https://api.clubelo.com"
    for i in range(5):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"{base}/{date}"
        try:
            df = pd.read_csv(url)
            if "Club" in df.columns:
                return df
        except Exception:
            continue
    return None

df = get_latest_elo()

if df is None:
    st.error("ClubElo data temporarily unavailable – trying again in a few hours usually fixes it.")
    st.stop()

# Correct club name
mancity_row = df[df["Club"] == "Man City"]
if mancity_row.empty:
    st.error("Manchester City not found in latest data – check club name ('Man City') in ClubElo.")
    st.stop()
else:
    mancity_row = mancity_row.iloc[0]

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Current Elo Rating", f"{int(mancity_row['Elo'])}")
with col2:
    st.metric("World Rank", f"#{mancity_row['Rank']}")
with col3:
    # guard if CountryRank is missing
    if "CountryRank" in df.columns:
        st.metric("England Rank", f"#{mancity_row['CountryRank']}")
with col4:
    st.metric("Competition", mancity_row['Level'])

# Premier League top 10
st.subheader("Premier League Top 10 (Elo)")
epl = df[df["Country"] == "ENG"].sort_values("Elo", ascending=False).head(10)
epl_display = epl[["Rank", "Club", "Elo"]].copy()
epl_display["Club"] = epl_display["Club"].replace({"Man City": "Manchester City"})
st.dataframe(epl_display.reset_index(drop=True), hide_index=True, use_container_width=True)

# Leader-based title probability
leader_elo = df[df["Country"] == "ENG"]["Elo"].max()
title_prob = 1 / (1 + 10 ** ((leader_elo - mancity_row["Elo"]) / 100))
st.metric("Estimated Premier League Title Probability", f"{title_prob:.1%}")
