# import streamlit as st
# import pandas as pd
# import boto3
# import os

# S3_BUCKET = os.environ["S3_BUCKET"]
# s3_client = boto3.client("s3")

# st.title("⛳ Golf Tournament Predictions")

# # List all prediction files in S3
# response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix="predictions/")
# files = [obj["Key"] for obj in response.get("Contents", []) 
#          if obj["Key"].endswith("_predictions.csv")]

# if not files:
#     st.warning("No predictions found yet.")
# else:
#     # Dropdown to select tournament
#     selected = st.selectbox("Select Tournament", files)
    
#     # Load and display
#     df = pd.read_csv(f"s3://{S3_BUCKET}/{selected}")
    
#     st.subheader(f"🏆 {df['tournament'].iloc[0]} {df['year'].iloc[0]}")
#     st.dataframe(
#         df[["rank", "player_name", "p"]].rename(columns={
#             "rank": "Rank",
#             "player_name": "Player",
#             "p": "Probability"
#         }),
#         hide_index=True
#     )

# import streamlit as st
# import pandas as pd
# import boto3
# import os

# S3_BUCKET = os.environ["S3_BUCKET"]
# AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
# AWS_SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

# s3_client = boto3.client(
#     "s3",
#     aws_access_key_id=AWS_ACCESS_KEY,
#     aws_secret_access_key=AWS_SECRET_KEY,
#     region_name="us-east-1"
# )

# st.title("⛳ Golf Tournament Predictions")

# response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix="predictions/")
# files = [obj["Key"] for obj in response.get("Contents", [])
#          if obj["Key"].endswith("_predictions.csv")]

# if not files:
#     st.warning("No predictions found yet.")
# else:
#     selected = st.selectbox("Select Tournament", files)
#     df = pd.read_csv(f"s3://{S3_BUCKET}/{selected}",
#                      storage_options={
#                          "key": AWS_ACCESS_KEY,
#                          "secret": AWS_SECRET_KEY
#                      })

#     st.subheader(f"🏆 {df['tournament'].iloc[0]} {df['year'].iloc[0]}")
#     st.dataframe(
#         df[["rank", "player_name", "p"]].rename(columns={
#             "rank": "Rank",
#             "player_name": "Player",
#             "p": "Probability"
#         }),
#         hide_index=True
#     )

# import streamlit as st
# import pandas as pd
# import boto3
# import os

# S3_BUCKET = os.environ["S3_BUCKET"]
# AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
# AWS_SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

# s3_client = boto3.client(
#     "s3",
#     aws_access_key_id=AWS_ACCESS_KEY,
#     aws_secret_access_key=AWS_SECRET_KEY,
#     region_name="us-east-1"
# )

# st.title("⛳ Golf Tournament Predictions")

# # ADD THIS - refreshes every 5 minutes
# @st.cache_data(ttl=300)
# def get_files():
#     response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix="predictions/")
#     return [obj["Key"] for obj in response.get("Contents", [])
#             if obj["Key"].endswith("_predictions.csv")]

# files = get_files()

# if not files:
#     st.warning("No predictions found yet.")
# else:
#     selected = st.selectbox("Select Tournament", files)
#     df = pd.read_csv(f"s3://{S3_BUCKET}/{selected}",
#                      storage_options={
#                          "key": AWS_ACCESS_KEY,
#                          "secret": AWS_SECRET_KEY
#                      })
#     st.subheader(f"🏆 {df['tournament'].iloc[0]} {df['year'].iloc[0]}")
#     st.dataframe(
#         df[["rank", "player_name", "p"]].rename(columns={
#             "rank": "Rank",
#             "player_name": "Player",
#             "p": "Probability"
#         }),
#         hide_index=True
#     )

# import streamlit as st
# import pandas as pd
# import boto3
# import os

# S3_BUCKET = os.environ["S3_BUCKET"]
# AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
# AWS_SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

# s3_client = boto3.client(
#     "s3",
#     aws_access_key_id=AWS_ACCESS_KEY,
#     aws_secret_access_key=AWS_SECRET_KEY,
#     region_name="us-east-1"
# )

# st.title("⛳ Golf Tournament Predictions")

# @st.cache_data(ttl=300)
# def get_files():
#     response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix="predictions/")
#     return [obj["Key"] for obj in response.get("Contents", [])
#             if obj["Key"].endswith("_predictions.csv")]

# files = get_files()

# if not files:
#     st.warning("No predictions found yet.")
# else:
#     # Sort files and show latest by default
#     files_sorted = sorted(files, reverse=True)
    
#     selected = st.selectbox(
#         "Select Tournament", 
#         files_sorted,
#         index=0  # always selects latest file by default
#     )
    
#     df = pd.read_csv(f"s3://{S3_BUCKET}/{selected}",
#                      storage_options={
#                          "key": AWS_ACCESS_KEY,
#                          "secret": AWS_SECRET_KEY
#                      })
#     st.subheader(f"🏆 {df['tournament'].iloc[0]} {df['year'].iloc[0]}")
#     st.dataframe(
#         df[["rank", "player_name", "p"]].rename(columns={
#             "rank": "Rank",
#             "player_name": "Player",
#             "p": "Probability"
#         }),
#         hide_index=True
#     )
import streamlit as st
import pandas as pd
import requests
import boto3
import os
from datetime import datetime

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

# ── helpers ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
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


# @st.cache_data(ttl=300)
# def get_book_odds():
#     url = "https://feeds.datagolf.com/betting-tools/outrights"
#     params = {
#         "tour": "pga",
#         "market": "top_5",
#         "odds_format": "percent",
#         "file_format": "json",
#         "key": DATAGOLF_KEY,
#     }
#     r = requests.get(url, params=params, timeout=30)
#     r.raise_for_status()
#     data = r.json()
#     rows = []
#     for p in data.get("odds", []):
#         name = p.get("player_name", "")
#         dg_prob = p.get("datagolf_base_history", {}).get("baseline", None)
#         # average implied prob across all books that have odds
#         book_probs = []
#         for k, v in p.items():
#             if k not in ("player_name", "dg_id", "datagolf_base_history") and isinstance(v, dict):
#                 imp = v.get("implied_prob", None)
#                 if imp is not None:
#                     book_probs.append(imp)
#         avg_book = sum(book_probs) / len(book_probs) if book_probs else None
#         rows.append({
#             "player_name": name,
#             "dg_model_prob": dg_prob,
#             "avg_book_prob": avg_book,
#         })
#     return pd.DataFrame(rows)

@st.cache_data(ttl=300)
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

    # log raw structure so we can see what comes back
    st.write("Raw odds API response keys:", list(data.keys()) if isinstance(data, dict) else type(data))
    st.write("Sample:", str(data)[:500])

    rows = []
    for p in data.get("odds", []):
        name = p.get("player_name", "")
        # collect all book implied probs
        book_probs = []
        for k, v in p.items():
            if k not in ("player_name", "dg_id", "datagolf_base_history") and isinstance(v, dict):
                imp = v.get("implied_prob", None)
                if imp is not None:
                    book_probs.append(float(imp))
        avg_book = sum(book_probs) / len(book_probs) if book_probs else None
        rows.append({
            "player_name": name,
            "avg_book_prob": avg_book,
        })
    return pd.DataFrame(rows)
    
@st.cache_data(ttl=300)
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
    """Last, First -> first last lowercase for fuzzy matching."""
    if "," in str(n):
        parts = str(n).split(",", 1)
        return (parts[1].strip() + " " + parts[0].strip()).lower()
    return str(n).lower()


# ── UI ───────────────────────────────────────────────────────────────────────

st.title("Golf edge dashboard")
st.caption(f"Refreshes every 5 minutes — last load: {datetime.now().strftime('%H:%M:%S')}")

col_refresh = st.columns([6, 1])[1]
if col_refresh.button("Refresh now"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# load data
with st.spinner("Loading predictions, odds and live stats..."):
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

# ── build merged table ────────────────────────────────────────────────────────

preds = preds.copy()
preds["name_key"] = preds["player_name"].apply(normalize_name)

if odds_ok and not odds_df.empty:
    odds_df["name_key"] = odds_df["player_name"].apply(normalize_name)
    preds = preds.merge(odds_df[["name_key", "dg_model_prob", "avg_book_prob"]],
                        on="name_key", how="left")
else:
    preds["dg_model_prob"] = None
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

# edge score: your model p vs avg book implied prob
preds["your_model_pct"] = (preds["p"] * 100).round(1)
preds["book_pct"] = (preds["avg_book_prob"] * 100).round(1) if "avg_book_prob" in preds else None
preds["edge"] = (preds["your_model_pct"] - preds["book_pct"]).round(1)

# ── metric row ───────────────────────────────────────────────────────────────

m1, m2, m3, m4 = st.columns(4)
m1.metric("Players tracked", len(preds))
if "edge" in preds.columns and preds["edge"].notna().any():
    best = preds.loc[preds["edge"].idxmax()]
    m2.metric("Best edge", f"+{best['edge']}%", best["player_name"].split(",")[0])
    positive = (preds["edge"] > 0).sum()
    m3.metric("Positive edges", int(positive))
else:
    m2.metric("Odds status", "Unavailable")
    m3.metric("Live status", "Pre-tournament" if not live_ok else "Live")

if live_ok and "thru" in preds.columns:
    avg_thru = preds["thru"].dropna()
    if not avg_thru.empty:
        m4.metric("Avg holes played", f"{avg_thru.mean():.0f}")

st.divider()

# ── player cards ─────────────────────────────────────────────────────────────

st.markdown("### Your top 5 model picks")

for _, row in preds.sort_values("rank").iterrows():
    edge_val = row.get("edge", None)
    has_edge = pd.notna(edge_val)

    if has_edge and edge_val > 5:
        border = "2px solid #1D9E75"
        badge_bg = "#E1F5EE"
        badge_color = "#0F6E56"
        signal = f"BET +{edge_val:.1f}%"
    elif has_edge and edge_val > 0:
        border = "0.5px solid #5DCAA5"
        badge_bg = "#E1F5EE"
        badge_color = "#0F6E56"
        signal = f"Lean +{edge_val:.1f}%"
    elif has_edge:
        border = "0.5px solid var(--color-border-tertiary)"
        badge_bg = "#FCEBEB"
        badge_color = "#A32D2D"
        signal = f"Skip {edge_val:.1f}%"
    else:
        border = "0.5px solid var(--color-border-tertiary)"
        badge_bg = "#F1EFE8"
        badge_color = "#5F5E5A"
        signal = "No odds"

    with st.container():
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])

        c1.markdown(f"**{int(row['rank'])}. {row['player_name']}**")

        c2.markdown(
            f"<span style='font-size:13px; color:var(--color-text-secondary)'>Your model</span><br>"
            f"<span style='font-size:18px; font-weight:500'>{row['your_model_pct']}%</span>",
            unsafe_allow_html=True
        )

        book_display = f"{row['book_pct']}%" if pd.notna(row.get('book_pct')) else "—"
        c3.markdown(
            f"<span style='font-size:13px; color:var(--color-text-secondary)'>Book implied</span><br>"
            f"<span style='font-size:18px; font-weight:500'>{book_display}</span>",
            unsafe_allow_html=True
        )

        sg_display = f"{row['sg_total']:.2f}" if pd.notna(row.get('sg_total')) else "—"
        pos_display = row.get('position', '—') or '—'
        thru_display = f"thru {int(row['thru'])}" if pd.notna(row.get('thru')) and row.get('thru', 0) > 0 else "not started"
        c4.markdown(
            f"<span style='font-size:13px; color:var(--color-text-secondary)'>Live pos / SG</span><br>"
            f"<span style='font-size:18px; font-weight:500'>{pos_display}</span> "
            f"<span style='font-size:12px; color:var(--color-text-secondary)'>{thru_display} · SG {sg_display}</span>",
            unsafe_allow_html=True
        )

        c5.markdown(
            f"<span style='font-size:13px; color:var(--color-text-secondary)'>Signal</span><br>"
            f"<span style='background:{badge_bg}; color:{badge_color}; "
            f"padding:3px 10px; border-radius:6px; font-size:13px; font-weight:500'>{signal}</span>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div style='border-top:{border}; margin:8px 0 16px 0'></div>",
            unsafe_allow_html=True
        )

st.divider()

# ── full live leaderboard ─────────────────────────────────────────────────────

if live_ok and not live_df.empty:
    st.markdown("### Live leaderboard")
    live_display = live_df[["position", "player_name", "total", "thru", "sg_total", "sg_app", "sg_ott", "sg_putt"]].copy()
    live_display.columns = ["Pos", "Player", "Score", "Thru", "SG Total", "SG App", "SG OTT", "SG Putt"]
    st.dataframe(live_display, hide_index=True, use_container_width=True)
