import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.title("🔵 Manchester City Win Probability Dashboard 2025-26")

# FiveThirtyEight data
@st.cache_data(ttl=3600)
def load_data():
    epl = requests.get("https://projects.fivethirtyeight.com/soccer-predictions/forecasts/2025-26_premier-league_forecast.json").json()
    ucl = requests.get("https://projects.fivethirtyeight.com/soccer-predictions/forecasts/2025-26_ucl_forecast.json").json()
    return epl, ucl

epl, ucl = load_data()

# Find Man City
team = "Manchester City"
for t in epl['forecasts'][-1]['teams']:
    if t['name'] == team:
        st.metric("Premier League Title Chance", f"{t['championship']: .1%}")
        st.metric("Top 4 Chance", f"{t['top4']: .1%}")

# Upcoming matches
matches = pd.DataFrame(epl['forecasts'][-1]['upcoming'])
mancity_matches = matches[(matches['team1']==team) | (matches['team2']==team)]
st.subheader("Next Premier League Matches")
st.table(mancity_matches[['date', 'team1', 'team2', 'prob1', 'prob2', 'probtie']].head(10))
