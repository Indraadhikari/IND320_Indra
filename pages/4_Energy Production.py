import streamlit as st
import pandas as pd
import plotly.express as px
import utils as ut

ut.apply_styles()
ut.show_sidebar()

st.title("Energy Production Dashboard (MongoDB)")

selected_area = st.session_state.get('selected_area', None)

if selected_area:
    st.write(f"Working with Price Area: {selected_area}")
    selected_area = selected_area.replace(" ", "")

if selected_area is None:
    st.warning("No price area selected. Please select one from the Map page.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()


@st.cache_data(show_spinner=False)
def get_df():
    df = st.session_state.get("df", [])

    if len(df) == 0:
        df = ut.load_data_from_csv(file_path="No_sync/P_Energy.csv")
        st.session_state["df"] = df
    return df


# ---------------- LOAD DATA ----------------
with st.spinner("Fetching data..."):
    df = get_df()
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")

# ---------------- YEAR SELECTION ----------------
# Auto-detect available years
available_years = sorted(df["startTime"].dt.year.unique())

selected_year = st.selectbox("Select Year:", available_years)

# Filter for selected year (instead of fixed 2021)
df = df[df["startTime"].dt.year == selected_year]


# ---------------- CLEAN AGAIN (unchanged logic) ----------------
df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
df["quantityKwh"] = pd.to_numeric(df["quantityKwh"], errors="coerce")


# -------------- LAYOUT: TWO COLUMNS ----------------
col1, col2 = st.columns(2)

# --------- PIE CHART ---------
with col1:
    st.header(f"Pie Chart for Price Area {selected_area}")
    st.write("\n")

    pie_df = (
        df[df["priceArea"] == selected_area]
        .groupby("productionGroup")["quantityKwh"]
        .sum()
        .reset_index()
    )

    pie_fig = px.pie(
        pie_df,
        values="quantityKwh",
        names="productionGroup",
        title=f"Energy Production by Group in {selected_area} ({selected_year})"
    )
    
    pie_fig.update_layout(margin=dict(t=200, b=0, l=0, r=0))  # Adjust 't' (top margin) to your desired value (e.g., 80)

    st.plotly_chart(pie_fig, use_container_width=True)


# --------- LINE CHART ---------
with col2:
    st.header("Select Production Groups and Month for Line Chart")

    # Unique production groups
    all_groups = sorted(df["productionGroup"].unique())

    # Pills for groups
    selected_groups = st.pills(
        "Select Production Groups:",
        options=all_groups,
        selection_mode="multi",
        default=all_groups
    )

    # Month selector
    month = st.selectbox(
        "Select Month:",
        list(range(1, 12 + 1)),
        format_func=lambda x: pd.Timestamp(selected_year, x, 1).strftime("%B")
    )

    # Filter for line chart
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
            title=f"Energy Production in {selected_area} for {pd.Timestamp(selected_year, month, 1).strftime('%B')} {selected_year}"
        )

        st.plotly_chart(line_fig, use_container_width=True)
    else:
        st.info("No data available for the selected combination.")


# --------- EXPANDER ---------
with st.expander("Data Source & Notes"):
    st.write("""
    The data shown here is sourced from the MongoDB collection `production_per_group` in database `indra`. 
    The original source of the data is Elhub API ('https://api.elhub.no/') - once extracted from the API, data is stored in MongoDB.
    It contains hourly energy production by production group (hydro, wind, thermal, solar, and others) and price area. 
    The pie chart shows total production for the selected price area, while the line chart shows time series data for the selected month and production groups.
    """)
