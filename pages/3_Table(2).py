import pandas as pd
import streamlit as st
import requests

st.title('Tabular data from the open-meteo API.')

area = st.session_state.get("selected_area")

if area is None:
    st.warning("Please go back to page 'Energy Production' and select a price area first.")
    st.stop()

data = {
    "priceArea": ["NO1", "NO2", "NO3", "NO4", "NO5"],
    "city": ["Oslo", "Kristiansand", "Trondheim", "Tromsø", "Bergen"],
    "latitude": [59.9127, 58.1467, 63.4305, 69.6489, 60.393],
    "longitude": [10.7461, 7.9956, 10.3951, 18.9551, 5.3242]
}

idx = data["priceArea"].index(area)

# Extract matching values
city = data["city"][idx]
lat = data["latitude"][idx]
lon = data["longitude"][idx]

st.caption(f"Info: These dataset cover open-meteo weathers data for {city} for year 2021.")


def get_weather_data(lat, lon, year):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "hourly": ["temperature_2m", "precipitation", "windspeed_10m", "wind_gusts_10m", "wind_direction_10m"],  # example variables
        "timezone": "Europe/Oslo"
    }
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data["hourly"])
    df = df.rename(columns={'temperature_2m': 'temperature_2m (°C)', 'windspeed_10m': 'wind_speed_10m (m/s)', 
                             'precipitation': 'precipitation (mm)','wind_gusts_10m': 'wind_gusts_10m (m/s)', 
                             'wind_direction_10m': 'wind_direction_10m (°)'})
    return df


df_2021 = get_weather_data(lat, lon, 2021)

#df = pd.read_csv("open-meteo-subset.csv", encoding='UTF-8')
# df.head()
df_2021["time"] = pd.to_datetime(df_2021["time"], format="%Y-%m-%dT%H:%M")
st.write("1. Overview of the dataset.")
st.write(df_2021)

st.write("2. Weather Data Summary - First Month with Line Chart Previews")

# the row-wise LineChartColumn() to display the first month of the data series
first_month = df_2021[df_2021["time"].dt.month == df_2021["time"].dt.month.min()]

# DataFrame where: - Each row = a variable (column), - A small timeseries goes in the "chart" column
summary_data = {
    "Variable": [],
    "Preview": []
}

for col in df_2021.columns:
    if col != "time":  # skiping the time column
        summary_data["Variable"].append(col)
        summary_data["Preview"].append(list(first_month[col].values))

summary_df = pd.DataFrame(summary_data)

# Display interactive table with line charts
st.dataframe(
    summary_df,
    column_config={
        "Variable": st.column_config.TextColumn("Variable Name"),
        "Preview": st.column_config.LineChartColumn(
            "First Month Trend",
            y_min=min(summary_df["Preview"][0]),  # auto scale
        )
    },
    hide_index=True
)

st.session_state["city"] = city
st.session_state["df_2021"] = df_2021