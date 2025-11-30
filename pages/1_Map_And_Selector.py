import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import utils as ut

ut.apply_styles()
ut.show_sidebar()

# --- load GeoJSON once, cache to speed up ---
@st.cache_data(show_spinner=False)
def load_geojson():
    url = "https://nve.geodataonline.no/arcgis/rest/services/Mapservices/Elspot/MapServer/0/query?where=OBJECTID%20IN%20(6,7,8,9,10)&outFields=*&f=geojson"
    gdf = gpd.read_file(url)
    return gdf


# --- UPDATED FUNCTION ---
def mean_values_by_area(production_df, group, start_date, end_date):
    """Return mean quantityKwh per priceArea for chosen group and interval (start_date to end_date)."""
    start_date = pd.Timestamp(start_date).tz_localize('UTC')
    end_date = pd.Timestamp(end_date).tz_localize('UTC')
    # Ensure start_date is before end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date # Swap them if necessary
    
    df = production_df[
        (production_df['productionGroup'].str.lower() == group.lower()) &
        (production_df['startTime'].between(pd.to_datetime(start_date), pd.to_datetime(end_date)))
    ]
    return df.groupby('priceArea')['quantityKwh'].mean().reset_index()


def get_area_centroid(geojson_gdf, area_name):
    """Calculate the centroid of a selected price area."""
    selected = geojson_gdf[geojson_gdf['ElSpotOmr'] == area_name]
    if not selected.empty:
        # Get centroid in lat/lon
        centroid = selected.geometry.centroid.iloc[0]
        return (centroid.y, centroid.x)  # (lat, lon)
    return None


st.set_page_config(page_title="Price Areas Map", layout="wide")

st.title("Price Areas NO1 - NO5")

# --- Initialize session state ---
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'selected_coords' not in st.session_state:
    st.session_state.selected_coords = None

with st.spinner("Fetching data..."):
# --- load your production data ---
    production_df = st.session_state.get("df", None)
    if production_df is None:
    
        production_df = ut.load_data_from_mongo(db_name="indra", collection_name="production_per_group")
        #production_df = ut.load_data_from_csv(file_path="No_sync/P_Energy.csv")
        st.session_state["df"] = production_df

    # --- DATA RANGE LIMITS ---
    min_date = production_df['startTime'].min().date()
    max_date = production_df['startTime'].max().date()

# --- Display Data Range Info ---
st.info(f"The available production data ranges from **{min_date.strftime('%Y-%m-%d')}** to **{max_date.strftime('%Y-%m-%d')}**.")

# --- user choices ---
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    group = st.selectbox("Select energy group", ["hydro", "wind", "solar", "thermal", "other"])

# --- UPDATED DATE INPUTS ---
with col2:
    start_date = st.date_input(
        "Start Date (inclusive)",
        value=max_date - pd.Timedelta(days=30), # Default to 30 days back
        min_value=min_date,
        max_value=max_date
    )

with col3:
    end_date = st.date_input(
        "End Date (inclusive)",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

with st.spinner("Fetching data..."):
    geojson = load_geojson()

    # --- compute mean values for chosen interval ---
    # NOTE: Pass start_date and end_date directly
    mean_df = mean_values_by_area(production_df, group, start_date, end_date)
    mean_df['priceArea'] = mean_df['priceArea'].str.replace('NO', 'NO ', regex=False)

    # --- build choropleth map (Map building code remains the same) ---
    fig = px.choropleth_mapbox(
        mean_df,    
        geojson=geojson,
        color="quantityKwh",
        color_continuous_scale="Viridis",
        featureidkey="properties.ElSpotOmr",
        locations="priceArea",
        center={"lat": 65, "lon": 13},
        mapbox_style="carto-positron",
        opacity=0.5,
        zoom=3,
        height=600,
        hover_name="priceArea",
    )

# ... (Rest of the map drawing code for outline, marker, layout, and click handler) ...
# --- Add highlighted outline for selected area ---
if st.session_state.selected_area:
    selected_gdf = geojson[geojson['ElSpotOmr'] == st.session_state.selected_area]
    
    if not selected_gdf.empty:
        selected_geojson = json.loads(selected_gdf.to_json())
        
        for feature in selected_geojson['features']:
            if feature['geometry']['type'] == 'Polygon':
                coords = feature['geometry']['coordinates'][0]
                lons = [coord[0] for coord in coords]
                lats = [coord[1] for coord in coords]
                
                fig.add_trace(go.Scattermapbox(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=dict(width=2, color='red'),
                    name=f'Selected: {st.session_state.selected_area}',
                    showlegend=True,
                    hoverinfo='skip'
                ))
            elif feature['geometry']['type'] == 'MultiPolygon':
                for polygon in feature['geometry']['coordinates']:
                    coords = polygon[0]
                    lons = [coord[0] for coord in coords]
                    lats = [coord[1] for coord in coords]
                    
                    fig.add_trace(go.Scattermapbox(
                        lon=lons,
                        lat=lats,
                        mode='lines',
                        line=dict(width=3, color='red'),
                        name=f'Selected: {st.session_state.selected_area}',
                        showlegend=False,
                        hoverinfo='skip'
                    ))

# --- Add marker for selected coordinates ---
if st.session_state.selected_coords:
    lat, lon = st.session_state.selected_coords
    fig.add_trace(go.Scattermapbox(
        lon=[lon],
        lat=[lat],
        mode='markers',
        marker=dict(size=15, color='red', symbol='star'),
        name='Selected Location',
        showlegend=False,
        hovertext=f'Lat: {lat:.4f}°, Lon: {lon:.4f}°',
        hoverinfo='text'
    ))

fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    coloraxis_colorbar=dict(title="Mean kWh"),
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        bgcolor="rgba(255,255,255,0.8)"
    )
)

# --- Display map and capture click events ---
selected = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points"
)

# --- Handle selection ---
if selected and selected.selection and selected.selection.get("points"):
    points = selected.selection["points"]
    if points:
        point = points[0]
        
        # Get the clicked price area
        clicked_area = point.get("location")
        
        if clicked_area:
            # Area was clicked - update both area and coordinates
            if clicked_area != st.session_state.selected_area:
                st.session_state.selected_area = clicked_area
                
                # Calculate centroid of the selected area
                centroid = get_area_centroid(geojson, clicked_area)
                if centroid:
                    st.session_state.selected_coords = centroid
                
                st.rerun()

if st.button("Clear Selection", use_container_width=True, type="secondary"):
    st.session_state.selected_area = None
    st.session_state.selected_coords = None
    st.rerun()

# --- Display selection info ---

# Calculate number of days for display in the metric
days_diff = (end_date - start_date).days + 1 

col1, col2, col3 = st.columns([30, 30, 50])

with col1:
    if st.session_state.selected_area:
        st.success(f"**Selected Price Area:** {st.session_state.selected_area}")
        
        area_data = mean_df[mean_df['priceArea'] == st.session_state.selected_area]
        if not area_data.empty:
            st.metric(
                label=f"Mean Production ({group})",
                value=f"{area_data['quantityKwh'].values[0]:,.0f} kWh",
                help=f"Average over {days_diff} days"
            )
    else:
        st.info("No price area selected")

with col2:
    if st.session_state.selected_coords:
        lat, lon = st.session_state.selected_coords
        st.success(f"**Selected Coordinates:**")
        st.write(f"📍 Latitude: **{lat:.4f}°**")
        st.write(f"📍 Longitude: **{lon:.4f}°**")
    else:
        st.info("No coordinates selected")

with col3:
    st.metric("Time Period", f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    st.metric("Energy Group", group.title())

#For weathers data
selected_coords = st.session_state.get("selected_coords", None) 
