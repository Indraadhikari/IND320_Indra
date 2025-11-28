import streamlit as st
import pandas as pd
import plotly.express as px
#from Home import load_data

st.title("Energy Production Dashboard (MongoDB)")


@st.cache_data(show_spinner=False)
def get_df():
    df = st.session_state.get("df", [])

    if len(df) == 0:
        with st.spinner("Fetching data..."):
            #df = load_data()
            #-------- Start: For Local test to prevent many request to MongoDB in testing ---------
            df = pd.read_csv("No_sync/P_Energy.csv")
            df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
            df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")
            #------------ End ---------------

            df = df[df['startTime'].dt.year == 2021]
    return df


with st.spinner("Fetching data..."):
    df = get_df()
# making startTime datetime
df["startTime"] = pd.to_datetime(df["startTime"], utc=True)

# making quantityKwh column numberic
df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")

# --- Streamlit layout ---
col1, col2 = st.columns(2)

# --- LEFT COLUMN: Pie Chart by Price Area ---
with col1:
    st.header("Select Price Area for Pie Chart")
    
    price_areas = sorted(df["priceArea"].unique())
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
    
    # Unique production groups
    all_groups = sorted(df["productionGroup"].unique())

    # Use st.pills instead of st.multiselect
    selected_groups = st.pills(
        "Select Production Groups:",
        options=all_groups,
        selection_mode="multi",
        default=all_groups
    )
    
    # Month selection
    month = st.selectbox(
        "Select Month:", 
        list(range(1, 13)), 
        format_func=lambda x: pd.Timestamp(2021, x, 1).strftime("%B")
    )
    
    # Filter the data
    line_df = df[
        (df["productionGroup"].isin(selected_groups)) &
        (df["startTime"].dt.month == month) &
        (df["priceArea"] == selected_area)
    ]
    
    # Create line plot
    if not line_df.empty:
        pivot_df = line_df.pivot_table(
            index="startTime",
            columns="productionGroup",
            values="quantityKwh",
            aggfunc="sum",
            fill_value=0
        ).reset_index()
        
        line_long = pivot_df.melt(
            id_vars="startTime", 
            var_name="productionGroup", 
            value_name="quantityKwh"
        )
        
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
    The original source of the data is Elhub API ('https://api.elhub.no/') - once extracted from the API, data is stored in MongoDB.
    It contains hourly energy production by production group (hydro, wind, thermal, solar, and others) and price area. 
    The pie chart shows total production for the selected price area, while the line chart shows time series data for the selected month and production groups.
    """)

# Store in session state for other pages
#st.session_state["selected_area"] = selected_area
st.session_state["selected_year"] = 2021  # fixed year
# st.session_state["df"] = df_one_year