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

import streamlit as st
import pandas as pd
import boto3
import os

S3_BUCKET = os.environ["S3_BUCKET"]
AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="us-east-1"
)

st.title("⛳ Golf Tournament Predictions")

# ADD THIS - refreshes every 5 minutes
@st.cache_data(ttl=300)
def get_files():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix="predictions/")
    return [obj["Key"] for obj in response.get("Contents", [])
            if obj["Key"].endswith("_predictions.csv")]

files = get_files()

if not files:
    st.warning("No predictions found yet.")
else:
    selected = st.selectbox("Select Tournament", files)
    df = pd.read_csv(f"s3://{S3_BUCKET}/{selected}",
                     storage_options={
                         "key": AWS_ACCESS_KEY,
                         "secret": AWS_SECRET_KEY
                     })
    st.subheader(f"🏆 {df['tournament'].iloc[0]} {df['year'].iloc[0]}")
    st.dataframe(
        df[["rank", "player_name", "p"]].rename(columns={
            "rank": "Rank",
            "player_name": "Player",
            "p": "Probability"
        }),
        hide_index=True
    )
