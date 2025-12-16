import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import time
from streamlit_autorefresh import st_autorefresh

# --- Configuration ---
SHEET_ID = "1DGkrU18QI7dItEiVZvMhBPMJNA2dSMSD1HvR6jK1E44"
WORKSHEET_DATA_NAME = "Data"
WORKSHEET_ARCHIVE_NAME = "Archive"
# ... (rest of configuration)

# Column names must match the order of your Python logger's output
COLUMN_NAMES = [
    "timestamp", "temp1", "humidity1", "temp2", "humidity2",
    "light1", "light2", "UV", "temp3", "humidity3", "pressure"
]
ARCHIVE_COLUMN_NAMES = [
    "Hour_Start", "temp1", "humidity1", "temp2", "humidity2",
    "light1", "light2", "UV", "temp3", "humidity3", "pressure"
]

# ------------------------------
# Google Sheets Authentication (Helper Function)
# ------------------------------
@st.cache_resource
def get_gspread_client():
    """Authenticates and returns the gspread client. Cached with st.cache_resource."""
    try:
        creds_dict = dict(st.secrets["gspread"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        scope = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

# ------------------------------
# Function to fetch data from the 'Data' sheet (10s/1m res)
# ------------------------------
@st.cache_data(ttl=60)
def get_data(sheet_id, worksheet_name):
    """Fetches and processes the high-resolution data."""
    client = get_gspread_client()
    if not client:
        return pd.DataFrame(columns=COLUMN_NAMES)
        
    try:
        sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    except Exception as e:
        st.error(f"Could not open worksheet {worksheet_name}: {e}")
        return pd.DataFrame(columns=COLUMN_NAMES)
        
    raw = sheet.get_all_values()
    if len(raw) <= 1:
        return pd.DataFrame(columns=COLUMN_NAMES)
        
    df = pd.DataFrame(raw[1:], columns=COLUMN_NAMES)
    
    # Convert types
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in COLUMN_NAMES[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    return df

# ------------------------------
# Function to fetch data from the 'Archive' sheet (1h res)
# ------------------------------
@st.cache_data(ttl=3600)
def get_archive_data(sheet_id, worksheet_name):
    """Fetches and processes the hourly consolidated data."""
    client = get_gspread_client()
    if not client:
        return pd.DataFrame(columns=ARCHIVE_COLUMN_NAMES)
        
    try:
        sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    except Exception as e:
        st.error(f"Could not open worksheet {worksheet_name}: {e}")
        return pd.DataFrame(columns=ARCHIVE_COLUMN_NAMES)
        
    raw = sheet.get_all_values()
    if len(raw) <= 1:
        return pd.DataFrame(columns=ARCHIVE_COLUMN_NAMES)
        
    df_archive = pd.DataFrame(raw[1:], columns=ARCHIVE_COLUMN_NAMES)
    
    df_archive.rename(columns={'Hour_Start': 'timestamp'}, inplace=True)
    
    # Convert types
    df_archive["timestamp"] = pd.to_datetime(df_archive["timestamp"])
    for col in ARCHIVE_COLUMN_NAMES[1:]:
        df_archive[col] = pd.to_numeric(df_archive[col], errors="coerce")
        
    return df_archive


# ------------------------------
# Auto-refresh and Data Loading
# ------------------------------
st.set_page_config(page_title="Live Sensor Dashboard", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")

# Fetch both DataFrames
df_data = get_data(SHEET_ID, WORKSHEET_DATA_NAME)
df_archive = get_archive_data(SHEET_ID, WORKSHEET_ARCHIVE_NAME)

# --- Combine DataFrames (Logic remains the same) ---
# ... (rest of the combination and plotting logic from your previous response)

# --- Combination Logic ---
if not df_archive.empty and not df_data.empty:
    latest_archive_time = df_archive['timestamp'].max()
    df_data_filtered = df_data[df_data['timestamp'] > latest_archive_time]
    df_combined = pd.concat([df_archive, df_data_filtered], ignore_index=True)
elif df_archive.empty:
    df_combined = df_data
else:
    df_combined = df_archive

if df_combined.empty:
    st.warning("No data found in either the 'Data' or 'Archive' sheets.")
    st.stop()
    
df_combined.sort_values(by='timestamp', inplace=True)

# ------------------------------
# Dashboard Title and Plotting
# ------------------------------
st.title("🌡️ Live Weather Station Dashboard")

st.markdown(f"**Current Resolution:** 10s (Today) / 1m (Last 7 Days) / 1h (Archived)")
st.caption(f"Showing **{len(df_combined):,}** data points, ranging from **{df_combined['timestamp'].min().strftime('%Y-%m-%d')}** to **{df_combined['timestamp'].max().strftime('%Y-%m-%d %H:%M')}**.")

# Temperature plot (using df_combined)
temp_fig = px.line(
    df_combined, x="timestamp", y=["temp1", "temp2", "temp3"],
    labels={"value": "Temperature (°C)", "timestamp": "Time"},  
    title="Temperature Sensors (Full History)",
    line_shape='linear'
)
st.plotly_chart(temp_fig, use_container_width=True)

# Humidity plot (using df_combined)
hum_fig = px.line(
    df_combined, x="timestamp", y=["humidity1", "humidity2", "humidity3"],
    labels={"value": "Relative Humidity (%)", "timestamp": "Time"},  
    title="Humidity Sensors (Full History)",
    line_shape='linear'
)
st.plotly_chart(hum_fig, use_container_width=True)

# Light, UV, and Pressure Plots
col1, col2, col3 = st.columns(3)

with col1:
    light_fig = px.line(
        df_combined, x="timestamp", y=["light1", "light2"],
        labels={"value": "Light (Raw ADC)", "timestamp": "Time"},  
        title="Light Sensors (Full History)",
        line_shape='linear'
    )
    st.plotly_chart(light_fig, use_container_width=True)

with col2:
    uv_fig = px.line(
        df_combined, x="timestamp", y="UV",
        labels={"UV": "UV Index", "timestamp": "Time"},  
        title="UV Sensor (Full History)",
        line_shape='linear'
    )
    st.plotly_chart(uv_fig, use_container_width=True)

with col3:
    pressure_fig = px.line(
        df_combined, x="timestamp", y="pressure",
        labels={"pressure": "Pressure (Pa)", "timestamp": "Time"},  
        title="Pressure Sensor (Full History)",
        line_shape='linear'
    )
    st.plotly_chart(pressure_fig, use_container_width=True)


st.caption("Data refreshes automatically every ~60 seconds. Plots show combined historical data.")
