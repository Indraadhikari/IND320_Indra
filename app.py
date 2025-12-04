import streamlit as st
import utils as ut
from pymongo.mongo_client import MongoClient


# Apply custom CSS and show sidebar
ut.apply_styles()
ut.show_sidebar()

# Streamlit page configuration
st.set_page_config(
    page_title="Data to Decision Project Work",
    page_icon="💡",
    layout="wide"
)

st.title("Data to Decision with Energy and Weathers Data")
st.write("""
Welcome to the Project - Data to Decision with Energy and Weathers Data´s dashboard. Use this page to quickly navigate to any part of the application. Below is an overview of all available analysis modules.
""")

st.subheader("📌 Project Overview")

col1, col2, col3 = st.columns([3,4,3])
with col1:
    st.markdown("### **Dashboard Basics**")

    if st.button("🏠 Home"):
        st.switch_page("app.py")

    if st.button("📊 Tables"):
        st.switch_page("pages/5_Table.py")

    if st.button("📈 Plots"):
        st.switch_page("pages/6_Plot.py")


# -----------------------------
# PART 2 — DATA SOURCES
# -----------------------------
with col2:
    st.markdown("### **Data Sources and Quality**")

    if st.button("⚡ Energy Production/Consumption"):
        st.switch_page("pages/4_Energy Production.py")

    if st.button("🔦 STL & Spectrogram"):
        st.switch_page("pages/5_STL and Spectrogram.py")

    if st.button("⚠️ Outliers & Anomalies"):
        st.switch_page("pages/7_Outliers and Anomalies.py")


# -----------------------------
# PART 4 — ADVANCED ANALYSIS
# -----------------------------
with col3:
    st.markdown("### **Advanced Analysis**")

    if st.button("🗺️ Map Overview"):
        st.switch_page("pages/1_Map_And_Selector.py")

    if st.button("❄️ Snow Drift Analysis"):
        st.switch_page("pages/2_Snow_drift.py")

    if st.button("🛰️ Sliding Window Correlation"):
        st.switch_page("pages/3_Sliding_Window_Correlation.py")

    if st.button("📉 SARIMAX Forecasting"):
        st.switch_page("pages/8_ Forecasting SARIMAX.py")
# DATA PRELOADING
df = st.session_state.get("df")

if df is None:
    with st.spinner("Fetching data..."):
        #production_df = ut.load_data_from_mongo(db_name="indra", collection_name="production_per_group")
        #df = ut.load_data_from_csv(file_path="No_sync/P_Energy.csv")
        st.info("Before explore the others page, please load the data and select a price area from Map Page.")
  
        if st.button("🗺️Load data from Map Page", type="primary"):
            st.switch_page("pages/1_Map_And_Selector.py") 
        st.stop()

selected_area = st.session_state.get('selected_area', None)


if selected_area is None:
    st.info("You should select a price area in Map page to see the results in different pages.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()
st.caption("💡 **Tip:** The sidebar provides an even faster way to navigate the app.")
