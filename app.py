import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import datetime as dt
import streamlit as st

st.title("Project work, part 1 - Dashboard basics")
st.write("Streamlit app.")

df = pd.read_csv("open-meteo-subset.csv", encoding='UTF-8')
#df.head()

df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M")
df.head()


fig, ax = plt.subplots(figsize=(8,4))
ax.bar(df['time'].dt.month, df['precipitation (mm)'], color="skyblue", edgecolor="black")
ax.set_xlabel("Month")
ax.set_ylabel("Total Precipitation (mm)")
ax.set_title("Precipitation per Month")

st.pyplot

