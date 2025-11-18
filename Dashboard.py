import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Man City Win Probability", layout="centered")
st.title("🔵 Manchester City Win Probability Dashboard 2025-26")
st.markdown("Live data from **FiveThirtyEight** • Updated daily")

# Cache the data for 1 hour
@st.cache_data(ttl=3600, show_spinner="Fetching latest predictions...")
def load_fivethirtyeight_data():
    try:
        # Premier League
        epl_url = "https://projects.fivethirtyeight.com/soccer-predictions/forecasts/2025-26_premier-league_forecast.json"
        epl_data = requests.get(epl_url).json()
        
        # Champions League (if available)
        ucl_url = "https://projects.fivethirtyeight.com/soccer-predictions/forecasts/2025-26_ucl_forecast.json"
        ucl_data = requests.get(ucl_url).json()
        
        return epl_data, ucl_data
    except:
        st.error("Could not fetch data right now. FiveThirtyEight might not have published 2025-26 forecasts yet, or the season URL changed.")
        return None, None

epl_data, ucl_data = load_fivethirtyeight_data()

if epl_data is None:
    st.stop()

# Find latest forecast
latest = epl_data["forecasts"][-1]
teams = pd.DataFrame(latest["teams"])
mancity = teams[teams["name"] == "Manchester City"].iloc[0]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Premier League Title Chance", f"{mancity['championship']:.1%}")
with col2:
    st.metric("Top 4 Chance", f"{mancity['top4']:.1%}")
with col3:
    st.metric("Projected Points", f"{mancity['points']:.1f}")
with col4:
    st.metric("Current SPI Rating", f"{mancity['rating']:.1f}")

# Upcoming matches
st.subheader("🔜 Next Premier League Matches")
upcoming = pd.DataFrame(latest.get("upcoming", []))
if not upcoming.empty:
    # Filter matches involving Man City
    city_matches = upcoming[
        (upcoming["team1"] == "Manchester City") | 
        (upcoming["team2"] == "Manchester City")
    ].copy()
    
    city_matches["date"] = pd.to_datetime(city_matches["date"]).dt.strftime("%b %d")
    city_matches["opponent"] = city_matches.apply(
        lambda x: x["team2"] if x["team1"] == "Manchester City" else x["team1"], axis=1
    )
    city_matches["win_prob"] = city_matches.apply(
        lambda x: x["prob1"] if x["team1"] == "Manchester City" else x["prob2"], axis=1
    )
    city_matches["venue"] = city_matches.apply(
        lambda x: "Home" if x["team1"] == "Manchester City" else "Away", axis=1
    )
    
    display = city_matches[["date", "venue", "opponent", "win_prob"]].head(8)
    display["win_prob"] = (display["win_prob"] * 100).round(1).astype(str) + "%"
    st.dataframe(display, hide_index=True, use_container_width=True)

# Champions League (if data exists)
if ucl_data:
    try:
        ucl_latest = ucl_data["forecasts"][-1]
        ucl_teams = pd.DataFrame(ucl_latest["teams"])
        ucl_city = ucl_teams[ucl_teams["name"] == "Manchester City"].iloc[0]
        
        st.subheader("🏆 UEFA Champions League Outlook")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chance to Advance to Knockouts", f"{ucl_city.get('make_playoffs', ucl_city.get('advancement', {}).get('Round of 16', 0)):.1%}")
        with col2:
            st.metric("Chance to Win UCL", f"{ucl_city['championship']:.1%}")
        with col3:
            st.metric("Projected Group Finish", f"{ucl_city['proj_rank']:.0f}th")
    except:
        st.info("Champions League data not yet available or format changed.")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC • Source: FiveThirtyEight")
