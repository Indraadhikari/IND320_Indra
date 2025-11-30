import pandas as pd
import datetime as dt
import streamlit as st
import plotly.express as px
import utils as ut 

ut.apply_styles()
ut.show_sidebar()

st.title("Interactive line plot for different weathers variable over time.")

city = st.session_state.get("city", "Oslo")
selected_coords = st.session_state.get("selected_coords", None)  # expects tuple/list: (lat, lon)

if city is None or selected_coords is None:
    st.warning("No price area selected. Please select one from the Map page.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()


year = st.selectbox(
    "Select Year",
    options=range(1940, 2025), # Range from 1940 up to (but not including) 2025
    index=2021 - 1940 # Sets 2021 as the default index
)

lat, lon = selected_coords
# Convert the integer year into the required date strings
with st.spinner("Fetching data..."):
    df_2021 = ut.get_weather_data(lat, lon, f"{year}-01-01", f"{year}-12-31")

st.caption(f"Info: These dataset cover open-meteo weathers data for {city} for year {year}.")

df_2021["time"] = pd.to_datetime(df_2021["time"], format="%Y-%m-%dT%H:%M")  # converting datetime format

columns = df_2021.columns.tolist()
columns.remove('time')  # Remove 'time' from selectable options
select_options = columns + ['All Columns']
selected_column = st.selectbox("Choose data column to plot:", select_options, 
                               index=select_options.index('All Columns')
                               ) # default option 'All Columns'

s_month = st.slider(
    "Select month range:",
    min_value = 1,
    max_value = 12,
    value=(1, 2)
)

start_month, end_month = s_month

#month in words
def get_month_name(month_int):
    if 1 <= month_int <= 12:
        # Corrected line: Access the 'datetime' class inside the 'dt' module
        date_object = dt.datetime(2000, month_int, 1) 
        return date_object.strftime("%B")
    return "Invalid Month"

st.caption(f"Selected range: {get_month_name(start_month)} to {get_month_name(end_month)}")

try:
    filtered_df = df_2021[df_2021['time'].dt.month.between(start_month, end_month)]
except AttributeError as e:
    st.error(f"Error: {e}")

# ploting data with all columns if 'all cloumns' options selected
if selected_column == 'All Columns':
    df_long = filtered_df.melt(id_vars="time", var_name="variable", value_name="value") #st.write(df_long.tail())

    # Interactive multi-line plot
    fig2 = px.line(df_long, x="time", y="value", color="variable", title="Weather Data over Time", width=1000,height=500)

    st.plotly_chart(fig2, use_container_width=True)
# ploting line charts as a columns selected from dropbox option 
else:
    fig = px.line(filtered_df, x='time', y=selected_column, 
                  title=f"{selected_column.title()} Over Months",
                  labels={selected_column: selected_column.title(), 'month': 'Month'},
                  width=1000, height=500)
    fig.update_layout(yaxis_title=selected_column.title(), xaxis_title="Month")

    st.plotly_chart(fig, use_container_width=True)
