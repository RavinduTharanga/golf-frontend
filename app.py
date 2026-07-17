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

# ── checkpoint config ──────────────────────────────────────────────────────
# label shown on button -> (S3 prefix to search, filename matcher within that prefix)
ROUND_TAGS = ("_r1_", "_r2_", "_r3_")

CHECKPOINT_CONFIG = {
    # Same file(s) the original script used: anything ending in
    # "_predictions.csv" that ISN'T tagged as an r1/r2/r3 checkpoint file.
    # Already has player_name / rank / p / tournament / year — no renaming needed.
    "Pre-Tournament": {
        "prefix": "predictions/",
        "matcher": lambda key: key.endswith("_predictions.csv") and not any(tag in key for tag in ROUND_TAGS),
        "column_map": {},
    },
    # results_post_r1/live_post_r1_top10_predictions.csv
    # columns: dg_id, player_name, r1_sg_total, r1_rank, r1_strokes_back, p_top10
    # no tournament/year in this file — falls back to the live-stats event name.
    "After Round 1": {
        "prefix": "results_post_r1/",
        "matcher": lambda key: key.endswith("_top10_predictions.csv"),
        "column_map": {"r1_rank": "rank", "p_top10": "p"},
    },
    # Guessing the same naming pattern will be used for rounds 2/3 —
    # update prefix/matcher/column_map here once those folders exist.
    "After Round 2": {
        "prefix": "results_post_r2/",
        "matcher": lambda key: key.endswith("_top10_predictions.csv"),
        "column_map": {"r2_rank": "rank", "p_top10": "p"},
    },
    "After Round 3": {
        "prefix": "results_post_r3/",
        "matcher": lambda key: key.endswith("_top10_predictions.csv"),
        "column_map": {"r3_rank": "rank", "p_top10": "p"},
    },
}
DEFAULT_CHECKPOINT = "Pre-Tournament"

if "checkpoint" not in st.session_state:
    st.session_state.checkpoint = DEFAULT_CHECKPOINT

# ── tournament live check ─────────────────────────────────────────────────────

def is_tournament_live():
    et = pytz.timezone("America/New_York")
    now = datetime.now(pytz.utc).astimezone(et)
    is_tournament_day = now.weekday() in [3, 4, 5, 6]  # Thu-Sun
    is_playing_hours = dtime(8, 0) <= now.time() <= dtime(20, 0)
    return is_tournament_day and is_playing_hours

ttl = 300 if is_tournament_live() else 3600  # 5 min live, 1 hour otherwise

# ── helpers ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_latest_predictions(checkpoint_label: str):
    """Loads the most recent predictions file in S3 matching this checkpoint."""
    config = CHECKPOINT_CONFIG[checkpoint_label]
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=config["prefix"])
    files = sorted(
        [obj for obj in response.get("Contents", [])
         if config["matcher"](obj["Key"])],
        key=lambda x: x["LastModified"],
        reverse=True
    )
    if not files:
        return None
    latest_key = files[0]["Key"]
    df = pd.read_csv(
        f"s3://{S3_BUCKET}/{latest_key}",
        storage_options={"key": AWS_ACCESS_KEY, "secret": AWS_SECRET_KEY}
    )
    if config["column_map"]:
        df = df.rename(columns=config["column_map"])
    if "category" in df.columns:
        df = df[df["category"] == "Top10"].copy()
    return df


@st.cache_data(ttl=ttl)
def get_book_odds():
    """Returns (dataframe, event_name). event_name='' if no odds market open yet."""
    url = "https://feeds.datagolf.com/betting-tools/outrights"
    params = {
        "tour": "pga",
        "market": "top_10",
        "odds_format": "percent",
        "file_format": "json",
        "key": DATAGOLF_KEY,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    event_name = data.get("event_name", "")
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
        rows.append({"player_name": name, "avg_book_prob": avg_book})
    return pd.DataFrame(rows), event_name


@st.cache_data(ttl=ttl)
def get_live_stats():
    """Returns (dataframe, event_name). event_name='' if round hasn't started."""
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
    event_name = data.get("event_name", "")
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
    return pd.DataFrame(rows), event_name


def normalize_name(n):
    if "," in str(n):
        parts = str(n).split(",", 1)
        return (parts[1].strip() + " " + parts[0].strip()).lower()
    return str(n).lower()


def adjust_probability(base_p: float, sg_total, thru) -> float:
    """Adjust base model probability using live SG performance."""
    if pd.isna(sg_total) or pd.isna(thru) or thru == 0:
        return base_p
    holes_weight = min(thru / 18, 1.0)
    ADJUSTMENT_FACTOR = 0.03
    adjustment = sg_total * ADJUSTMENT_FACTOR * holes_weight
    adjusted = base_p * (1 + adjustment)
    return round(min(max(adjusted, 0.0), 1.0), 4)


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("⛳ Fairway Edge Predictions")

# ── checkpoint button row ───────────────────────────────────────────────────
cols = st.columns(len(CHECKPOINT_CONFIG))
for col, label in zip(cols, CHECKPOINT_CONFIG.keys()):
    is_active = st.session_state.checkpoint == label
    if col.button(
        label,
        use_container_width=True,
        type="primary" if is_active else "secondary",
        key=f"btn_{label}",
    ):
        st.session_state.checkpoint = label
        st.rerun()

active_label = st.session_state.checkpoint

et = pytz.timezone("America/New_York")
now_et = datetime.now(pytz.utc).astimezone(et)

live_now = is_tournament_live()
if live_now:
    st.caption(f"🟢 Live | {now_et.strftime('%H:%M:%S')} ET")
else:
    st.caption(f"🔴 No active round | {now_et.strftime('%H:%M:%S')} ET")

# ── load data ──────────────────────────────────────────────────────────────────

with st.spinner("Loading..."):
    preds = get_latest_predictions(active_label)

    if preds is None:
        st.error(f"No '{active_label}' predictions found in S3.")
        st.stop()

    # live stats — fetch first, since round-checkpoint files (r1/r2/r3)
    # don't carry their own tournament/year columns; we borrow the event
    # name from this feed in that case
    try:
        live_df, live_event_name = get_live_stats()
        live_fetch_ok = not live_df.empty
    except Exception as e:
        live_df, live_event_name = pd.DataFrame(), ""
        live_fetch_ok = False
        st.warning(f"Could not load live stats: {e}")

    if "tournament" in preds.columns:
        tournament = preds["tournament"].iloc[0]
        year = preds["year"].iloc[0]
    else:
        tournament = live_event_name or "Current Tournament"
        year = now_et.year

    live_ok = live_fetch_ok and (live_event_name == tournament)

    # odds — usually available once the field is set, even pre-tournament
    try:
        odds_df, odds_event_name = get_book_odds()
        odds_ok = (not odds_df.empty) and (odds_event_name == tournament)
    except Exception as e:
        odds_ok = False
        odds_event_name = ""
        st.warning(f"Could not load odds: {e}")

st.subheader(f"{tournament} {year} — {active_label}")

if not odds_ok and odds_event_name and odds_event_name != tournament:
    st.info(f"Odds board is still showing '{odds_event_name}' — not open yet for {tournament}.")

if not live_ok:
    if live_event_name and live_event_name != tournament:
        st.info(f"Live stats are for '{live_event_name}' — {tournament} hasn't teed off yet.")
    else:
        st.info(f"{tournament} hasn't started yet — live position/SG will appear once round 1 tees off.")

# ── merge data ────────────────────────────────────────────────────────────────

preds = preds.copy()
preds["name_key"] = preds["player_name"].apply(normalize_name)

if odds_ok:
    odds_df = odds_df.copy()
    odds_df["name_key"] = odds_df["player_name"].apply(normalize_name)
    preds = preds.merge(odds_df[["name_key", "avg_book_prob"]], on="name_key", how="left")
else:
    preds["avg_book_prob"] = None

if live_ok:
    live_df = live_df.copy()
    live_df["name_key"] = live_df["player_name"].apply(normalize_name)
    preds = preds.merge(
        live_df[["name_key", "position", "total", "thru", "sg_total", "sg_app", "sg_ott", "sg_putt"]],
        on="name_key", how="left"
    )
else:
    for col in ["position", "total", "thru", "sg_total"]:
        preds[col] = None

# live adjustment only does anything once thru > 0, otherwise returns base_p unchanged
preds["adjusted_p"] = preds.apply(
    lambda row: adjust_probability(row["p"], row.get("sg_total"), row.get("thru")),
    axis=1
)

preds["your_model_pct"] = (preds["p"] * 100).round(1)
preds["adjusted_pct"] = (preds["adjusted_p"] * 100).round(1)
preds["book_pct"] = (preds["avg_book_prob"] * 100).round(1) if "avg_book_prob" in preds else None
preds["edge"] = (preds["adjusted_pct"] - preds["book_pct"]).round(1)

st.divider()

# ── top 10 table ───────────────────────────────────────────────────────────────

st.markdown(f"### Top 10 model picks — {active_label}")

table_rows = []
for _, row in preds.sort_values("rank").iterrows():
    edge_val = row.get("edge", None)
    has_edge = pd.notna(edge_val)

    if has_edge and edge_val > 5:
        signal = f"🟢 +{edge_val:.1f}%"
    elif has_edge and edge_val > 0:
        signal = f"🟡 +{edge_val:.1f}%"
    elif has_edge:
        signal = f"🔴 {edge_val:.1f}%"
    else:
        signal = "⚪ —"

    table_rows.append({
        "Rank": int(row["rank"]),
        "Player": row["player_name"],
        "Model %": f"{row['your_model_pct']}%",
        "Live adj %": f"{row['adjusted_pct']}%" if live_ok else "—",
        "Book %": f"{row['book_pct']:.1f}%" if pd.notna(row.get("book_pct")) else "—",
        "Edge": signal,
        "Pos": str(row.get("position", "—") or "—") if live_ok else "—",
        "SG": f"{row['sg_total']:.2f}" if live_ok and pd.notna(row.get("sg_total")) else "—",
        "Thru": int(row["thru"]) if live_ok and pd.notna(row.get("thru")) and row.get("thru", 0) > 0 else "—",
    })

st.dataframe(
    pd.DataFrame(table_rows),
    hide_index=True,
    use_container_width=True
)

st.divider()

# ── live leaderboard ──────────────────────────────────────────────────────────

if live_ok:
    st.markdown("### Live leaderboard")
    live_display = live_df[["position", "player_name", "total", "thru", "sg_total", "sg_app", "sg_ott", "sg_putt"]].copy()
    live_display.columns = ["Pos", "Player", "Score", "Thru", "SG Total", "SG App", "SG OTT", "SG Putt"]
    st.dataframe(live_display, hide_index=True, use_container_width=True)
