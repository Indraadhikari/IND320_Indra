import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import streamlit as st
import numpy as np

st.title("Project work, part 1 - Dashboard basics")

df = pd.read_csv("open-meteo-subset.csv", encoding='UTF-8')

st.write("1. Wind Direction in the Compass-Style.")
fig, ax = plt.subplots(figsize=(8,4))

theta = np.radians(df['wind_direction_10m (°)'])
r = df['wind_speed_10m (m/s)']

ax = plt.subplot(111, polar=True)
ax.scatter(theta, r, s=5, c='b', alpha=0.7)

ax.set_theta_zero_location("N")   # 0° at North
ax.set_theta_direction(-1)        # clockwise
plt.title("Wind Direction (Compass-Style)", va='bottom')
plt.show()

st.pyplot(fig)

#-------- Precipitation per Month --------
st.write("2. Precipitation per Month")
fig1, ax = plt.subplots(figsize=(8,4))

df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M")
month = df['time'].dt.month
prec = df['precipitation (mm)']

ax.bar(month, prec)
ax.set_xlabel("Month")
ax.set_ylabel("Total Precipitation (mm)")
ax.set_title("Precipitation per Month")

st.pyplot(fig1)

#----------- Interactive with plotly ---------------
st.write("3. Interactive multi-line plot for different weathers variable over time.")

import plotly.express as px

df_long = df.melt(id_vars="time", var_name="variable", value_name="value")

# Interactive multi-line plot
fig2 = px.line(df_long, x="time", y="value", color="variable", title="Weather Data over Time")

##fig2.show()
st.plotly_chart(fig2, use_container_width=True)