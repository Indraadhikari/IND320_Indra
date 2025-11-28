import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor
import numpy as np
from scipy.fftpack import dct, idct

st.title("Outlier/SPC and Anomaly/LOF analysis")

df_2021 = st.session_state.get("df_2021")

city = st.session_state.get("city", "Oslo")

if df_2021 is None:
    st.warning("Please go back to page 'Table' and load data first.")
    st.stop()

st.caption(f"Info: These dataset cover open-meteo weathers data for {city} for year 2021.")

# Fuction for SPC Outlier Analysis (Temperature)


def analyze_temperature_outliers(
    df_2021,
    time_col='time',
    temp_col='temperature_2m (°C)',
    freq_cutoff=10,  # Number of low-frequency DCT components to remove (default=10).
    k=3  # Number of robust standard deviations (MAD scaled) for SPC limits (default=3)
    # plot=True # plot by default, not an optional but it is nice to have optional with default value.
):
    """
    Returns
    outliers_df : DataFrame of outlier rows (with SATV column)
    stats : dict of summary statistics
    fig : matplotlib figure
    """

    #  Prepare data 
    data = df_2021.copy()  # This will speed up the plot process as it copy all data once and work with it
    data[time_col] = pd.to_datetime(data[time_col])
    data = data.sort_values(time_col).reset_index(drop=True)

    temps = data[temp_col].astype(float).values

    #  DCT high-pass filter 
    coeff = dct(temps, norm='ortho')
    highpass = np.copy(coeff)
    highpass[:freq_cutoff] = 0.0  # remove low-frequency (seasonal) components
    satv = idct(highpass, norm='ortho')  # Seasonally Adjusted Temperature Variations

    #  Robust SPC limits 
    median_satv = np.median(satv)
    mad_satv = np.median(np.abs(satv - median_satv))
    robust_sigma = 1.4826 * mad_satv  # (robust_sigma = 1.4826; For a formal data- lecture)
    upper = median_satv + k * robust_sigma
    lower = median_satv - k * robust_sigma

    #  Identify outliers 
    outlier_mask = (satv > upper) | (satv < lower)
    outliers_df = data.loc[outlier_mask].copy()
    outliers_df.loc[:, 'SATV'] = satv[outlier_mask]

        #  Compute trend estimate (approximate low‑frequency component)
    temp_trend = temps - satv

    #  Convert SPC limits from SATV back to temperature space
    upper_curve = temp_trend + upper
    lower_curve = temp_trend + lower

    #  Plot 
    # fig = None
    # if plot:

    fig, ax = plt.subplots(figsize=(12, 6))

    #  Plot raw temperatures
    ax.plot(data[time_col], temps, color='orange', lw=1, label='Temperature')
    ax.plot(data[time_col], upper_curve, color='grey', linestyle='--', lw=1, label='Upper SPC limit')
    ax.plot(data[time_col], lower_curve, color='grey', linestyle='--', lw=1, label='Lower SPC limit')

    #  Mark outliers on the raw temperature curve
    ax.scatter(data.loc[outlier_mask, time_col], temps[outlier_mask], color='red', s=20, zorder=3, label='Outliers')

    ax.set_title("Temperature Outliers via DCT High‑pass Filtering & Robust SPC")
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (°C)")
    ax.legend()
    plt.tight_layout()

    #  Summary 
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

    # if plot:
    return outliers_df, stats, fig


# Function for ocal Outlier Factor (Precipitation)

def analyze_precipitation_anomalies(
    df_2021,
    time_col='time',  # Column name for timestamps
    precip_col='precipitation (mm)',  # Column name for precipitation values
    proportion=0.01  # Expected proportion of anomalies (0-1); 1%
):
    """
    Returns
    outlier_df : DataFrame containing only the detected anomalies
    stats : Summary statistics about anomalies
    fig : matplotlib.figure.Figure
    """
    
    df = df_2021.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values(time_col).reset_index(drop=True)
    
    precip = df[precip_col].fillna(0).values.reshape(-1, 1)

    #  Apply LOF (Local Outlier Factor) 
    lof = LocalOutlierFactor(contamination=proportion)
    labels = lof.fit_predict(precip)
    mask = labels == -1  # -1 means anomaly (outlier)
    
    # Extract anomalies
    outlier_df = df[mask].copy()
    outlier_df['LOF_Score'] = lof.negative_outlier_factor_[mask]

    #  Plot 
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df[time_col], df[precip_col], label='Precipitation', color='blue')
    ax.scatter(df.loc[mask, time_col], df.loc[mask, precip_col],
               color='red', label='Anomalies (LOF)', zorder=3)
    ax.set_title("Precipitation Anomalies via Local Outlier Factor")
    ax.set_xlabel("Time")
    ax.set_ylabel("Precipitation (mm)")
    ax.legend()
    plt.tight_layout()

    #  Summary Statistics 
    stats = {
        'n_points': len(df),
        'n_anomalies': len(outlier_df),
        'proportion_anomalies': round(len(outlier_df) / len(df), 4),
        'mean_precipitation': df[precip_col].mean(),
        'mean_anomalies': outlier_df[precip_col].mean() if len(outlier_df) > 0 else None
    }

    #  Return Results 
    return outlier_df, stats, fig


# Tabs
tab1, tab2 = st.tabs(["Temperature Outliers (SPC)", "Precipitation Anomalies (LOF)"])

with tab1:
    st.subheader("SPC Outlier Analysis (Temperature)")
    cutoff = st.slider("DCT frequency cutoff", 5, 50, 10)
    k = st.slider("MAD multiplier (k)", 1, 5, 3)
    outliers, stats, fig = analyze_temperature_outliers(df_2021, freq_cutoff=cutoff, k=k)
    st.pyplot(fig)
    st.write("Summary:")
    st.write(stats)
    # st.dataframe(outliers.head())

with tab2:
    st.subheader("Local Outlier Factor (Precipitation)")
    prop = st.slider("Proportion of anomalies", 0.001, 0.05, 0.01)
    anomalies, stats, fig = analyze_precipitation_anomalies(df_2021, proportion=prop)
    st.pyplot(fig)
    st.write("Summary:")
    st.write(stats)
    # st.dataframe(anomalies.head())
