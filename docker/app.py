import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import om_extract as om_extract
from datetime import datetime, timedelta
from meteostat import Stations, Hourly
import pytz
import numpy as np
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="Weather Forecast Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# Custom CSS to prevent overflow and optimize dashboard layout
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    .stPlotlyChart {
        background-color: white;
    }
    div[data-testid="stMarkdownContainer"] h2 {
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Static hourly parameters
hourly_params = [
    'shortwave_radiation', 
    'temperature_2m', 
    'apparent_temperature',
    'precipitation',
    'cloud_cover',
    'wind_speed_10m',
    'wind_speed_100m',
    'wind_direction_10m',
    'wind_direction_100m',
    'wind_gusts_10m',
    'relative_humidity_2m'
]
# Static daily parameters
daily_params = ['temperature_2m_max', 'temperature_2m_min']

# Define a color mapping for deterministic models
deterministic_color_map = {
    'ecmwf_ifs025': 'orange',
    'ecmwf_aifs025': 'red',
    'bom_access_global': 'green',
    'gfs_global': 'grey',
    'cma_grapes_global': 'purple',
    'ukmo_global_deterministic_10km': 'cyan'
}

# Define a color mapping for ensemble models
ensemble_color_map = {
    'ecmwf_ifs_ensemble': '#FF8C42',
    'gfs_ensemble': '#B8B8B8',
    'bom_access_global_ensemble': '#5FFF8C'
}

# Column name mapping between model data and observational data
column_mapping = {
    'temperature_2m': 'temp',
    'wind_speed_10m': 'wspd',
}

# Available timezones
TIMEZONES = [
    'UTC',
    'Australia/Brisbane',
    'Australia/Sydney',
    'Australia/Melbourne',
    'Australia/Perth',
    'Australia/Adelaide',
    'America/New_York',
    'America/Los_Angeles',
    'Europe/London',
    'Asia/Tokyo',
]

# Helper functions
def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert hex color to rgba string"""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})'

def calculate_exceedance_probability(df: pd.DataFrame, variable: str, threshold: float, models: list) -> pd.DataFrame:
    """Calculate probability of exceeding threshold across ensemble members"""
    result_df = pd.DataFrame(index=df.index)
    
    for model in models:
        model_cols = [col for col in df.columns 
                     if variable in col and model in col and '_member_' in col]
        
        if model_cols:
            ensemble_data = df[model_cols]
            exceedance = (ensemble_data > threshold).sum(axis=1) / len(model_cols) * 100
            result_df[f'{model}_{variable}_exceed_{threshold}'] = exceedance
    
    return result_df

def get_yaxis_title(column):
    title_dict = {
        'shortwave_radiation': 'Shortwave Radiation (W/m²)',
        'temperature_2m': 'Temperature at 2m (°C)',
        'apparent_temperature': 'Apparent Temperature (°C)',
        'precipitation': 'Precipitation (mm)',
        'precipitation_3h': 'Precipitation 3h Accumulation (mm)',
        'precipitation_6h': 'Precipitation 6h Accumulation (mm)',
        'precipitation_12h': 'Precipitation 12h Accumulation (mm)',
        'precipitation_24h': 'Precipitation 24h Accumulation (mm)',
        'wind_speed_10m': 'Wind Speed at 10m (m/s)',
        'wind_speed_100m': 'Wind Speed at 100m (m/s)',
        'wind_direction_10m': 'Wind Direction at 10m (°)',
        'wind_direction_100m': 'Wind Direction at 100m (°)',
        'wind_gusts_10m': 'Wind Gusts at 10m (m/s)',
        'cloud_cover': 'Cloud Cover (%)',
        'relative_humidity_2m': 'Relative Humidity at 2m (%)',
        'temperature_2m_max': 'Max Temperature at 2m (°C)',
        'temperature_2m_min': 'Min Temperature at 2m (°C)',
    }
    return title_dict.get(column, column)

def accumulate_precipitation(df: pd.DataFrame, variable: str, hours: int) -> pd.DataFrame:
    """
    Accumulate precipitation over specified hours
    
    Args:
        df: DataFrame with precipitation data
        variable: Variable name (should contain 'precipitation')
        hours: Number of hours to accumulate (3, 6, 12, or 24)
    
    Returns:
        DataFrame with accumulated precipitation columns
    """
    result_df = df.copy()
    
    # Find all precipitation columns
    precip_cols = [col for col in df.columns if variable in col]
    
    for col in precip_cols:
        # Create new column name
        new_col = col.replace(variable, f'{variable}_{hours}h')
        
        # Rolling sum for accumulation
        result_df[new_col] = df[col].rolling(window=hours, min_periods=1).sum()
    
    return result_df

# Function to fetch nearest stations from Meteostat and get observational data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_nearest_station_data(lat, lon):
    stations = Stations().nearby(lat, lon).fetch(1)
    station_id = stations.index[0]
    station_name = stations['name'][0]
    station_lat = stations['latitude'][0]
    station_lon = stations['longitude'][0]
    
    end = datetime.today()
    start = end - timedelta(days=1)
    
    hourly_data = Hourly(station_id, start, end).fetch()
    hourly_data["station_name"] = station_name
    hourly_data["station_lat"] = station_lat
    hourly_data["station_lon"] = station_lon
    
    return hourly_data

# Load site data
@st.cache_data
def load_site_data():
    return pd.read_csv('./siteList.csv', skipinitialspace=True, usecols=['site', 'lat', 'lon'])

# Cached data fetching functions to prevent repeated API calls
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_hourly_data(lat, lon, location_name, variables):
    """Fetch hourly forecast data with caching"""
    return om_extract.getData([str(lat)], [str(lon)], [location_name], variables=variables)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_daily_data(lat, lon, location_name, variables):
    """Fetch daily forecast data with caching"""
    return om_extract.getDailyData([str(lat)], [str(lon)], [location_name], variables=variables)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_ensemble_data(lat, lon, location_name, variable, models):
    """Fetch ensemble forecast data with caching"""
    return om_extract.getEnsembleData([str(lat)], [str(lon)], [location_name], [variable], models)

def create_site_map(scatter_geo_df, selected_site=None, custom_lat=None, custom_lon=None):
    """Create an interactive Folium map with site locations"""
    
    # Determine center and zoom
    if custom_lat is not None and custom_lon is not None:
        center_lat, center_lon = custom_lat, custom_lon
        zoom_start = 8
    elif selected_site:
        selected_row = scatter_geo_df[scatter_geo_df['site'] == selected_site]
        if not selected_row.empty:
            center_lat = selected_row['lat'].values[0]
            center_lon = selected_row['lon'].values[0]
            zoom_start = 8
        else:
            center_lat = scatter_geo_df['lat'].mean()
            center_lon = scatter_geo_df['lon'].mean()
            zoom_start = 4
    else:
        center_lat = scatter_geo_df['lat'].mean()
        center_lon = scatter_geo_df['lon'].mean()
        zoom_start = 4
    
    # Create Folium map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Add all site markers (blue circles)
    for idx, row in scatter_geo_df.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            popup=f"{row['site']}<br>Lat: {row['lat']:.4f}°<br>Lon: {row['lon']:.4f}°",
            tooltip=row['site'],
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.7
        ).add_to(m)
    
    # Add highlighted marker for selected/custom location (red circle)
    if custom_lat is not None and custom_lon is not None:
        folium.CircleMarker(
            location=[custom_lat, custom_lon],
            radius=10,
            popup=f'Selected Location<br>Lat: {custom_lat:.4f}°<br>Lon: {custom_lon:.4f}°',
            tooltip='Selected Location',
            color='red',
            fill=True,
            fillColor='red',
            fillOpacity=0.9
        ).add_to(m)
    elif selected_site:
        selected_row = scatter_geo_df[scatter_geo_df['site'] == selected_site]
        if not selected_row.empty:
            sel_lat = selected_row['lat'].values[0]
            sel_lon = selected_row['lon'].values[0]
            folium.CircleMarker(
                location=[sel_lat, sel_lon],
                radius=10,
                popup=f'{selected_site}<br>Lat: {sel_lat:.4f}°<br>Lon: {sel_lon:.4f}°',
                tooltip=selected_site,
                color='red',
                fill=True,
                fillColor='red',
                fillOpacity=0.9
            ).add_to(m)
    
    return m

def create_deterministic_time_series_plot(location_name, site_lat, site_lon, selected_column, timezone='UTC', precip_accum=None, thresholds=None):
    """Create time series plot for selected variable with optional threshold lines"""
    fig = go.Figure()
    
    # Fetch observational data
    obs_data = get_nearest_station_data(site_lat, site_lon)
    
    # All variables with their types
    all_variables = [(var, 'hourly') for var in hourly_params] + \
                    [(var, 'daily') for var in daily_params]
    
    # Determine data type
    selected_data_type = next(data_type for var, data_type in all_variables if var == selected_column)
    
    # Store original column name for display
    display_column = selected_column
    
    # Get data based on type
    if selected_data_type == 'hourly':
        df = fetch_hourly_data(site_lat, site_lon, location_name, hourly_params)
    elif selected_data_type == 'daily':
        df = fetch_daily_data(site_lat, site_lon, location_name, daily_params)
    
    # Apply precipitation accumulation if needed
    if selected_column == 'precipitation' and precip_accum:
        df = accumulate_precipitation(df, 'precipitation', precip_accum)
        display_column = f'precipitation_{precip_accum}h'
    
    # Convert timezone if needed
    if timezone != 'UTC':
        try:
            tz = pytz.timezone(timezone)
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC').tz_convert(tz)
            else:
                df.index = df.index.tz_convert(tz)
        except Exception:
            pass
    
    # Filter for selected column
    df = df[[col for col in df.columns if display_column in col]]
    
    # Add traces for each model
    for col in df.columns:
        cleaned_col = col.replace(display_column, '').strip('_')
        color = deterministic_color_map.get(cleaned_col, 'black')
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col], 
            mode='lines', 
            name=cleaned_col, 
            line=dict(color=color)
        ))
    
    # Add observational data if available
    obs_column = column_mapping.get(display_column, display_column)
    if obs_column in obs_data.columns:
        obs_index = obs_data.index
        if timezone != 'UTC':
            try:
                tz = pytz.timezone(timezone)
                if obs_index.tz is None:
                    obs_index = obs_index.tz_localize('UTC').tz_convert(tz)
                else:
                    obs_index = obs_index.tz_convert(tz)
            except Exception:
                pass
        
        fig.add_trace(go.Scatter(
            x=obs_index,
            y=obs_data[obs_column],
            mode='markers',
            name='Observations',
            marker=dict(color='black', size=4, symbol='circle')
        ))
    
    # Add vertical line for current time
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        
        fig.add_shape(
            type="line",
            x0=current_time,
            x1=current_time,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=current_time,
            y=1.02,
            yref="paper",
            text="Now",
            showarrow=False,
            font=dict(color="red", size=12),
            xanchor="left"
        )
    except Exception:
        pass
    
    # Add threshold lines if provided
    if thresholds and len(df.index) > 0:
        for threshold in thresholds:
            fig.add_shape(
                type="line",
                x0=df.index.min(),
                x1=df.index.max(),
                y0=threshold,
                y1=threshold,
                line=dict(color="orange", width=2, dash="dash"),
                name=f'Threshold: {threshold}'
            )
            
            # Add annotation for threshold
            fig.add_annotation(
                x=df.index.max(),
                y=threshold,
                text=f'{threshold}',
                showarrow=False,
                font=dict(color="orange", size=10),
                xanchor="left",
                xshift=5,
                bgcolor="white"
            )
    
    # Update layout
    fig.update_layout(
        title=f'Deterministic Forecast - {location_name} - {display_column}',
        yaxis_title=get_yaxis_title(display_column),
        legend=dict(
            title='Model',
            font=dict(size=9),
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="left",
            x=0
        ),
        xaxis=dict(showgrid=True, title='Time'),
        yaxis=dict(showgrid=True),
        hovermode="x unified",
        margin=dict(l=30, r=30, t=40, b=120),
        template="simple_white",
        height=450
    )
    
    return fig

def create_ensemble_time_series_plot(location_name, site_lat, site_lon, selected_variable, selected_models, 
                                     show_percentiles=True, show_members=False, timezone='UTC', precip_accum=None, thresholds=None):
    """Create ensemble time series plot with percentile bands and optional threshold lines"""
    fig = go.Figure()
    
    # Get ensemble data
    df = fetch_ensemble_data(site_lat, site_lon, location_name, selected_variable, selected_models)
    
    # Apply precipitation accumulation if needed
    display_variable = selected_variable
    if selected_variable == 'precipitation' and precip_accum:
        df = accumulate_precipitation(df, 'precipitation', precip_accum)
        display_variable = f'precipitation_{precip_accum}h'
    
    # Convert timezone if needed
    if timezone != 'UTC':
        try:
            tz = pytz.timezone(timezone)
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC').tz_convert(tz)
            else:
                df.index = df.index.tz_convert(tz)
        except Exception:
            pass
    
    for model in selected_models:
        # Get member columns for this model
        member_cols = [col for col in df.columns 
                      if display_variable in col and model in col and '_member_' in col]
        
        if member_cols:
            color = ensemble_color_map.get(model, '#666666')
            
            # Show individual members if requested
            if show_members:
                for col in member_cols:
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df[col],
                        mode='lines',
                        name=f'{model} (member)',
                        line=dict(color=hex_to_rgba(color, 0.2), width=1),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
            
            # Calculate and show percentiles
            if show_percentiles:
                ensemble_data = df[member_cols]
                
                # Calculate percentiles
                p10 = ensemble_data.quantile(0.10, axis=1)
                p25 = ensemble_data.quantile(0.25, axis=1)
                p50 = ensemble_data.quantile(0.50, axis=1)
                p75 = ensemble_data.quantile(0.75, axis=1)
                p90 = ensemble_data.quantile(0.90, axis=1)
                
                # Add 10-90 percentile band
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=p90,
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=p10,
                    fill='tonexty',
                    mode='lines',
                    name=f'{model} (10-90%)',
                    line=dict(width=0),
                    fillcolor=hex_to_rgba(color, 0.2)
                ))
                
                # Add 25-75 percentile band
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=p75,
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=p25,
                    fill='tonexty',
                    mode='lines',
                    name=f'{model} (25-75%)',
                    line=dict(width=0),
                    fillcolor=hex_to_rgba(color, 0.4)
                ))
                
                # Add median line
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=p50,
                    mode='lines',
                    name=f'{model} (median)',
                    line=dict(color=color, width=2)
                ))
    
    # Add vertical line for current time
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        
        fig.add_shape(
            type="line",
            x0=current_time,
            x1=current_time,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=current_time,
            y=1.02,
            yref="paper",
            text="Now",
            showarrow=False,
            font=dict(color="red", size=12),
            xanchor="left"
        )
    except Exception:
        pass
    
    # Add threshold lines if provided
    if thresholds:
        for threshold in thresholds:
            fig.add_shape(
                type="line",
                x0=df.index.min(),
                x1=df.index.max(),
                y0=threshold,
                y1=threshold,
                line=dict(color="red", width=2, dash="dash"),
                name=f'Threshold: {threshold}'
            )
            
            # Add annotation for threshold
            fig.add_annotation(
                x=df.index.max(),
                y=threshold,
                text=f'{threshold}',
                showarrow=False,
                font=dict(color="red", size=10),
                xanchor="left",
                xshift=5,
                bgcolor="white"
            )
    
    # Update layout
    fig.update_layout(
        title=f'Ensemble Forecast - {location_name} - {display_variable}',
        yaxis_title=get_yaxis_title(display_variable),
        legend=dict(
            title='Model',
            font=dict(size=9),
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="left",
            x=0
        ),
        xaxis=dict(showgrid=True, title='Time'),
        yaxis=dict(showgrid=True),
        hovermode="x unified",
        margin=dict(l=30, r=30, t=40, b=120),
        template="simple_white",
        height=450
    )
    
    return fig, df

def create_exceedance_plot(df_exceedance, thresholds, selected_models, variable, location_name):
    """Create exceedance probability plot"""
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    for i, threshold in enumerate(thresholds):
        color = colors[i % len(colors)]
        for model in selected_models:
            col_name = f'{model}_{variable}_exceed_{threshold}'
            if col_name in df_exceedance.columns:
                fig.add_trace(go.Scatter(
                    x=df_exceedance.index,
                    y=df_exceedance[col_name],
                    mode='lines',
                    name=f'{model} > {threshold}',
                    line=dict(color=color, width=2)
                ))
    
    fig.update_layout(
        title=f'Exceedance Probability - {location_name}',
        yaxis_title='Probability (%)',
        xaxis_title='Time',
        legend=dict(
            font=dict(size=9),
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="left",
            x=0
        ),
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True, range=[0, 100]),
        hovermode="x unified",
        margin=dict(l=30, r=30, t=40, b=120),
        template="simple_white",
        height=300
    )
    
    return fig

# Main app
def main():
    # Simple compact header
    st.markdown("## Weather Forecast Dashboard")
    
    # Load site data
    scatter_geo_df = load_site_data()
    
    # Sidebar for options
    with st.sidebar:
        st.header('Configuration')
        
        # Forecast type
        forecast_type = st.radio(
            "Forecast Type",
            options=['Deterministic', 'Ensemble'],
            key='forecast_type'
        )
        
        # Timezone selection
        timezone = st.selectbox(
            'Timezone',
            options=TIMEZONES,
            index=0,
            key='timezone_select'
        )
        
        # Location mode selection
        location_mode = st.radio(
            "Location Selection",
            options=['Predefined Sites', 'Select from Map'],
            key='location_mode'
        )
        
        # Initialize session state for coordinates
        if 'selected_lat' not in st.session_state:
            st.session_state.selected_lat = -27.47
        if 'selected_lon' not in st.session_state:
            st.session_state.selected_lon = 153.03
        
        if location_mode == 'Predefined Sites':
            # Site selection
            selected_site = st.selectbox(
                'Select Site',
                options=scatter_geo_df['site'].tolist(),
                index=scatter_geo_df['site'].tolist().index('Brisbane') if 'Brisbane' in scatter_geo_df['site'].tolist() else 0
            )
            # Get site coordinates
            site_row = scatter_geo_df[scatter_geo_df['site'] == selected_site]
            site_lat = site_row['lat'].values[0]
            site_lon = site_row['lon'].values[0]
            location_name = selected_site
        else:
            # Map selection mode - coordinates from clicks or manual input
            st.info("🗺️ Click anywhere on the map or enter coordinates manually")
            
            col1, col2 = st.columns(2)
            with col1:
                site_lat = st.number_input(
                    'Latitude',
                    min_value=-90.0,
                    max_value=90.0,
                    value=float(st.session_state.selected_lat),
                    step=0.01,
                    format="%.4f",
                    key='manual_lat_input'
                )
            with col2:
                site_lon = st.number_input(
                    'Longitude',
                    min_value=-180.0,
                    max_value=180.0,
                    value=float(st.session_state.selected_lon),
                    step=0.01,
                    format="%.4f",
                    key='manual_lon_input'
                )
            
            # Update session state if manually changed
            if site_lat != st.session_state.selected_lat or site_lon != st.session_state.selected_lon:
                st.session_state.selected_lat = site_lat
                st.session_state.selected_lon = site_lon
            
            selected_site = None
            location_name = f"Custom ({site_lat:.4f}, {site_lon:.4f})"
        
        st.markdown("---")
        
        # Threshold configuration (variable-specific)
        st.subheader('Thresholds')
        
        # Initialize session state for thresholds
        if 'variable_thresholds' not in st.session_state:
            st.session_state.variable_thresholds = {}
        
        with st.expander("⚙️ Configure Variable Thresholds", expanded=False):
            # Select variable to configure thresholds for
            threshold_variable = st.selectbox(
                'Variable',
                options=hourly_params + daily_params,
                key='threshold_variable_select'
            )
            
            # Initialize thresholds for this variable if not exists
            if threshold_variable not in st.session_state.variable_thresholds:
                st.session_state.variable_thresholds[threshold_variable] = []
            
            # Display current thresholds
            current_thresholds = st.session_state.variable_thresholds[threshold_variable]
            
            st.markdown(f"**Thresholds for {threshold_variable}:**")
            
            # Input for new threshold
            new_threshold = st.number_input(
                "Add new threshold",
                value=None,
                step=0.1,
                key='new_threshold_input',
                placeholder="Enter value"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add Threshold", key='add_threshold_btn'):
                    if new_threshold is not None and new_threshold not in current_thresholds:
                        st.session_state.variable_thresholds[threshold_variable].append(new_threshold)
                        st.session_state.variable_thresholds[threshold_variable].sort()
                        st.rerun()
            
            # Display and allow removal of existing thresholds
            if current_thresholds:
                st.markdown("**Current thresholds:**")
                for idx, thresh in enumerate(current_thresholds):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.text(f"{thresh}")
                    with col_b:
                        if st.button("🗑️", key=f'remove_thresh_{threshold_variable}_{idx}'):
                            st.session_state.variable_thresholds[threshold_variable].remove(thresh)
                            st.rerun()
            else:
                st.info("No thresholds set for this variable")
        
        # Show summary of all configured thresholds
        configured_vars = [var for var, threshs in st.session_state.variable_thresholds.items() if threshs]
        if configured_vars:
            st.caption(f"Variables with thresholds: {', '.join(configured_vars)}")
    
        st.markdown("---")
        
        # Data Attribution
        with st.expander("📚 Data Sources & Attribution", expanded=False):
            st.markdown("""
            **Weather Forecast Data:**
            - [Open-Meteo](https://open-meteo.com/) - Weather API
            - ECMWF IFS & AIFS - European Centre for Medium-Range Weather Forecasts
            - GFS - NOAA Global Forecast System
            - BOM ACCESS - Australian Bureau of Meteorology
            - UKMO - UK Met Office
            - CMA GRAPES - China Meteorological Administration
            
            **Observational Data:**
            - [Meteostat](https://meteostat.net/) - Historical weather observations
            
            **Map Data:**
            - © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors
            
            ---
            
            *This application uses data from multiple sources. Please refer to each provider's terms of use for commercial applications.*
            """)
    
    # Create layout with map on left, controls on right
    map_col, control_col = st.columns([2, 1])
    
    with map_col:
        # Display coordinates
        st.caption(f"📍 {location_name} | Lat: {site_lat:.4f}° | Lon: {site_lon:.4f}°")
        
        # Create and display map
        if location_mode == 'Select from Map':
            st.caption("⬇️ Click anywhere on the map to select a location")
            folium_map = create_site_map(scatter_geo_df, custom_lat=site_lat, custom_lon=site_lon)
        else:
            folium_map = create_site_map(scatter_geo_df, selected_site=selected_site)
        
        # Display Folium map and capture clicks
        map_data = st_folium(
            folium_map,
            width=None,
            height=280,
            returned_objects=['last_clicked'],
            key="folium_map"
        )
        
        # Handle map click - only in Select from Map mode
        if location_mode == 'Select from Map':
            clicked_data = map_data.get('last_clicked')
            if clicked_data:
                st.session_state.selected_lat = clicked_data['lat']
                st.session_state.selected_lon = clicked_data['lng']
                st.rerun()
    
    with control_col:
        st.markdown("### Parameters")
        
        if forecast_type == 'Deterministic':
            # Variable selection (single)
            selected_variable = st.selectbox(
                'Select Variable',
                options=hourly_params + daily_params,
                index=hourly_params.index('temperature_2m'),
                key='det_variable'
            )
            
            # Precipitation accumulation option
            precip_accum = None
            if selected_variable == 'precipitation':
                precip_accum_option = st.selectbox(
                    'Precipitation Accumulation',
                    options=['None', 3, 6, 12, 24],
                    format_func=lambda x: 'None' if x == 'None' else f'{x} hours',
                    key='det_precip_accum_hours'
                )
                if precip_accum_option != 'None':
                    precip_accum = precip_accum_option
            
            # Show active thresholds for this variable
            current_thresholds = st.session_state.variable_thresholds.get(selected_variable, [])
            if current_thresholds:
                st.caption(f"Active thresholds: {', '.join(map(str, current_thresholds))}")
        
        else:  # Ensemble
            # Variable selection
            selected_variable = st.selectbox(
                'Select Variable',
                options=hourly_params,
                index=hourly_params.index('temperature_2m'),
                key='ens_variable'
            )
            
            # Model selection
            available_ensemble_models = ['ecmwf_ifs_ensemble', 'gfs_ensemble']
            selected_models = st.multiselect(
                'Select Models',
                options=available_ensemble_models,
                default=[available_ensemble_models[0]],
                key='ens_models'
            )
            
            # Precipitation accumulation option for ensemble
            precip_accum = None
            if selected_variable == 'precipitation':
                precip_accum_option = st.selectbox(
                    'Precipitation Accumulation',
                    options=['None', 3, 6, 12, 24],
                    format_func=lambda x: 'None' if x == 'None' else f'{x} hours',
                    key='ens_precip_accum_hours'
                )
                if precip_accum_option != 'None':
                    precip_accum = precip_accum_option
            
            # Display options
            disp_col1, disp_col2 = st.columns(2)
            with disp_col1:
                show_percentiles = st.checkbox("Show Percentiles", value=True)
            with disp_col2:
                show_members = st.checkbox("Show Members", value=False)
            
            # Show active thresholds for this variable
            current_thresholds = st.session_state.variable_thresholds.get(selected_variable, [])
            if current_thresholds:
                st.caption(f"Active thresholds: {', '.join(map(str, current_thresholds))}")
    
    # Forecast plots below (full width)
    if forecast_type == 'Deterministic':
        if selected_variable:
            # Get thresholds for the selected variable (or adjusted for accumulation)
            display_var = selected_variable
            if selected_variable == 'precipitation' and precip_accum:
                display_var = f'precipitation_{precip_accum}h'
                # For accumulated precipitation, use the base precipitation thresholds
                plot_thresholds = st.session_state.variable_thresholds.get('precipitation', [])
            else:
                plot_thresholds = st.session_state.variable_thresholds.get(selected_variable, [])
            
            with st.spinner('Loading forecast data...'):
                try:
                    ts_fig = create_deterministic_time_series_plot(
                        location_name, site_lat, site_lon, selected_variable, timezone, precip_accum, plot_thresholds
                    )
                    st.plotly_chart(ts_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading data: {str(e)}")
        else:
            st.info("Please select a variable to display.")
    
    else:  # Ensemble
        if selected_models:
            # Get thresholds for the selected variable (or adjusted for accumulation)\n            # For accumulated precipitation, use the base precipitation thresholds
            if selected_variable == 'precipitation' and precip_accum:
                plot_ens_thresholds = st.session_state.variable_thresholds.get('precipitation', [])
            else:
                plot_ens_thresholds = st.session_state.variable_thresholds.get(selected_variable, [])
            
            with st.spinner('Loading ensemble forecast data...'):
                try:
                    ens_fig, df_ensemble = create_ensemble_time_series_plot(
                        location_name, site_lat, site_lon, selected_variable, selected_models, 
                        show_percentiles, show_members, timezone, precip_accum, plot_ens_thresholds
                    )
                    
                    # Create tabs for percentiles and exceedance analysis
                    tab1, tab2 = st.tabs(["Percentiles", "Exceedance"])
                    
                    with tab1:
                        st.plotly_chart(ens_fig, use_container_width=True)
                    
                    with tab2:
                        if plot_ens_thresholds:
                            # Determine the variable name to use for exceedance calculation
                            exceedance_variable = selected_variable
                            if selected_variable == 'precipitation' and precip_accum:
                                exceedance_variable = f'precipitation_{precip_accum}h'
                            
                            # Calculate exceedance probabilities
                            df_exceedance = pd.DataFrame(index=df_ensemble.index)
                            for threshold in plot_ens_thresholds:
                                df_exceed_temp = calculate_exceedance_probability(
                                    df_ensemble, exceedance_variable, threshold, selected_models
                                )
                                df_exceedance = pd.concat([df_exceedance, df_exceed_temp], axis=1)
                            
                            # Plot exceedance
                            exceed_fig = create_exceedance_plot(
                                df_exceedance, plot_ens_thresholds, selected_models, 
                                exceedance_variable, location_name
                            )
                            st.plotly_chart(exceed_fig, use_container_width=True)
                        else:
                            st.info("Set threshold values in the sidebar for this variable to see exceedance probability analysis.")
                
                except Exception as e:
                    st.error(f"Error loading ensemble data: {str(e)}")
        else:
            st.warning("Please select at least one ensemble model.")

# Run the app
if __name__ == '__main__':
    main()
