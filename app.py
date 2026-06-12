import streamlit as st
import pandas as pd
import requests
import boto3
import os
import pytz
from datetime import datetime, time as dtime

st.set_page_config(page_title="Golf Edge Dashboard", layout="wide")

DATAGOLF_KEY = os.environ["DATAGOLF_KEY"]
S3_BUCKET = os.environ["S3_BUCKET"]
AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="us-east-1"
)

# ── tournament live check ─────────────────────────────────────────────────────

def is_tournament_live():
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    is_tournament_day = now.weekday() in [3, 4, 5, 6]  # Thu-Sun
    is_playing_hours = dtime(8, 0) <= now.time() <= dtime(20, 0)
    return is_tournament_day and is_playing_hours

ttl = 300 if is_tournament_live() else 3600  # 5 min live, 1 hour otherwise

# ── helpers ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=ttl)
def get_latest_predictions():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix="predictions/")
    files = sorted(
        [obj["Key"] for obj in response.get("Contents", [])
         if obj["Key"].endswith("_predictions.csv")],
        reverse=True
    )
    if not files:
        return None
    df = pd.read_csv(
        f"s3://{S3_BUCKET}/{files[0]}",
        storage_options={"key": AWS_ACCESS_KEY, "secret": AWS_SECRET_KEY}
    )
    return df[df["category"] == "Top5"].copy()


@st.cache_data(ttl=ttl)
def get_book_odds():
    url = "https://feeds.datagolf.com/betting-tools/outrights"
    params = {
        "tour": "pga",
        "market": "top_5",
        "odds_format": "percent",
        "file_format": "json",
        "key": DATAGOLF_KEY,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    books = data.get("books_offering", [])
    rows = []
    for p in data.get("odds", []):
        name = p.get("player_name", "")
        book_probs = []
        for book in books:
            val = p.get(book)
            if val is not None:
                try:
                    book_probs.append(float(val))
                except (ValueError, TypeError):
                    pass
        avg_book = sum(book_probs) / len(book_probs) if book_probs else None
        rows.append({
            "player_name": name,
            "avg_book_prob": avg_book,
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=ttl)
def get_live_stats():
    url = "https://feeds.datagolf.com/preds/live-tournament-stats"
    params = {
        "stats": "sg_total,sg_app,sg_ott,sg_putt",
        "round": "event_cumulative",
        "display": "value",
        "file_format": "json",
        "key": DATAGOLF_KEY,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    rows = []
    for p in data.get("live_stats", []):
        rows.append({
            "player_name": p.get("player_name", ""),
            "position": p.get("position", "-"),
            "total": p.get("total", None),
            "thru": p.get("thru", 0),
            "sg_total": p.get("sg_total", None),
            "sg_app": p.get("sg_app", None),
            "sg_ott": p.get("sg_ott", None),
            "sg_putt": p.get("sg_putt", None),
        })
    return pd.DataFrame(rows)


def normalize_name(n):
    if "," in str(n):
        parts = str(n).split(",", 1)
        return (parts[1].strip() + " " + parts[0].strip()).lower()
    return str(n).lower()


# ── UI ────────────────────────────────────────────────────────────────────────

# st.title("Golf edge dashboard")
st.title("⛳ Fairway Edge  Predictions")

if is_tournament_live():
    st.caption(f"🟢 Live..... | {datetime.now().strftime('%H:%M:%S')} ET")
else:
    st.caption(f"🔴 Game Stopped | {datetime.now().strftime('%H:%M:%S')} ET")



# load data
with st.spinner("Loading..."):
    preds = get_latest_predictions()
    try:
        odds_df = get_book_odds()
        odds_ok = True
    except Exception as e:
        odds_ok = False
        st.warning(f"Could not load odds: {e}")
    try:
        live_df = get_live_stats()
        live_ok = True
    except Exception as e:
        live_ok = False
        st.warning(f"Could not load live stats: {e}")

if preds is None:
    st.error("No predictions found in S3.")
    st.stop()

tournament = preds["tournament"].iloc[0]
year = preds["year"].iloc[0]
st.subheader(f"{tournament} {year}")

# ── merge data ────────────────────────────────────────────────────────────────

preds = preds.copy()
preds["name_key"] = preds["player_name"].apply(normalize_name)

if odds_ok and not odds_df.empty:
    odds_df["name_key"] = odds_df["player_name"].apply(normalize_name)
    preds = preds.merge(odds_df[["name_key", "avg_book_prob"]], on="name_key", how="left")
else:
    preds["avg_book_prob"] = None

if live_ok and not live_df.empty:
    live_df["name_key"] = live_df["player_name"].apply(normalize_name)
    preds = preds.merge(
        live_df[["name_key", "position", "total", "thru", "sg_total", "sg_app", "sg_ott", "sg_putt"]],
        on="name_key", how="left"
    )
else:
    for col in ["position", "total", "thru", "sg_total"]:
        preds[col] = None

preds["your_model_pct"] = (preds["p"] * 100).round(1)
preds["book_pct"] = (preds["avg_book_prob"] * 100).round(1) if "avg_book_prob" in preds else None
preds["edge"] = (preds["your_model_pct"] - preds["book_pct"]).round(1)

# ── metrics ───────────────────────────────────────────────────────────────────

# m1, m2, m3, m4 = st.columns(4)
# m1.metric("Players tracked", len(preds))
# if "edge" in preds.columns and preds["edge"].notna().any():
#     best = preds.loc[preds["edge"].idxmax()]
#     m2.metric("Best edge", f"+{best['edge']}%", best["player_name"].split(",")[0])
#     m3.metric("Positive edges", int((preds["edge"] > 0).sum()))
# else:
#     m2.metric("Odds", "Unavailable")
#     m3.metric("Live", "Pre-tournament" if not live_ok else "Live")

# if live_ok and "thru" in preds.columns:
#     avg_thru = preds["thru"].dropna()
#     if not avg_thru.empty:
#         m4.metric("Avg holes played", f"{avg_thru.mean():.0f}")

# st.divider()

# ── top 5 table ───────────────────────────────────────────────────────────────

st.markdown("### Top 5 model picks")

table_rows = []
for _, row in preds.sort_values("rank").iterrows():
    edge_val = row.get("edge", None)
    has_edge = pd.notna(edge_val)

    if has_edge and edge_val > 50:
        signal = f"🟢 +{edge_val:.1f}%"
    elif has_edge and edge_val < 50:
        signal = f"🟡 +{edge_val:.1f}%"
    elif has_edge and edge_val<30:
        signal = f"🔴 {edge_val:.1f}%"
    else:
        signal = "⚪ —"

    table_rows.append({
        "Rank": int(row["rank"]),
        "Player": row["player_name"],
        "Model %": f"{row['your_model_pct']}%",
        "Book %": f"{row['book_pct']:.1f}%" if pd.notna(row.get("book_pct")) else "—",
        "Edge": signal,
        "Pos": str(row.get("position", "—") or "—"),
        "SG": f"{row['sg_total']:.2f}" if pd.notna(row.get("sg_total")) else "—",
        "Thru": int(row["thru"]) if pd.notna(row.get("thru")) and row.get("thru", 0) > 0 else "—",
    })

st.dataframe(
    pd.DataFrame(table_rows),
    hide_index=True,
    use_container_width=True
)

st.divider()

# ── live leaderboard ──────────────────────────────────────────────────────────

if live_ok and not live_df.empty:
    st.markdown("### Live leaderboard")
    live_display = live_df[["position", "player_name", "total", "thru", "sg_total", "sg_app", "sg_ott", "sg_putt"]].copy()
    live_display.columns = ["Pos", "Player", "Score", "Thru", "SG Total", "SG App", "SG OTT", "SG Putt"]
    st.dataframe(live_display, hide_index=True, use_container_width=True)
