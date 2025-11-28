import streamlit as st
from pymongo import MongoClient
import pandas as pd

st.set_page_config(
    page_title="IND320 Project work - Part 1 and Part 2",
    page_icon="📶",
    layout="wide"
)

st.sidebar.title("Navigation")
st.sidebar.write("Use the sidebar to navigate pages")

st.title("IND320 Project Work")
st.write("""
         * **Project work, Part 1 - Dashboard Basics**
            * Page 1 → Home (Current page)
            * Page 4 → Table 
            * Page 5 → Plot
            * Page 2 → Dummy page (Now changed to Energy Production for Part 2)
        """)

st.write("""
         * **Project work, Part 2 - Data Sources**
            * Page 2 → Energy Production
         """)

st.write("""
         * **Project work, Part 3 - Data Quality**
            * Page 3 → STL and Spectrogram
            * Page 5 → Outliers and Anomalies
         """)

st.write("""
         * **Project work, Part 4 - Streamlit App, New Elements**
            * Map Overview → Interactive GeoJSON map with Price Areas NO1-NO5
                * Choropleth visualization with energy production data
                * Clickable areas with coordinate selection
                * Mean values calculation by time interval and energy group
            * Snow Drift Analysis → Calculate and visualize snow drift (Tabler 2003)
                * Year-by-year calculations (July 1 to June 30)
                * Wind rose diagrams showing directional distribution
                * Uses coordinates selected from map
            * Correlation Analysis → Sliding window correlation with lag
                * Meteorology vs Energy production/consumption
                * Selectable window length and lag parameters
                * Extreme weather event detection and analysis
            * Forecasting → SARIMAX time series forecasting
                * Dynamic forecasting with confidence intervals
                * Selectable SARIMAX parameters (p,d,q)(P,D,Q,s)
                * Optional exogenous variables (weather data)
                * Training data selection and forecast horizon control
         """)
st.caption("**Navigate using the sidebar to view tables, plots, or more content.**")


# --- Connect to MongoDB ---
USR = st.secrets["mongo"]["username"]
PWD = st.secrets["mongo"]["password"]

#c_file = '/Users/indra/Documents/Masters in Data Science/Data to Decision/IND320_Indra/No_sync/MongoDB.txt' #creadential file
#USR, PWD = open(c_file).read().splitlines()

uri = f"mongodb+srv://{USR}:{PWD}@cluster0.wmoqhtp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


@st.cache_resource
def get_client():
    return MongoClient(uri)


client = get_client()
db = client["indra"]


@st.cache_data(show_spinner=False)
def load_data():
    data_cursor = db["production_per_group"].find()
    data = list(data_cursor)
    df = pd.DataFrame(data)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")
    if len(df) == 0:
        st.warning("No data found in MongoDB collection!")
        st.stop()
    return df


#-------- Start: For Local test to prevent many request to MongoDB in testing --------- 
@st.cache_data(show_spinner=False)
def load_data_file():
        df = pd.read_csv("No_sync/P_Energy.csv")
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
        df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")

        return df
#------------ End ---------------


with st.spinner("Fetching data..."):
    #df = load_data()
    df = load_data()
      
df_one_year = df[df['startTime'].dt.year == 2021]

st.session_state["df"] = df_one_year