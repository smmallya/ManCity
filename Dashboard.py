import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import math

# ------------------------------------------------------------------
# Page + simple "modern" styling
# ------------------------------------------------------------------
st.set_page_config(page_title="Man City Win Probability", layout="wide")

st.markdown(
    """
    <style>
    /* Make main background lighter and content tighter */
    .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    /* Metric row spacing */
    .stMetric {
        background: #f9fafb;
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(15,23,42,0.08);
    }
    /* Section headers */
    h2, h3 {
        margin-top: 1.75rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔵 Manchester City Win Probability Dashboard 2025-26")
st.markdown("Live Elo rating from **clubelo.com** • Updates after every match")

# ------------------------------------------------------------------
# Existing Elo fetch (unchanged logic)
# ------------------------------------------------------------------
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

# Ensure CountryRank exists (fix for earlier error)
if "CountryRank" not in df.columns:
    df["CountryRank"] = df.groupby("Country")["Elo"].rank(
        ascending=False, method="dense"
    )
    mancity_row = df[df["Club"] == "Man City"].iloc[0]

# ------------------------------------------------------------------
# Metrics row
# ------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Current Elo Rating", f"{int(mancity_row['Elo'])}")
with col2:
    st.metric("World Rank", f"#{mancity_row['Rank']}")
with col3:
    st.metric("England Rank", f"#{int(mancity_row['CountryRank'])}")
with col4:
    st.metric("Competition", mancity_row['Level'])

# ------------------------------------------------------------------
# Premier League top 10
# ------------------------------------------------------------------
st.subheader("Premier League Top 10 (Elo)")
epl = df[df["Country"] == "ENG"].sort_values("Elo", ascending=False).head(10)
epl_display = epl[["Rank", "Club", "Elo"]].copy()
epl_display["Club"] = epl_display["Club"].replace("ManCity", "Manchester City")
st.dataframe(epl_display.reset_index(drop=True), hide_index=True, use_container_width=True)

# Optional: small bar chart for a more modern feel
st.caption("Relative strength of top 10 by Elo")
st.bar_chart(
    epl_display.set_index("Club")["Elo"],
    height=260,
)

# ------------------------------------------------------------------
# Estimated title probability using classic Elo formula
# ------------------------------------------------------------------
leader_elo = df[df["Country"] == "ENG"].iloc[0]["Elo"]
title_prob = 1 / (1 + 10 ** ((leader_elo - mancity_row["Elo"]) / 100))
st.metric("Estimated Premier League Title Probability", f"{title_prob:.1%}")

# ------------------------------------------------------------------
# Upcoming matches + Elo-based predictions (using football-data.org)
# ------------------------------------------------------------------

st.subheader("Next Manchester City Matches – Elo-based Win Probability")

# Map football-data.org team names to ClubElo names
CLUB_NAME_MAP = {
    "Manchester City FC": "Man City",
    "Arsenal FC": "Arsenal",
    "Liverpool FC": "Liverpool",
    "Chelsea FC": "Chelsea",
    "Tottenham Hotspur FC": "Tottenham",
    "Manchester United FC": "Man United",
    "Newcastle United FC": "Newcastle",
    "Aston Villa FC": "Aston Villa",
    "Brighton & Hove Albion FC": "Brighton",
    "Crystal Palace FC": "Crystal Palace",
    "AFC Bournemouth": "Bournemouth",
    # add more here if needed
}

def get_next_city_matches():
    """
    Uses free-tier football-data.org API.
    Requires an API key in Streamlit secrets as FOOTBALL_DATA_API_KEY.
    Returns a pandas DataFrame or (None, reason).
    """
    api_key = st.secrets.get("FOOTBALL_DATA_API_KEY", None)
    if not api_key:
        return None, "no_key"

    url = "https://api.football-data.org/v4/teams/65/matches"  # 65 = Man City
    params = {"status": "SCHEDULED", "limit": 5}
    headers = {"X-Auth-Token": api_key}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        data = r.json()
    except Exception:
        return None, "network"

    matches = data.get("matches", [])
    rows = []

    for m in matches:
        utc_date = m["utcDate"]
        dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
        # show in local time-ish (you can adjust to timezone if needed)
        date_str = dt.strftime("%Y-%m-%d %H:%M")

        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        comp = m["competition"]["name"]

        if m["homeTeam"]["id"] == 65:
            venue = "Home"
            opp_name_fd = away
        else:
            venue = "Away"
            opp_name_fd = home

        opp_elo_name = CLUB_NAME_MAP.get(opp_name_fd)
        opp_elo = None
        win_prob = None

        if opp_elo_name and (df["Club"] == opp_elo_name).any():
            opp_elo = float(df.loc[df["Club"] == opp_elo_name, "Elo"].iloc[0])

            # Simple Elo win probability with home advantage
            home_adv = 100
            city_elo = float(mancity_row["Elo"])

            if venue == "Home":
                city_adj = city_elo + home_adv
                opp_adj = opp_elo
            else:
                city_adj = city_elo
                opp_adj = opp_elo + home_adv

            win_prob = 1 / (1 + 10 ** ((opp_adj - city_adj) / 400))

        rows.append(
            {
                "Date (UTC)": date_str,
                "Competition": comp,
                "Venue": venue,
                "Opponent": opp_name_fd,
                "Opponent Elo": round(opp_elo, 1) if opp_elo else None,
                "City win chance": f"{win_prob*100:0.1f}%"
                if win_prob is not None
                else "N/A",
            }
        )

    if not rows:
        return None, "no_matches"

    return pd.DataFrame(rows), None


fixtures_df, fixtures_err = get_next_city_matches()

if fixtures_df is not None:
    st.dataframe(
        fixtures_df,
        hide_index=True,
        use_container_width=True,
    )
else:
    if fixtures_err == "no_key":
        st.info(
            "To see upcoming fixtures and win probabilities, add a free API key from "
            "football-data.org to Streamlit secrets as `FOOTBALL_DATA_API_KEY`."
        )
    elif fixtures_err == "no_matches":
        st.info("No upcoming Manchester City matches found in the fixture API.")
    else:
        st.warning("Unable to load fixtures right now. Please try again later.")

# ------------------------------------------------------------------
# Footnote
# ------------------------------------------------------------------
st.caption(
    f"Data from { (datetime.utcnow() - timedelta(days=4)).strftime('%Y-%m-%d') } → today • "
    "Elo source: clubelo.com • Fixtures: football-data.org"
)
