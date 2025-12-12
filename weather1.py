import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# ------------------------------
# Google Sheets authentication
# ------------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

SHEET_ID = "1Uecp6hM7EridbdZczfo7cxlF9n_SX4jYKiJAPTGn3o4"
WORKSHEET_NAME = "sheet1"
sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)

COLUMN_NAMES = [
    "timestamp", "temp1", "humidity1", "temp2", "humidity2",
    "light1", "light2", "UV", "temp3", "humidity3", "pressure"
]

def get_data():
    raw = sheet.get_all_values()
    df = pd.DataFrame(raw[1:], columns=COLUMN_NAMES)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in COLUMN_NAMES[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ------------------------------
# Streamlit App
# ------------------------------
st.title("Live Sensor Dashboard")

# Refresh every 60 seconds
st_autorefresh = st.experimental_rerun()

df = get_data()

# ------------------------------
# Temperature plot
# ------------------------------
temp_fig = px.line(df, x="timestamp", y=["temp1","temp2","temp3"], title="Temperature")
st.plotly_chart(temp_fig, use_container_width=True)

# ------------------------------
# Humidity plot
# ------------------------------
hum_fig = px.line(df, x="timestamp", y=["humidity1","humidity2","humidity3"], title="Humidity")
st.plotly_chart(hum_fig, use_container_width=True)

# ------------------------------
# Light plot
# ------------------------------
light_fig = px.line(df, x="timestamp", y=["light1","light2"], title="Light")
st.plotly_chart(light_fig, use_container_width=True)

# ------------------------------
# UV plot
# ------------------------------
uv_fig = px.line(df, x="timestamp", y="UV", title="UV")
st.plotly_chart(uv_fig, use_container_width=True)

# ------------------------------
# Pressure plot
# ------------------------------
pressure_fig = px.line(df, x="timestamp", y="pressure", title="Pressure")
st.plotly_chart(pressure_fig, use_container_width=True)
