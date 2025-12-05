import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import utils as ut

ut.apply_styles()
ut.show_sidebar()

st.set_page_config(page_title="Snow Drift Analysis", page_icon="❄️", layout="wide")

st.title("Snow Drift Analysis")

# ========== SNOW DRIFT CALCULATION FUNCTIONS ==========

def compute_Qupot(hourly_wind_speeds, dt=3600):
    """Compute potential wind-driven snow transport (Qupot) [kg/m]"""
    total = sum((u ** 3.8) * dt for u in hourly_wind_speeds) / 233847
    return total

def sector_index(direction):
    """Convert wind direction to sector index (0-15)"""
    return int(((direction + 11.25) % 360) // 22.5)

def compute_sector_transport(hourly_wind_speeds, hourly_wind_dirs, dt=3600):
    """Compute transport for each of 16 wind sectors"""
    sectors = [0.0] * 16
    for u, d in zip(hourly_wind_speeds, hourly_wind_dirs):
        idx = sector_index(d)
        sectors[idx] += ((u ** 3.8) * dt) / 233847
    return sectors

def compute_snow_transport(T, F, theta, Swe, hourly_wind_speeds, dt=3600):
    """Compute snow drifting transport according to Tabler (2003)"""
    Qupot = compute_Qupot(hourly_wind_speeds, dt)
    Qspot = 0.5 * T * Swe
    Srwe = theta * Swe
    
    if Qupot > Qspot:
        Qinf = 0.5 * T * Srwe
        control = "Snowfall controlled"
    else:
        Qinf = Qupot
        control = "Wind controlled"
    
    Qt = Qinf * (1 - 0.14 ** (F / T))
    
    return {
        "Qt (kg/m)": Qt,
        "Control": control
    }

def compute_yearly_results(df, T, F, theta):
    """
    Compute yearly snow transport.
    Year defined as July 1 to June 30 of next year.
    """
    seasons = sorted(df['season'].unique())
    results_list = []
    
    for s in seasons:
        season_start = pd.Timestamp(year=s, month=7, day=1)
        season_end = pd.Timestamp(year=s+1, month=6, day=30, hour=23, minute=59, second=59)
        df_season = df[(df['time'] >= season_start) & (df['time'] <= season_end)].copy()
        
        if df_season.empty:
            continue
            
        # Swe = precipitation when temp < 1°C
        df_season['Swe_hourly'] = df_season.apply(
            lambda row: row['precipitation'] if row['temperature'] < 1 else 0, 
            axis=1
        )
        
        total_Swe = df_season['Swe_hourly'].sum()
        wind_speeds = df_season["wind_speed"].tolist()
        
        result = compute_snow_transport(T, F, theta, total_Swe, wind_speeds)
        result["season"] = f"{s}/{s+1}"
        results_list.append(result)
    
    return pd.DataFrame(results_list)

def compute_average_sector(df):
    """Compute average directional breakdown over all seasons"""
    sectors_list = []
    
    for s, group in df.groupby('season'):
        group = group.copy()
        group['Swe_hourly'] = group.apply(
            lambda row: row['precipitation'] if row['temperature'] < 1 else 0,
            axis=1
        )
        ws = group["wind_speed"].tolist()
        wdir = group["wind_direction"].tolist()
        sectors = compute_sector_transport(ws, wdir)
        sectors_list.append(sectors)
    
    avg_sectors = np.mean(sectors_list, axis=0)
    return avg_sectors

def plot_wind_rose(avg_sector_values, overall_avg):
    """Create polar wind rose plot"""
    num_sectors = 16
    angles = np.linspace(0, 360, num_sectors, endpoint=False)
    avg_sector_values_tonnes = np.array(avg_sector_values) / 1000.0
    
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    
    fig = go.Figure()
    
    fig.add_trace(go.Barpolar(
        r=avg_sector_values_tonnes,
        theta=angles,
        width=22.5,
        marker_color='lightblue',
        marker_line_color='black',
        marker_line_width=1,
        name='Snow Transport',
        hovertemplate='<b>%{theta}°</b><br>Transport: %{r:.2f} tonnes/m<extra></extra>'
    ))
    
    overall_tonnes = overall_avg / 1000.0
    
    fig.update_layout(
        title=f"Wind Rose - Average Directional Snow Transport<br>Overall Average: {overall_tonnes:.1f} tonnes/m",
        polar=dict(
            radialaxis=dict(
                showticklabels=True,
                ticks='outside',
                title='Snow Transport (tonnes/m)'
            ),
            angularaxis=dict(
                tickmode='array',
                tickvals=angles,
                ticktext=directions,
                direction='clockwise',
                rotation=90
            )
        ),
        showlegend=False,
        height=600
    )
    
    return fig


@st.cache_data(show_spinner=False)
def fetch_weather_data(lat, lon, start_year, end_year):
    """Fetch hourly weather data from Open-Meteo API"""
    start_date = f"{start_year}-07-01"
    end_date = f"{end_year + 1}-06-30"
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_direction_10m",
        "timezone": "Europe/Oslo"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get('hourly', {})
        
        df = pd.DataFrame({
            'time': pd.to_datetime(hourly['time']),
            'temperature': hourly['temperature_2m'],
            'precipitation': hourly['precipitation'],
            'wind_speed': hourly['wind_speed_10m'],
            'wind_direction': hourly['wind_direction_10m']
        })
        
        # Define season: July onwards = current year, before July = previous year
        df['season'] = df['time'].apply(
            lambda dt: dt.year if dt.month >= 7 else dt.year - 1
        )
        
        return df
    
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return None

# ========== MAIN APP ==========


# Check for selected coordinates
if not st.session_state.get('selected_coords'):
    st.warning("Please go to the Map page and select a location by clicking on a price area.")
  
    if st.button("🗺️ Go to Map Page", type="primary"):
        st.switch_page("pages/1_Map_And_Selector.py") 
    st.stop()

# selected location
lat, lon = st.session_state.selected_coords

# ========== USER INPUTS ==========

col1, col2, col3, col4 = st.columns(4)

with col1:
    start_year = st.number_input(
        "Start Year",
        min_value=1940,
        max_value=2023,
        value=2015,
        step=1
    )

with col2:
    end_year = st.number_input(
        "End Year",
        min_value=start_year,
        max_value=2024,
        value=2024,
        step=1
    )

with col3:
    T = st.number_input(
        "Max transport distance (m)",
        min_value=100,
        max_value=10000,
        value=3000,
        step=100
    )

with col4:
    F = st.number_input(
        "Fetch distance (m)",
        min_value=1000,
        max_value=100000,
        value=30000,
        step=1000
    )

theta = st.slider(
    "Relocation coefficient (θ)",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="Fraction of snow available for relocation"
)


# Calculate button
if st.button("🔄 Calculate Snow Drift", type="primary", use_container_width=False):
    with st.spinner(f"Fetching weather data for {start_year}-{end_year}..."):
        df = fetch_weather_data(lat, lon, start_year, end_year)
    
    if df is not None and not df.empty:
        st.session_state['snow_drift_df'] = df
        st.session_state['snow_drift_params'] = {
            'T': T, 'F': F, 'theta': theta,
            'start_year': start_year, 'end_year': end_year
        }
        st.success("Data fetched successfully!")
        st.rerun()
    else:
        st.error("Failed to fetch weather data. Please try again.")

# ========== RESULTS DISPLAY ==========

if 'snow_drift_df' in st.session_state:
    df = st.session_state['snow_drift_df']
    params = st.session_state['snow_drift_params']
    
    st.divider()
    st.subheader("Results")
    
    with st.spinner("Calculating snow drift..."):
        yearly_df = compute_yearly_results(df, params['T'], params['F'], params['theta'])
        
        if yearly_df.empty:
            st.warning("No complete seasons found in the selected year range.")
            st.stop()
        
        overall_avg = yearly_df['Qt (kg/m)'].mean()
        overall_avg_tonnes = overall_avg / 1000.0
        avg_sectors = compute_average_sector(df)
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Overall Average Qt",
            f"{overall_avg_tonnes:.1f} t/m",
            help="Mean annual snow transport (tonnes per meter)"
        )
    
    with col2:
        st.metric("Number of Seasons", len(yearly_df))
    
    with col3:
        max_drift = yearly_df['Qt (kg/m)'].max() / 1000.0
        st.metric("Maximum Drift", f"{max_drift:.1f} t/m")
    
    st.divider()
    
    # Wind Rose
    st.subheader("Wind Rose - Directional Snow Transport")
    fig_rose = plot_wind_rose(avg_sectors, overall_avg)
    st.plotly_chart(fig_rose, width='stretch')
    
    st.divider()
    
    # Yearly Results Table
    st.subheader("Snow Drift Per Year")
    
    yearly_display = yearly_df.copy()
    yearly_display['Qt (tonnes/m)'] = yearly_display['Qt (kg/m)'] / 1000.0
    
    display_cols = ['season', 'Qt (tonnes/m)', 'Control']
    
    st.dataframe(
        yearly_display[display_cols].style.format({
            'Qt (tonnes/m)': '{:.1f}'
        }),
        width='stretch',
        height=400
    )
    
    # Bar chart
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        x=yearly_display['season'],
        y=yearly_display['Qt (tonnes/m)'],
        marker_color='lightblue',
        hovertemplate='Season: %{x}<br>Qt: %{y:.2f} t/m<extra></extra>'
    ))
    
    fig_bar.add_hline(
        y=overall_avg_tonnes,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Average: {overall_avg_tonnes:.1f} t/m"
    )
    
    fig_bar.update_layout(
        title="Snow Drift Per Year",
        xaxis_title="Season (July-June)",
        yaxis_title="Snow Transport (tonnes/m)",
        height=400
    )
    
    st.plotly_chart(fig_bar, width='stretch')
    

# Help
with st.expander("ℹ️ About this analysis"):
    st.markdown("""
    ### Snow Drift Calculation (Tabler 2003)
    
    **Season Definition:**
    - A year runs from **July 1** to **June 30** of the following year
    - Example: 2020/2021 = July 1, 2020 to June 30, 2021
    
    **Parameters:**
    - **T**: Maximum transport distance (m)
    - **F**: Fetch distance - upwind distance over which wind can accumulate snow (m)
    - **θ (theta)**: Relocation coefficient - fraction of snow available for relocation (0-1)
    
    **Wind Rose:**
    - Shows average directional distribution of snow transport
    - 16 sectors representing wind directions (N, NNE, NE, etc.)
    - Values in tonnes per meter
    
    **Control Type:**
    - **Wind controlled**: Wind speed limits the transport
    - **Snowfall controlled**: Available snow limits the transport
    """)