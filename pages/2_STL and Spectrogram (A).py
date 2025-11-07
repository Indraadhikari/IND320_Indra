import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
from statsmodels.tsa.seasonal import STL

st.title("STL analysis and Spectrogram")

# Try to get the selected area and year from Page 2
area = st.session_state.get("selected_area")
production_df = st.session_state.get("df", [])


if area is None or len(production_df) == 0:
    st.warning("Please go back to page 'Energy Production' and select a price area first.")
    st.stop()

st.caption("Info: The analysing datase is the energy production by production data - same data from 'Energy Production' page.")

# Function for spectrogram


def production_spectrogram(
    production_df,
    area='NO1',  # price area (we can use city as STL)
    group='hydro',
    time_col='startTime',
    value_col='quantityKwh',
    window_length=256,  # Controls resolution. Larger windows give better frequency (but worse time precision).
    overlap=128  # Overlap between windows.
):
    """
    Create a spectrogram based on production data for a given price area and group.

    Returns
    f : np.ndarray (Array of sample frequencies)
    t : np.ndarray (Array of segment times)
    Sxx : np.ndarray (Spectrogram intensity matrix)
    fig : matplotlib figure
    """

    #  Filter area and group 
    sub = production_df[(production_df['priceArea'] == area) &
                        (production_df['productionGroup'].str.lower() == group.lower())].copy()

    #  Sort & clean signal 
    sub = sub.sort_values(time_col)
    sub[time_col] = pd.to_datetime(sub[time_col], utc=True)
    sub = sub.set_index(time_col)
    signal = sub[value_col].values

    #  signal = np.nan_to_num(signal)

    #  Compute Spectrogram 
    fs = 1.0  # sampling frequency = 1 sample per time step (hourly)
    f, t, Sxx = spectrogram(
        signal,
        fs=fs,
        nperseg=window_length,
        noverlap=overlap,
        scaling='density'
    )

    fig = None
    fig, ax = plt.subplots(figsize=(10, 5))

    # convert to dB scale for better visualization
    Sxx_dB = 10 * np.log10(Sxx + 1e-10)

    im = ax.pcolormesh(t, f, Sxx_dB, shading='auto', cmap='viridis')
    plt.colorbar(im, ax=ax, label='Power (dB)')
    ax.set_ylabel('Frequency [cycles per time unit]')
    ax.set_xlabel('Time [index]')
    ax.set_title(f"Spectrogram — {area} ({group.title()})")
    plt.tight_layout()

    return f, t, Sxx, fig


# Function for STL


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
        (production_df['productionGroup'].str.lower() == group.lower())
    ].copy()

    sub = sub.sort_values(time_col)
    sub[time_col] = pd.to_datetime(sub[time_col], utc=True)
    sub = sub.set_index(time_col)

    stl = STL(sub[value_col], period=period, seasonal=seasonal, trend=trend, robust=robust)
    result = stl.fit()

    fig = result.plot()
    fig.set_size_inches(10, 7)
    plt.suptitle(f"STL Decomposition — {area} ({group.title()})", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    return result, fig


# Let user choose production group or year if needed
group = st.selectbox("Select production group", ["wind", "hydro", "solar", "thermal", "other"], index=0)

#st.info(f"Analyzing area:  {area},  group: {group}")

# Tabs
tab1, tab2 = st.tabs(["STL Decomposition", "Spectrogram"])

with tab1:
    st.subheader("Seasonal-Trend Decomposition (LOESS/STL)")
    result, fig = stl_decomposition_by_area(
        production_df,
        area=area, group=group,
        period=24, seasonal=13, trend=365, robust=True
    )
    st.pyplot(fig)

with tab2:
    st.subheader("Spectrogram")
    f, t, Sxx, fig2 = production_spectrogram(
        production_df,
        area=area, group=group,
        window_length=256, overlap=128
    )
    st.pyplot(fig2)