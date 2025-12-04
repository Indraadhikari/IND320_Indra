# --------------------------------------------------------------------
# Streamlit Page : Forecasting of Energy Production and Consumption
# --------------------------------------------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
warnings.filterwarnings("ignore")
import utils as ut 

ut.apply_styles()
ut.show_sidebar()

# --------------------------------------------------------------------
# Page Config
# --------------------------------------------------------------------
st.set_page_config(page_title="Energy Forecasting (SARIMAX)", layout="wide")
st.title("Forecasting of Energy Production and Consumption")

# --------------------------------------------------------------------
# Load Data
# --------------------------------------------------------------------
energy_df = st.session_state.get("df", pd.DataFrame())

#meteo_df = st.session_state.get("df_2021", pd.DataFrame())
selected_area = st.session_state.get("selected_area", None)
selected_coords = st.session_state.get("selected_coords", None)
selected_data_type = st.session_state.get("selected_data_type", None)

if selected_area:
    st.write(f"Working with Price Area: {selected_area}")
    selected_area = selected_area.replace(" ", "")
    # Use it for filtering, analysis, etc.
if selected_area is None or selected_coords is None:
    st.warning("No price area selected. Please select one from the Map page.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()

# Filter for selected area if available
if selected_area is not None:
    energy_df = energy_df[energy_df["priceArea"] == selected_area]
    if energy_df.empty:
        st.warning(f"No data found for selected area: {selected_area}")
        st.stop()

# --------------------------------------------------------------------
# User Controls
# --------------------------------------------------------------------
group = st.selectbox("Select energy group", energy_df["energyGroup"].unique().tolist())
value_col = st.selectbox("Select quantity to forecast", ["quantityKwh"])

energy_df["startTime"] = pd.to_datetime(energy_df["startTime"], utc=True)
min_date = energy_df["startTime"].min().date()
max_date = energy_df["startTime"].max().date()

one_year_later = min_date + pd.Timedelta(days=365)

default_end = min(one_year_later, max_date)

start_date, end_date = st.slider(
    "Select training period",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, default_end),
    format="YYYY-MM-DD"
)

forecast_horizon = st.number_input(
    "Forecast horizon (hours)", min_value=24, max_value=720, value=168, step=24
)

lat, lon = selected_coords
meteo_df = ut.get_weather_data(lat, lon, start_date, end_date)

# SARIMAX parameters
st.markdown("### Model hyperparameters (SARIMAX)")
col1, col2, col3 = st.columns(3)
p = col1.number_input("p", 0, 5, 1)
d = col1.number_input("d", 0, 2, 1)
q = col1.number_input("q", 0, 5, 1)
P = col2.number_input("P", 0, 5, 1)
D = col2.number_input("D", 0, 2, 0)
Q = col2.number_input("Q", 0, 5, 0)
s = col3.number_input("Seasonal period (s)", 0, 8760, 24)

# Optional exogenous variables
st.markdown("### Optional exogenous variables (from meteorological data)")
if not meteo_df.empty:
    possible_exog = [c for c in meteo_df.columns if c not in ["time", "date", "datetime"]]
    exog_vars = st.multiselect("Select external meteorological variables", possible_exog)
else:
    exog_vars = []

# --------------------------------------------------------------------
# Data Preparation
# --------------------------------------------------------------------
df = energy_df[energy_df["energyGroup"]==group].copy()
df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
df = df[(df['startTime'] >= pd.Timestamp(start_date).tz_localize('UTC')) &
        (df['startTime'] <= pd.Timestamp(end_date).tz_localize('UTC'))]

if df.empty:
    st.warning("No data within selected training dates.")
    st.stop()

# --- Prepare y
y = df[["startTime", value_col]].groupby("startTime").mean().sort_index()
y.index = pd.to_datetime(y.index, utc=True)
y = y[~y.index.duplicated(keep="first")]
y = y.asfreq("H")
y[value_col] = y[value_col].replace([np.inf, -np.inf], np.nan).interpolate(method="time").fillna(method="ffill").fillna(method="bfill")
y = y[value_col].astype(float)

# --- Prepare X_train
X_train = None
if exog_vars and not meteo_df.empty:
    meteo_df["time"] = pd.to_datetime(meteo_df["time"], utc=True)
    X_full = meteo_df.groupby("time")[exog_vars].mean().astype(float).sort_index()
    X_full.index = pd.to_datetime(X_full.index, utc=True)
    X_full = X_full[~X_full.index.duplicated(keep="first")]
    
    X_train = X_full.reindex(y.index).replace([np.inf,-np.inf], np.nan).fillna(method="ffill").fillna(method="bfill")
    
    df_comb = pd.concat([y, X_train], axis=1).dropna()
    y = df_comb[value_col]
    X_train = df_comb[exog_vars].astype(float)

# --------------------------------------------------------------------
# Fit SARIMAX Model
# --------------------------------------------------------------------
if st.button("Run Forecast", type="primary"):

    @st.cache_resource(show_spinner=False)
    def fit_sarimax_model(y, X_train, order, seasonal_order):
        model = SARIMAX(y, order=order, seasonal_order=seasonal_order,
                        exog=X_train, enforce_stationarity=False, enforce_invertibility=False)
        return model.fit(disp=False, maxiter=200, method="lbfgs")

    with st.spinner("Training SARIMAX model... ⏳"):
        seasonal_order = (P,D,Q,s) if s>0 else (0,0,0,0)
        results = fit_sarimax_model(y, X_train, (p,d,q), seasonal_order)

    st.success("Model trained successfully ✅")

    # --- Forecast
    idx_forecast = pd.date_range(y.index[-1]+pd.Timedelta(hours=1), periods=forecast_horizon, freq="H", tz="UTC")
    if X_train is not None:
        last_exog = X_train.iloc[-1:]
        X_future = pd.concat([last_exog]*forecast_horizon)
        X_future.index = idx_forecast
    else:
        X_future = None

    with st.spinner("Generating forecast... ⏳"):
        pred_res = results.get_forecast(steps=forecast_horizon, exog=X_future)
        y_pred = pred_res.predicted_mean
        conf_int = pred_res.conf_int()

    # --- Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=y.index, y=y, mode="lines", name="Observed", line=dict(color="royalblue")))
    fig.add_trace(go.Scatter(x=y_pred.index, y=y_pred, mode="lines", name="Forecast", line=dict(color="orange")))
    fig.add_trace(go.Scatter(
        x=list(conf_int.index)+list(conf_int.index[::-1]),
        y=list(conf_int.iloc[:,0])+list(conf_int.iloc[:,1][::-1]),
        fill="toself", fillcolor="rgba(255,165,0,0.25)",
        line=dict(color="rgba(255,255,255,0)"), hoverinfo="skip", showlegend=True, name="95% CI"
    ))
    fig.update_layout(title=f"SARIMAX Forecast for {group} ({value_col})", template="plotly_white",
                      xaxis_title="Time", yaxis_title="Energy Production/Consumption (kWh)", height=600)
    st.plotly_chart(fig, use_container_width=True)

    # --- Metrics
    st.subheader("Model Summary (shortened)")
    st.text(results.summary().as_text()[:800])
    st.subheader("Training Fit Metrics")
    st.write(f"**AIC:** {results.aic:.2f}")
    st.write(f"**BIC:** {results.bic:.2f}")
