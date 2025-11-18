import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import math

# ------------------------------------------------------------------
# Page + Man City styling
# ------------------------------------------------------------------
st.set_page_config(page_title="Man City Win Probability", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --city-blue: #6CABDD;
        --city-navy: #00285E;
        --city-light: #f3f7fb;
    }

    .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .city-hero {
        background: linear-gradient(90deg, var(--city-navy), var(--city-blue));
        border-radius: 1.25rem;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 18px 35px rgba(0,0,0,0.15);
    }

    .city-hero-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .city-hero-subtitle {
        font-size: 0.95rem;
        opacity: 0.95;
    }

    .stMetric {
        background: white;
        padding: 0.75rem 1rem;
        border-radius: 0.9rem;
        box-shadow: 0 2px 8px rgba(15,23,42,0.08);
    }

    h2, h3 {
        margin-top: 1.75rem !important;
    }

    .stDataFrame {
        background: white;
        border-radius: 0.9rem;
        box-shadow: 0 1px 6px rgba(15,23,42,0.06);
        padding: 0.25rem 0.25rem 0.5rem 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="city-hero">
        <div class="city-hero-title">🔵 Manchester City Win Probability Dashboard 2025-26</div>
        <div class="city-hero-subtitle">
            Live Elo rating from <strong>clubelo.com</strong> • Updated after every match • Built for City fans
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Elo fetch
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
        except Exception:
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

# Ensure CountryRank exists
if "CountryRank" not in df.columns:
    df["CountryRank"] = df.groupby("Country")["Elo"].rank(
        ascending=False, method="dense"
    )
    mancity_row = df[df["Club"] == "Man City"].iloc[0]

# ------------------------------------------------------------------
# Title probability + key metrics in a single row
# ------------------------------------------------------------------
leader_elo = df[df["Country"] == "ENG"].iloc[0]["Elo"]
title_prob = 1 / (1 + 10 ** ((leader_elo - mancity_row["Elo"]) / 100))
prem_rank = int(mancity_row["CountryRank"])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Premier League Title Probability", f"{title_prob:.1%}")
with col2:
    st.metric("Current Elo Rating", f"{int(mancity_row['Elo'])}")
with col3:
    st.metric("World Elo Rank", f"#{int(mancity_row['Rank'])}")
with col4:
    st.metric("Premier League Elo Rank", f"#{prem_rank}")

# ------------------------------------------------------------------
# Premier League Top 10
# ------------------------------------------------------------------
st.subheader("Premier League Top 10 (Elo)")

epl = df[df["Country"] == "ENG"].sort_values("Elo", ascending=False).head(10)
epl_display = epl[["Rank", "Club", "Elo"]].copy()
epl_display["Club"] = epl_display["Club"].replace("ManCity", "Manchester City")

st.dataframe(
    epl_display.reset_index(drop=True),
    hide_index=True,
    use_container_width=True,
)

st.caption("Relative strength of top 10 by Elo")
st.bar_chart(
    epl_display.set_index("Club")["Elo"],
    height=260,
)

# ------------------------------------------------------------------
# Upcoming matches + Elo-based predictions (football-data.org)
# ------------------------------------------------------------------
st.subheader("Next Manchester City Matches – Elo-based Win Probability")

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
}

def get_next_city_matches():
    """
    Upcoming fixtures from football-data.org
    """
    api_key = st.secrets.get("FOOTBALL_DATA_API_KEY", None)
    if not api_key:
        return None, "no_key"

    url = "https://api.football-data.org/v4/teams/65/matches"  # 65 = Man City
    params = {"status": "SCHEDULED", "limit": 20}
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

def show_fixtures_table(df_to_show, label=""):
    if df_to_show is None or df_to_show.empty:
        st.write(f"No fixtures for {label} yet.")
    else:
        st.dataframe(
            df_to_show.sort_values("Date (UTC)").reset_index(drop=True),
            hide_index=True,
            use_container_width=True,
        )

if fixtures_df is not None:
    main_comps = [
        "Premier League",
        "UEFA Champions League",
        "FA Cup",
        "League Cup",
        "EFL Cup",
    ]

    tab_labels = ["All fixtures"]
    present = set(fixtures_df["Competition"].unique())

    comp_tabs = []
    for name in main_comps:
        if name in present:
            tab_labels.append(name)
            comp_tabs.append(name)

    if len(present - set(comp_tabs)) > 0:
        tab_labels.append("Other")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        show_fixtures_table(fixtures_df, "all competitions")

    tab_index = 1
    for comp_name in comp_tabs:
        with tabs[tab_index]:
            show_fixtures_table(
                fixtures_df[fixtures_df["Competition"] == comp_name],
                comp_name,
            )
        tab_index += 1

    if "Other" in tab_labels:
        with tabs[-1]:
            other_df = fixtures_df[
                ~fixtures_df["Competition"].isin(comp_tabs)
            ]
            show_fixtures_table(other_df, "other competitions")

else:
    if fixtures_err == "no_key":
        st.info(
            "To see upcoming fixtures and win probabilities across all tournaments, "
            "add a free API key from football-data.org to Streamlit secrets as "
            "`FOOTBALL_DATA_API_KEY`."
        )
    elif fixtures_err == "no_matches":
        st.info("No upcoming Manchester City matches found in the fixture API.")
    else:
        st.warning("Unable to load fixtures right now. Please try again later.")

# ------------------------------------------------------------------
# Last 2 matches – ratings & reactions (links only, no scraping)
# ------------------------------------------------------------------
st.subheader("Last 2 Matches – Ratings & Reactions")

@st.cache_data(ttl=6 * 3600, show_spinner="Loading recent matches...")
def get_recent_city_matches(limit=2):
    """
    Last finished matches from football-data.org
    """
    api_key = st.secrets.get("FOOTBALL_DATA_API_KEY", None)
    if not api_key:
        return None, "no_key"

    url = "https://api.football-data.org/v4/teams/65/matches"
    params = {"status": "FINISHED", "limit": limit}
    headers = {"X-Auth-Token": api_key}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        data = r.json()
    except Exception:
        return None, "network"

    matches = data.get("matches", [])
    if not matches:
        return None, "no_matches"

    rows = []
    for m in matches:
        utc_date = m["utcDate"]
        dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d %H:%M")

        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        comp = m["competition"]["name"]
        match_id = m["id"]

        home_goals = m["score"]["fullTime"]["home"]
        away_goals = m["score"]["fullTime"]["away"]

        if m["homeTeam"]["id"] == 65:
            venue = "Home"
            city_goals = home_goals
            opp_goals = away_goals
            opponent = away
        else:
            venue = "Away"
            city_goals = away_goals
            opp_goals = home_goals
            opponent = home

        result_str = f"{city_goals}-{opp_goals}"
        rows.append(
            {
                "MatchID": match_id,
                "Date (UTC)": date_str,
                "Competition": comp,
                "Venue": venue,
                "Opponent": opponent,
                "CityGoals": city_goals,
                "OppGoals": opp_goals,
                "Scoreline": result_str,
            }
        )

    return pd.DataFrame(rows), None


recent_df, recent_err = get_recent_city_matches()

# Map: our match key -> (ratings_url, report_url)
# You can update this dict as new games are played.
MATCH_LINKS = {
    # Example:
    # "123456": {
    #     "ratings": "https://www.whoscored.com/Matches/123456/LiveStatistics",
    #     "report": "https://www.mancity.com/news/mens/match-report-link"
    # }
}

if recent_df is not None:
    tab_titles = [
        f"{row['Scoreline']} vs {row['Opponent']} ({row['Competition']})"
        for _, row in recent_df.iterrows()
    ]
    match_tabs = st.tabs(tab_titles)

    for (idx, row), tab in zip(recent_df.iterrows(), match_tabs):
        with tab:
            st.write(f"**Date (UTC):** {row['Date (UTC)']}")
            st.write(f"**Competition:** {row['Competition']}")
            st.write(f"**Venue:** {row['Venue']}")
            st.write(
                f"**Result:** Manchester City {row['CityGoals']} – {row['OppGoals']} {row['Opponent']}"
            )

            link_info = MATCH_LINKS.get(str(row["MatchID"]), {})

            ratings_url = link_info.get("ratings")
            report_url = link_info.get("report")

            st.markdown("---")
            st.write("### Player ratings & match reaction")

            cols_rr = st.columns(2)
            with cols_rr[0]:
                if ratings_url:
                    st.link_button("View detailed player ratings", ratings_url)
                else:
                    st.caption(
                        "Player ratings link not configured yet – add a WhoScored/SofaScore URL in `MATCH_LINKS`."
                    )
            with cols_rr[1]:
                if report_url:
                    st.link_button("Read match report & quotes", report_url)
                else:
                    st.caption(
                        "Match report link not configured yet – add a ManCity/BBC article URL in `MATCH_LINKS`."
                    )
else:
    if recent_err == "no_key":
        st.info(
            "To see last match details, add a free API key from football-data.org "
            "to Streamlit secrets as `FOOTBALL_DATA_API_KEY`."
        )
    elif recent_err == "no_matches":
        st.info("No finished Manchester City matches found in the fixture API.")
    else:
        st.warning("Unable to load recent match details right now. Please try again later.")

# ------------------------------------------------------------------
# Footnote
# ------------------------------------------------------------------
st.caption(
    f"Data from { (datetime.utcnow() - timedelta(days=4)).strftime('%Y-%m-%d') } → today • "
    "Elo source: clubelo.com • Fixtures & results: football-data.org"
)
