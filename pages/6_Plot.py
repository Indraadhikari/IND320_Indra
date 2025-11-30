import pandas as pd
import datetime as dt
import streamlit as st
import plotly.express as px
import utils as ut 

ut.apply_styles()
ut.show_sidebar()

st.title("Interactive line plot for different weathers variable over time.")

city = st.session_state.get("city", "Oslo")

df_2021 = st.session_state.get("df_2021")

if city is None or df_2021 is None:
    st.warning("No price area selected. Please select one from the Map page.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()


st.caption(f"Info: These dataset cover open-meteo weathers data for {city} for year 2021.")

df_2021["time"] = pd.to_datetime(df_2021["time"], format="%Y-%m-%dT%H:%M")  # converting datetime format

columns = df_2021.columns.tolist()
columns.remove('time')  # Remove 'time' from selectable options
select_options = columns + ['All Columns']
selected_column = st.selectbox("Choose data column to plot:", select_options, 
                               index=select_options.index('All Columns')
                               ) # default option 'All Columns'

months = df_2021['time'].dt.month #st.write(months) #test
selected_month = st.select_slider(
    "Select month range:",
    options=months,
    value=months[0]  # Default to the first month
)

#get Month name under slider
date_object = dt.datetime(2000, selected_month, 1)
full_month_name = date_object.strftime("%B")
st.write(full_month_name)

#filtering df as month selected in the slider.
filtered_df = df_2021[df_2021['time'].dt.month==selected_month]

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
