import streamlit as st
from pymongo import MongoClient

# Retrieve secrets
USR = st.secrets["mongo"]["username"]
PWD = st.secrets["mongo"]["password"]

# Build connection string

uri = "mongodb+srv://"+USR+":"+PWD+"@cluster0.wmoqhtp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(uri)

st.success("Successfully connected to MongoDB Atlas!")

# Example: Read data from a collection

data = list(db["production_per_group"].find().limit(5))
st.write(data)
