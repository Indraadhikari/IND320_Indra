# components.py
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import requests


# CSS Helper
@st.cache_data(show_spinner=False)
def apply_styles():

    css = f"""
    <style>
    /* Hide Streamlit default multi-page navigation */
    div[data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    """
    st.markdown(css, unsafe_allow_html=True)
    
@st.cache_data(show_spinner=False)
def show_sidebar():
    st.sidebar.title("Navigation")
    # --- Overview ---
    with st.sidebar.expander("Overview", expanded=True): # Expanded by default for main navigation
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Map_And_Selector.py", label="🗺️ Map Overview")
        st.page_link("pages/4_Energy Production.py", label="⚡ Energy Production")


    # --- Explorative Analysis ---
    with st.sidebar.expander("Explorative Analysis", expanded=True):
        st.page_link("pages/5_Table.py", label="📊 Tables")
        st.page_link("pages/6_Plot.py", label="📈 Plots")
        st.page_link("pages/5_STL and Spectrogram.py", label="🔦 STL & Spectrogram")

    # --- Spatial / Climate Analysis ---
    with st.sidebar.expander("Energy & Climate Analysis", expanded=True):
        st.page_link("pages/2_Snow_drift.py", label="❄️ Snow Drift Analysis")
        # st.page_link("pages/7_Wind_Rose.py", label="🌬️ Wind Rose") # optional if you have this
        st.page_link("pages/3_Sliding_Window_Correlation.py", label="🛰️ Sliding Correlation")

    # --- Data Quality & Anomalies ---
    with st.sidebar.expander("Data Quality & Anomalies", expanded=True):
        st.page_link("pages/7_Outliers and Anomalies.py", label="⚠️ Outliers & Anomalies")

    # --- Forecasting ---
    with st.sidebar.expander("Forecasting", expanded=True):
        st.page_link("pages/8_ Forecasting SARIMAX.py", label="📉 SARIMAX Forecasting")

    st.sidebar.write("---")
    st.sidebar.caption("Use the sidebar to navigate pages.")
    # ----------------------------------------------------------------


# -----------------------------
# MongoDB URI Helper
# -----------------------------
def get_credential(host):
    # Streamlit Cloud (formerly "share.streamlit.io") sets this environment variable.
    # It also relies on 'st.secrets' being available, which only happens in deployment.
    if host == "github": 
        # --- Streamlit Cloud deployment ---
        USR = st.secrets["mongo"]["username"]
        PWD = st.secrets["mongo"]["password"]
        
    else:
        # --- Local development (secrets not available) ---
        st.info("Connecting using local file (Local Environment).")
        c_file = 'No_sync/MongoDB.txt'
        try:
            # Note: This assumes the local file is present and formatted correctly
            with open(c_file, 'r') as f:
                USR, PWD = f.read().splitlines()
        except FileNotFoundError:
            st.error(f"Local credential file not found at: {c_file}")
            st.stop()
        except Exception as e:
            st.error(f"Error reading local credentials: {e}")
            st.stop()
            
    return USR, PWD

@st.cache_resource
def get_mongo_uri():
    # --- Connect to MongoDB ---
    #host = "local"
    host = "github"
    USR, PWD = get_credential(host)
    uri = f"mongodb+srv://{USR}:{PWD}@cluster0.wmoqhtp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    return uri

# -----------------------------
# MongoDB Client
# -----------------------------
@st.cache_resource
def get_mongo_client(uri):
    return MongoClient(uri)

# --- Normalize columns function
# -------------------------------
def normalize_columns(df):
    """Normalize columns for production and consumption datasets."""
    df.columns = [c.lower() for c in df.columns]

    rename_map = {
        "productiongroup": "energyGroup",
        "consumptiongroup": "energyGroup",
        "starttime": "startTime",
        "pricearea": "priceArea",
        "quantitykwh": "quantityKwh"
    }
    df = df.rename(columns=rename_map)
    return df

# -----------------------------
# Load Data from MongoDB
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data_from_mongo(db_name="indra", collection_name="production_per_group"):
    uri = get_mongo_uri()
    client = get_mongo_client(uri)
    db = client[db_name]
    data = list(db[collection_name].find())
    df = pd.DataFrame(data)
    if "startTime" in df.columns:
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    if "quantityKwh" in df.columns:
        df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")
    return df

# -----------------------------
# Load CSV
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data_from_csv(file_path="No_sync/P_Energy.csv"):
    df = pd.read_csv(file_path)
    if "startTime" in df.columns:
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    if "quantityKwh" in df.columns:
        df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")
    return df

@st.cache_data(show_spinner=False)
def get_weather_data(lat, lon, start_date, end_date):
    try:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": [
                "temperature_2m",
                "precipitation",
                "windspeed_10m",
                "wind_gusts_10m",
                "wind_direction_10m"
            ],
            "timezone": "Europe/Oslo"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["hourly"])
        df = df.rename(columns={
            'temperature_2m': 'temperature_2m (°C)',
            'windspeed_10m': 'wind_speed_10m (m/s)',
            'precipitation': 'precipitation (mm)',
            'wind_gusts_10m': 'wind_gusts_10m (m/s)',
            'wind_direction_10m': 'wind_direction_10m (°)'
        })
        df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M")
        return df
    
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return None
