import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import spectrogram
from statsmodels.tsa.seasonal import STL
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.title("STL analysis and Spectrogram")

# Try to get the selected area and year

area = st.session_state.get('selected_area', None)
production_df = st.session_state.get("df", [])

if area:
    st.write(f"Working with Price Area: {area}")
    # Use it for filtering, analysis, etc.
if area is None or len(production_df) == 0:
    st.warning("No price area selected. Please select one from the Map page.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/6_Map_And_Selector.py")
    st.stop()

st.caption("Info: The analysing datase is the energy production by production data.")

area = area.replace(" ", "")


# Function for spectrogram
@st.cache_data(show_spinner=False)
def production_spectrogram(
    production_df,
    area='NO1',     # price area (city proxy)
    group='hydro',  # production group
    time_col='startTime',
    value_col='quantityKwh',
    window_length=256,
    overlap=128
):
    """
    Create an interactive Plotly spectrogram based on production data
    for a given price area and production group.

    Returns
    -------
    f : np.ndarray      Array of sample frequencies
    t : np.ndarray      Array of segment times
    Sxx : np.ndarray    Spectrogram intensity matrix
    fig : plotly.graph_objects.Figure (interactive figure)
    """

    # --- Filter area and group ---
    sub = production_df[
        (production_df['priceArea'] == area) &
        (production_df['productionGroup'].str.lower() == group.lower())
    ].copy()

    if sub.empty:
        raise ValueError(f"No data found for area '{area}' and group '{group}'.")

    # --- Sort & clean signal ---
    sub = sub.sort_values(time_col)
    sub[time_col] = pd.to_datetime(sub[time_col], utc=True)
    sub = sub.set_index(time_col)
    signal = sub[value_col].fillna(0.0).values

    # --- Compute Spectrogram ---
    fs = 1.0  # 1 sample per time step (hourly)
    f, t, Sxx = spectrogram(
        signal,
        fs=fs,
        nperseg=window_length,
        noverlap=overlap,
        scaling='density'
    )

    # --- Convert to dB for clearer visualization ---
    Sxx_dB = 10 * np.log10(Sxx + 1e-10)

    # --- Create interactive Plotly figure ---
    fig = go.Figure(
        data=go.Heatmap(
            z=Sxx_dB,
            x=t,
            y=f,
            colorscale='Viridis',
            colorbar=dict(title='Power (dB)'),
        )
    )

    fig.update_layout(
        title=f"Spectrogram — {area} ({group.title()})",
        xaxis_title="Time [index]",
        yaxis_title="Frequency [cycles per time unit]",
        template="plotly_white",
        autosize=True,
        height=500
    )

    return f, t, Sxx, fig


# Function for STL
@st.cache_data(show_spinner=False)
def stl_decomposition_by_area(
    production_df,
    area='NO1',
    group='wind',
    time_col='startTime',
    value_col='quantityKwh',
    period=24,
    seasonal=12,
    trend=365,
    robust=True
):
    """
    Perform STL decomposition for a specific city (price area) and production group.

    Returns
    -------
    result : STL decomposition object
    fig : plotly.graph_objects.Figure (interactive multi‑panel figure)
    """

    # --- Subset data ---
    sub = production_df[
        (production_df['priceArea'] == area) &
        (production_df['productionGroup'].str.lower() == group.lower())
    ].copy()

    if sub.empty:
        raise ValueError(f"No data found for city '{area}' and group '{group}'.")

    # --- Prepare time series ---
    sub = sub.sort_values(time_col)
    sub[time_col] = pd.to_datetime(sub[time_col], utc=True)
    sub = sub.set_index(time_col)

    # --- STL decomposition ---
    stl = STL(
        sub[value_col],
        period=period,
        seasonal=seasonal,
        trend=trend,
        robust=robust
    )
    result = stl.fit()

    # --- Build interactive subplots (4 rows like Matplotlib) ---
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=("Observed", "Trend", "Seasonal", "Residual")
    )

    idx = sub.index

    # Row 1 – Observed
    fig.add_trace(
        go.Scatter(x=idx, y=sub[value_col],
                   mode='lines', name='Observed',
                   line=dict(color='orange')),
        row=1, col=1
    )

    # Row 2 – Trend
    fig.add_trace(
        go.Scatter(x=idx, y=result.trend,
                   mode='lines', name='Trend',
                   line=dict(color='blue')),
        row=2, col=1
    )

    # Row 3 – Seasonal
    fig.add_trace(
        go.Scatter(x=idx, y=result.seasonal,
                   mode='lines', name='Seasonal',
                   line=dict(color='green')),
        row=3, col=1
    )

    # Row 4 – Residual
    fig.add_trace(
        go.Scatter(x=idx, y=result.resid,
                   mode='lines', name='Residual',
                   line=dict(color='red')),
        row=4, col=1
    )

    fig.update_layout(
        height=800,
        title_text=f"STL Decomposition — {area} ({group.title()})",
        showlegend=False,
        template="plotly_white",
        margin=dict(t=60, b=30, l=60, r=25)
    )

    # Axis labels
    fig.update_yaxes(title_text="Observed", row=1, col=1)
    fig.update_yaxes(title_text="Trend", row=2, col=1)
    fig.update_yaxes(title_text="Seasonal", row=3, col=1)
    fig.update_yaxes(title_text="Residual", row=4, col=1)
    fig.update_xaxes(title_text="Time", row=4, col=1)

    return result, fig


# Let user choose production group or year if needed
group = st.selectbox("Select production group", ["wind", "hydro", "solar", "thermal", "other"], index=0)

#st.info(f"Analyzing area:  {area},  group: {group}")

# Tabs
tab1, tab2 = st.tabs(["STL Decomposition", "Spectrogram"])

with tab1:
    st.subheader("Seasonal-Trend Decomposition (LOESS/STL)")
    with st.spinner("Fetching data..."):
        result, fig = stl_decomposition_by_area(
            production_df,
            area=area, group=group,
            period=24, seasonal=13, trend=365, robust=True
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Spectrogram")
    with st.spinner("Fetching data..."):
        f, t, Sxx, fig2 = production_spectrogram(
            production_df,
            area=area, group=group,
            window_length=256, overlap=128
        )
        st.plotly_chart(fig2, use_container_width=True)