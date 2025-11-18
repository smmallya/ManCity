import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ----------------------------------------------------
# Page setup
# ----------------------------------------------------
st.set_page_config(page_title="Man City Win Probability", layout="centered")
st.title("🔵 Manchester City Win Probability Dashboard 2025-26")
st.markdown("Live Elo rating from **clubelo.com** • Updates after every match")

# ----------------------------------------------------
# Data fetch
# ----------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Fetching latest Elo data...")
def get_latest_elo():
    """
    Try last 5 days of ClubElo daily CSV.
    Returns (df, date_string) or (None, None) on failure.
    """
    base = "https://api.clubelo.com"
    for i in range(5):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"{base}/{date}"
        try:
            df = pd.read_csv(url)
            # sanity check
            if "Club" in df.columns and "Elo" in df.columns:
                return df, date
        except Exception:
            continue
    return None, None


df, data_date = get_latest_elo()

if df is None:
    st.error(
        "ClubElo data temporarily unavailable – trying again in a few hours usually fixes it."
    )
    st.stop()

# ----------------------------------------------------
# Find Manchester City row robustly
# ----------------------------------------------------
club_candidates = ["Man City", "Manchester City", "ManCity"]
mancity = pd.DataFrame()

for name in club_candidates:
    mancity = df[df["Club"] == name]
    if not mancity.empty:
        club_name_in_data = name
        break

if mancity.empty:
    st.error(
        "Manchester City not found in latest ClubElo data – the naming/format may have changed."
    )
    st.stop()

mancity_row = mancity.iloc[0]

# ----------------------------------------------------
# Compute England (country) rank ourselves
# ----------------------------------------------------
# Rank by Elo within each country (higher Elo = rank 1)
df["CountryRankLocal"] = df.groupby("Country")["Elo"].rank(
    ascending=False, method="dense"
)
eng_rank = int(
    df.loc[df["Club"] == club_name_in_data, "CountryRankLocal"].iloc[0]
)

# ----------------------------------------------------
# Metrics
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current Elo Rating", f"{int(mancity_row['Elo'])}")

with col2:
    st.metric("World Rank", f"#{int(mancity_row['Rank'])}")

with col3:
    st.metric("England Rank", f"#{eng_rank}")

with col4:
    st.metric("Competition", str(mancity_row["Level"]))

# ----------------------------------------------------
# Premier League top 10 (by Elo)
# ----------------------------------------------------
st.subheader("Premier League Top 10 (Elo)")
epl = df[df["Country"] == "ENG"].sort_values("Elo", ascending=False).head(10)

epl_display = epl[["Rank", "Club", "Elo"]].copy()
epl_display["Club"] = epl_display["Club"].replace(
    {"Man City": "Manchester City", "ManCity": "Manchester City"}
)

st.dataframe(
    epl_display.reset_index(drop=True),
    hide_index=True,
    use_container_width=True,
)

# ----------------------------------------------------
# Title probability (simple Elo-based estimate)
# ----------------------------------------------------
leader_elo = epl["Elo"].max()
# Using /400 is the standard Elo logistic; change back to /100 if you prefer your steeper curve
title_prob = 1 / (1 + 10 ** ((leader_elo - mancity_row["Elo"]) / 400))

st.metric(
    "Estimated Premier League Title Probability",
    f"{title_prob:.1%}",
)

# ----------------------------------------------------
# Footnote
# ----------------------------------------------------
if data_date:
    st.caption(f"Data from {data_date} (UTC daily dump) • Source: clubelo.com")
else:
    st.caption("Date of data unknown • Source: clubelo.com")
