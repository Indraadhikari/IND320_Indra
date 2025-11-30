import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import utils as ut

ut.apply_styles()
ut.show_sidebar()

st.set_page_config(page_title="Meteorology ↔ Energy Correlation", page_icon='🆚', layout="wide")
st.title("Meteorology and Energy Production  - Sliding Window Correlation")

# Load data from session_state
meteo_df = st.session_state.get("df_2021", pd.DataFrame())
energy_df = st.session_state.get("df", pd.DataFrame())

if meteo_df.empty or energy_df.empty:
    st.warning("Please go to the Map page and select a location by clicking on a price area.")
  
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py") 
    st.stop()

# Helper: sliding‑window correlation
def sliding_window_corr(x: pd.Series, y: pd.Series, window: int = 24, lag: int = 0) -> pd.Series:
    """Compute rolling correlation between two equal‑length Series with lag."""
    x_shifted = x.shift(lag)
    return x_shifted.rolling(window).corr(y)

# User controls
meteo_cols = [c for c in meteo_df.columns if c not in ["time", "date", "datetime"]]
meteo_var = st.selectbox("Select meteorological variable", meteo_cols, index=0)

energy_groups = energy_df["productionGroup"].unique().tolist()
energy_group = st.selectbox("Select energy production/consumption group", energy_groups, index=0)

lag = st.slider("Lag (hours)", -72, 72, 0, step=3)
window = st.slider("Window length (hours)", 12, 240, 72, step=12)

# Prepare aligned data  (fixed duplicates + timezones)

# ---- ENERGY ----
ts_energy = (
    energy_df[energy_df["productionGroup"] == energy_group]
    .groupby("startTime", as_index=True)["quantityKwh"]
    .mean()                                   # aggregate -> unique timestamp
    .sort_index()
)
ts_energy.index = pd.to_datetime(ts_energy.index, utc=True)
ts_energy = ts_energy[~ts_energy.index.duplicated(keep="first")]

# ---- METEOROLOGY ----
ts_meteo = (
    meteo_df.groupby("time", as_index=True)[meteo_var]
    .mean()                                   # aggregate -> unique timestamp
    .astype(float)
    .sort_index()
)
ts_meteo.index = pd.to_datetime(ts_meteo.index, utc=True)
ts_meteo = ts_meteo[~ts_meteo.index.duplicated(keep="first")]

# ---- JOIN ----
joined = pd.concat(
    [ts_meteo.rename("meteo"), ts_energy.rename("energy")],
    axis=1
).dropna()

if joined.empty:
    st.warning("No overlapping timestamps found after alignment.")
    st.stop()

# Compute rolling correlation
corr_series = sliding_window_corr(joined["meteo"], joined["energy"], window, lag)
corr_series.name = "corr"

# Plotly visualization
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=corr_series.index,
    y=corr_series,
    mode="lines",
    line=dict(color="purple"),
    name=f"Corr({meteo_var}, {energy_group})",
))

fig.add_hline(y=0, line=dict(color="gray", dash="dash"), name="Zero line")

fig.update_layout(
    title=f"Sliding Window Correlation — lag = {lag} h, window = {window} h",
    xaxis_title="Time",
    yaxis_title="Correlation Coefficient",
    yaxis=dict(range=[-1, 1]),
    template="plotly_white",
    height=500,
)

st.plotly_chart(fig, use_container_width=True)

# Summary statistics
st.subheader("Correlation Summary Statistics")
st.write(f"**Mean correlation:** {corr_series.mean():.3f}")
st.write(f"**Maximum correlation:** {corr_series.max():.3f}")
st.write(f"**Minimum correlation:** {corr_series.min():.3f}")