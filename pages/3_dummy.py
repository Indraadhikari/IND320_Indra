import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

st.title("Energy Production Dashboard (MongoDB)")

# --- Connect to MongoDB ---
USR = st.secrets["mongo"]["username"]
PWD = st.secrets["mongo"]["password"]

uri = f"mongodb+srv://{USR}:{PWD}@cluster0.wmoqhtp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["indra"]

st.success("✅ Successfully connected to MongoDB Atlas!")

# --- Load data from collection ---
data_cursor = db["production_per_group"].find()
data = list(data_cursor)

if len(data) == 0:
    st.warning("No data found in MongoDB collection!")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(data)

# Ensure startTime is datetime
df["startTime"] = pd.to_datetime(df["startTime"])

# --- Streamlit layout ---
col1, col2 = st.columns(2)

# --- LEFT COLUMN: Pie Chart by Price Area ---
with col1:
    st.header("Select Price Area for Pie Chart")
    
    price_areas = df["priceArea"].unique()
    selected_area = st.radio("Price Area:", price_areas)
    
    pie_df = df[df["priceArea"] == selected_area].groupby("productionGroup")["quantityKwh"].sum().reset_index()
    
    pie_fig = px.pie(
        pie_df,
        values="quantityKwh",
        names="productionGroup",
        title=f"Energy Production by Group in {selected_area}"
    )
    st.plotly_chart(pie_fig, use_container_width=True)

# --- RIGHT COLUMN: Line Chart for Month and Production Groups ---
with col2:
    st.header("Select Production Groups and Month for Line Chart")
    
    all_groups = df["productionGroup"].unique()
    selected_groups = st.multiselect("Production Groups:", all_groups, default=list(all_groups))
    
    month = st.selectbox(
        "Select Month:", 
        list(range(1, 13)), 
        format_func=lambda x: pd.Timestamp(2021, x, 1).strftime("%B")
    )
    
    line_df = df[
        (df["productionGroup"].isin(selected_groups)) &
        (df["startTime"].dt.month == month) &
        (df["priceArea"] == selected_area)
    ]
    
    if not line_df.empty:
        pivot_df = line_df.pivot_table(
            index="startTime",
            columns="productionGroup",
            values="quantityKwh",
            aggfunc="sum",
            fill_value=0
        ).reset_index()
        
        line_long = pivot_df.melt(id_vars="startTime", var_name="productionGroup", value_name="quantityKwh")
        
        line_fig = px.line(
            line_long,
            x="startTime",
            y="quantityKwh",
            color="productionGroup",
            title=f"Energy Production in {selected_area} for {pd.Timestamp(2021, month, 1).strftime('%B')}"
        )
        st.plotly_chart(line_fig, use_container_width=True)
    else:
        st.info("No data available for the selected combination.")

# --- Expander: Data Source ---
with st.expander("Data Source & Notes"):
    st.write("""
    The data shown here is sourced from the MongoDB collection `production_per_group` in database `indra`. 
    It contains hourly energy production by production group (hydro, wind, thermal, etc.) and price area. 
    The pie chart shows total production for the selected price area, while the line chart shows time series data for the selected month and production groups.
    """)