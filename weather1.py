import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import time

st.set_page_config(page_title="Live Sensor Dashboard", layout="wide")

# ------------------------------
# Google Sheets authentication via Streamlit secrets
# ------------------------------
creds_dict = dict(st.secrets["gspread"])
# Ensure multi-line private key is parsed correctly
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

scope = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ------------------------------
# Sheet info
# ------------------------------
SHEET_ID = "1Uecp6hM7EridbdZczfo7cxlF9n_SX4jYKiJAPTGn3o4"
WORKSHEET_NAME = "sheet1"
sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)

COLUMN_NAMES = [
    "timestamp", "temp1", "humidity1", "temp2", "humidity2",
    "light1", "light2", "UV", "temp3", "humidity3", "pressure"
]

# ------------------------------
# Function to fetch data
# ------------------------------
@st.cache_data(ttl=55)  # refresh cache every ~55 seconds
def get_data():
    raw = sheet.get_all_values()
    df = pd.DataFrame(raw[1:], columns=COLUMN_NAMES)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in COLUMN_NAMES[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ------------------------------
# Auto-refresh every 60s
# ------------------------------
st_autorefresh = st.experimental_rerun

df = get_data()

st.title("🌡️ Live Sensor Dashboard")

# ------------------------------
# Temperature plot
# ------------------------------
temp_fig = px.line(
    df, x="timestamp", y=["temp1", "temp2", "temp3"],
    labels={"value": "Temperature", "timestamp": "Time"}, 
    title="Temperature Sensors"
)
st.plotly_chart(temp_fig, use_container_width=True)

# ------------------------------
# Humidity plot
# ------------------------------
hum_fig = px.line(
    df, x="timestamp", y=["humidity1", "humidity2", "humidity3"],
    labels={"value": "Humidity", "timestamp": "Time"}, 
    title="Humidity Sensors"
)
st.plotly_chart(hum_fig, use_container_width=True)

# ------------------------------
# Light plot
# ------------------------------
light_fig = px.line(
    df, x="timestamp", y=["light1", "light2"],
    labels={"value": "Light", "timestamp": "Time"}, 
    title="Light Sensors"
)
st.plotly_chart(light_fig, use_container_width=True)

# ------------------------------
# UV plot
# ------------------------------
uv_fig = px.line(
    df, x="timestamp", y="UV",
    labels={"UV": "UV Index", "timestamp": "Time"}, 
    title="UV Sensor"
)
st.plotly_chart(uv_fig, use_container_width=True)

# ------------------------------
# Pressure plot
# ------------------------------
pressure_fig = px.line(
    df, x="timestamp", y="pressure",
    labels={"pressure": "Pressure", "timestamp": "Time"}, 
    title="Pressure Sensor"
)
st.plotly_chart(pressure_fig, use_container_width=True)

st.caption("Data refreshes automatically every ~60 seconds.")
