import pandas as pd
import streamlit as st
import requests

st.title('Tabular data from the open-meteo API.')

# --------------------------------------------------------------------
# Get selected area and coordinates from session_state
# --------------------------------------------------------------------
selected_area = st.session_state.get("selected_area", None)
selected_coords = st.session_state.get("selected_coords", None)  # expects tuple/list: (lat, lon)
production_df = st.session_state.get("df", pd.DataFrame())

# Check if selections exist
if selected_area is None or selected_coords is None:
    st.warning("No price area or coordinates selected. Please select one from the Map page.")
    st.stop()

if production_df.empty:
    st.warning("No production dataset loaded.")
    st.stop()

lat, lon = selected_coords

# --------------------------------------------------------------------
# Area mapping (if needed)
# --------------------------------------------------------------------
area_mapping = {
    "NO1": {"city": "Oslo", "latitude": 59.9127, "longitude": 10.7461},
    "NO2": {"city": "Kristiansand", "latitude": 58.1467, "longitude": 7.9956},
    "NO3": {"city": "Trondheim", "latitude": 63.4305, "longitude": 10.3951},
    "NO4": {"city": "Tromsø", "latitude": 69.6489, "longitude": 18.9551},
    "NO5": {"city": "Bergen", "latitude": 60.393, "longitude": 5.3242},
}

area_key = selected_area.replace(" ", "")
if area_key in area_mapping:
    city = area_mapping[area_key]["city"]
else:
    city = "Unknown"

st.caption(f"Info: These dataset cover open-meteo weather data for {city} for year 2021.")

# --------------------------------------------------------------------
# Fetch weather data function
# --------------------------------------------------------------------
def get_weather_data(lat, lon, year):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
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

# --------------------------------------------------------------------
# Load weather data for 2021
# --------------------------------------------------------------------
df_2021 = get_weather_data(lat, lon, 2021)
st.write("1. Overview of the dataset.")
st.write(df_2021)

# --------------------------------------------------------------------
# Display summary with first month line chart preview
# --------------------------------------------------------------------
st.write("2. Weather Data Summary - First Month with Line Chart Previews")
first_month = df_2021[df_2021["time"].dt.month == df_2021["time"].dt.month.min()]

summary_data = {"Variable": [], "Preview": []}
for col in df_2021.columns:
    if col != "time":
        summary_data["Variable"].append(col)
        summary_data["Preview"].append(list(first_month[col].values))

summary_df = pd.DataFrame(summary_data)

st.dataframe(
    summary_df,
    column_config={
        "Variable": st.column_config.TextColumn("Variable Name"),
        "Preview": st.column_config.LineChartColumn(
            "First Month Trend",
            y_min=min([min(lst) for lst in summary_df["Preview"]]),  # auto scale
        )
    },
    hide_index=True
)

# --------------------------------------------------------------------
# Store in session_state
# --------------------------------------------------------------------
st.session_state["city"] = city
st.session_state["df_2021"] = df_2021
