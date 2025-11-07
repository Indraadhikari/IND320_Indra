import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import streamlit as st
import plotly.express as px

st.title("Interactive line plot for different weathers variable over time.")

df = pd.read_csv("open-meteo-subset.csv", encoding='UTF-8')

df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M") #converting datetime format

columns = df.columns.tolist()
columns.remove('time')  # Remove 'time' from selectable options
select_options = columns + ['All Columns']
selected_column = st.selectbox("Choose data column to plot:", select_options, 
                               index=select_options.index('All Columns')
                               ) # default option 'All Columns'

months = df['time'].dt.month #st.write(months) #test
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
filtered_df = df[df['time'].dt.month==selected_month]

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
