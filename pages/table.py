import pandas as pd
import streamlit as st

st.title('Tabular data from the CSV file.')

df = pd.read_csv("open-meteo-subset.csv", encoding='UTF-8')
#df.head()
df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M")
st.write(df.head())