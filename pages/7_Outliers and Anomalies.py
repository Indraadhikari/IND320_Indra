import streamlit as st
import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from scipy.fftpack import dct, idct
import plotly.graph_objects as go
import utils as ut 

ut.apply_styles()
ut.show_sidebar()

st.title("Outlier/SPC and Anomaly/LOF analysis")

selected_area = st.session_state.get('selected_area', None)
selected_coords = st.session_state.get("selected_coords", None)

if selected_area is None or selected_coords is None:
    st.warning("No price area selected. Please select one from the Map page.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()

lat, lon = selected_coords

year = st.selectbox(
    "Select Year",
    options=range(1940, 2025),
    index=2021 - 1940
)

with st.spinner("Fetching data..."):
    df_2021 = ut.get_weather_data(lat, lon, f"{year}-01-01", f"{year}-01-31")

area_mapping = {
    "NO1": {"city": "Oslo"},
    "NO2": {"city": "Kristiansand"},
    "NO3": {"city": "Trondheim"},
    "NO4": {"city": "Tromsø"},
    "NO5": {"city": "Bergen"},
}

area_key = selected_area.replace(" ", "")
city = area_mapping.get(area_key, {}).get("city", "Unknown")

st.caption(f"Info: These dataset cover open-meteo weathers data for {city} for year {year}.")


# =====================================================
#        REPLACEMENT 1 — SPC Plot Using Plotly
# =====================================================
def analyze_temperature_outliers(
    df_2021,
    time_col='time',
    temp_col='temperature_2m (°C)',
    freq_cutoff=10,
    k=3
):
    data = df_2021.copy()
    data[time_col] = pd.to_datetime(data[time_col])
    data = data.sort_values(time_col).reset_index(drop=True)

    temps = data[temp_col].astype(float).values

    # ---- DCT high-pass filter ----
    coeff = dct(temps, norm='ortho')
    highpass = np.copy(coeff)
    highpass[:freq_cutoff] = 0.0
    satv = idct(highpass, norm='ortho')

    median_satv = np.median(satv)
    mad_satv = np.median(np.abs(satv - median_satv))
    robust_sigma = 1.4826 * mad_satv
    upper = median_satv + k * robust_sigma
    lower = median_satv - k * robust_sigma

    outlier_mask = (satv > upper) | (satv < lower)
    outliers_df = data.loc[outlier_mask].copy()
    outliers_df['SATV'] = satv[outlier_mask]

    # ---- Convert to temperature space ----
    temp_trend = temps - satv
    upper_curve = temp_trend + upper
    lower_curve = temp_trend + lower

    # =====================================================
    #              PLOTLY VERSION OF THE FIGURE
    # =====================================================
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data[time_col], y=temps,
        mode="lines",
        name="Temperature",
        line=dict(color="orange")
    ))

    fig.add_trace(go.Scatter(
        x=data[time_col], y=upper_curve,
        mode="lines",
        name="Upper SPC Limit",
        line=dict(color="gray", dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=data[time_col], y=lower_curve,
        mode="lines",
        name="Lower SPC Limit",
        line=dict(color="gray", dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=data.loc[outlier_mask, time_col],
        y=temps[outlier_mask],
        mode="markers",
        name="Outliers",
        marker=dict(color="red", size=8)
    ))

    fig.update_layout(
        title="Temperature Outliers via DCT High-pass Filtering & Robust SPC",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        template="plotly_white",
        height=500
    )

    stats = {
        'n_points': len(data),
        'n_outliers': int(outlier_mask.sum()),
        'proportion_outliers': float(outlier_mask.sum()) / len(data),
        'median_SATV': float(median_satv),
        'MAD_SATV': float(mad_satv),
        'robust_sigma': float(robust_sigma),
        'upper_limit_SATV': float(upper),
        'lower_limit_SATV': float(lower)
    }

    return outliers_df, stats, fig


# =====================================================
#       REPLACEMENT 2 — LOF Plot Using Plotly
# =====================================================
def analyze_precipitation_anomalies(
    df_2021,
    time_col="time",
    precip_col="precipitation (mm)",
    proportion=0.01
):
    df = df_2021.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values(time_col).reset_index(drop=True)

    precip = df[precip_col].fillna(0).values.reshape(-1, 1)

    lof = LocalOutlierFactor(contamination=proportion)
    labels = lof.fit_predict(precip)
    mask = labels == -1

    outlier_df = df[mask].copy()
    outlier_df["LOF_Score"] = lof.negative_outlier_factor_[mask]

    # =====================================================
    #               PLOTLY VERSION OF THE FIGURE
    # =====================================================
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[time_col], y=df[precip_col],
        mode="lines",
        name="Precipitation",
        line=dict(color="blue")
    ))

    fig.add_trace(go.Scatter(
        x=df.loc[mask, time_col],
        y=df.loc[mask, precip_col],
        mode="markers",
        name="Anomalies (LOF)",
        marker=dict(color="red", size=8)
    ))

    fig.update_layout(
        title="Precipitation Anomalies via Local Outlier Factor",
        xaxis_title="Time",
        yaxis_title="Precipitation (mm)",
        template="plotly_white",
        height=500
    )

    stats = {
        "n_points": len(df),
        "n_anomalies": len(outlier_df),
        "proportion_anomalies": round(len(outlier_df) / len(df), 4),
        "mean_precipitation": df[precip_col].mean(),
        "mean_anomalies": outlier_df[precip_col].mean() if len(outlier_df) > 0 else None,
    }

    return outlier_df, stats, fig


# =====================================================
#                 TABS + DISPLAY
# =====================================================
tab1, tab2 = st.tabs(["Temperature Outliers (SPC)", "Precipitation Anomalies (LOF)"])

with tab1:
    st.subheader("SPC Outlier Analysis (Temperature)")
    cutoff = st.slider("DCT frequency cutoff", 5, 50, 10)
    k = st.slider("MAD multiplier (k)", 1, 5, 3)

    outliers, stats, fig = analyze_temperature_outliers(df_2021, freq_cutoff=cutoff, k=k)
    st.plotly_chart(fig, use_container_width=True)
    st.write("Summary:", stats)

with tab2:
    st.subheader("Local Outlier Factor (Precipitation)")
    prop = st.slider("Proportion of anomalies", 0.001, 0.05, 0.01)

    anomalies, stats, fig = analyze_precipitation_anomalies(df_2021, proportion=prop)
    st.plotly_chart(fig, use_container_width=True)
    st.write("Summary:", stats)
