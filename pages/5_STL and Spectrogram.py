import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import spectrogram
from statsmodels.tsa.seasonal import STL
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import utils as ut 

ut.apply_styles()
ut.show_sidebar()

st.title("STL analysis and Spectrogram")

# Try to get the selected area and year
area = st.session_state.get('selected_area', None)
production_df = st.session_state.get("df", [])
selected_data_type = st.session_state.get("selected_data_type", None)


if area:
    st.write(f"Working with Price Area: {area}")

if area is None or len(production_df) == 0:
    st.warning("No price area selected. Please select one from the Map page.")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()

if selected_data_type != "production":
    st.warning("This page only works for production data now. Please select production data")
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py")
    st.stop()

st.caption(f"Info: The analysing dataset is the energy {selected_data_type} data.")
area = area.replace(" ", "")


production_df["startTime"] = pd.to_datetime(production_df["startTime"], utc=True)
available_years = sorted(production_df["startTime"].dt.year.unique())

selected_year = st.selectbox("Select Year:", available_years)

# Filter entire dataframe BEFORE heavy computations
production_df = production_df[production_df["startTime"].dt.year == selected_year]

if production_df.empty:
    st.error(f"No data available for year {selected_year}.")
    st.stop()

with st.spinner("Implementing STL and Spectrogram... ⏳"):

    @st.cache_data(show_spinner=False)
    def production_spectrogram(
        production_df,
        area='NO1',
        group='hydro',
        time_col='startTime',
        value_col='quantityKwh',
        window_length=256,
        overlap=128
    ):
        sub = production_df[
            (production_df['priceArea'] == area) &
            (production_df['energyGroup'].str.lower() == group.lower())
        ].copy()

        if sub.empty:
            raise ValueError(f"No data found for area '{area}' and group '{group}'.")

        sub = sub.sort_values(time_col)
        sub[time_col] = pd.to_datetime(sub[time_col], utc=True)
        sub = sub.set_index(time_col)
        signal = sub[value_col].fillna(0.0).values

        fs = 1.0
        f, t, Sxx = spectrogram(
            signal,
            fs=fs,
            nperseg=window_length,
            noverlap=overlap,
            scaling='density'
        )

        Sxx_dB = 10 * np.log10(Sxx + 1e-10)

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
            title=f"Spectrogram — {area} ({group.title()}) — {selected_year}",
            xaxis_title="Time Index",
            yaxis_title="Frequency",
            template="plotly_white",
            height=500
        )

        return f, t, Sxx, fig


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
        sub = production_df[
            (production_df['priceArea'] == area) &
            (production_df['energyGroup'].str.lower() == group.lower())
        ].copy()

        if sub.empty:
            raise ValueError(f"No data found for city '{area}' and group '{group}'.")

        sub = sub.sort_values(time_col)
        sub[time_col] = pd.to_datetime(sub[time_col], utc=True)
        sub = sub.set_index(time_col)

        stl = STL(
            sub[value_col],
            period=period,
            seasonal=seasonal,
            trend=trend,
            robust=robust
        )
        result = stl.fit()

        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=("Observed", "Trend", "Seasonal", "Residual")
        )

        idx = sub.index

        fig.add_trace(go.Scatter(x=idx, y=sub[value_col], mode='lines', name='Observed'), row=1, col=1)
        fig.add_trace(go.Scatter(x=idx, y=result.trend, mode='lines', name='Trend'), row=2, col=1)
        fig.add_trace(go.Scatter(x=idx, y=result.seasonal, mode='lines', name='Seasonal'), row=3, col=1)
        fig.add_trace(go.Scatter(x=idx, y=result.resid, mode='lines', name='Residual'), row=4, col=1)

        fig.update_layout(
            height=800,
            title_text=f"STL Decomposition — {area} ({group.title()}) — {selected_year}",
            showlegend=False,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Time", row=4, col=1)

        return result, fig


# Group selector
group = st.selectbox("Select production group", ["hydro", "wind","solar", "thermal", "other"], index=0)

# Tabs
tab1, tab2 = st.tabs(["STL Decomposition", "Spectrogram"])

with tab1:
    st.subheader("Seasonal-Trend Decomposition (STL)")
    with st.spinner("Processing STL..."):
        result, fig = stl_decomposition_by_area(
            production_df,
            area=area,
            group=group,
            period=24,
            seasonal=13,
            trend=365,
            robust=True
        )
        st.plotly_chart(fig, width='stretch')

with tab2:
    st.subheader("Spectrogram")
    with st.spinner("Processing Spectrogram..."):
        f, t, Sxx, fig2 = production_spectrogram(
            production_df,
            area=area,
            group=group,
            window_length=256,
            overlap=128
        )
        st.plotly_chart(fig2, width='stretch')
