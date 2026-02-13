import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd
import plotly.graph_objs as go
import om_extract
from datetime import datetime, timedelta
from meteostat import Stations, Hourly
import pytz
import numpy as np
import logging
import time
import os
from functools import wraps, lru_cache
from flask_caching import Cache

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment configuration
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour default
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Weather Forecast Dashboard"
)

# Configure server-side caching
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': CACHE_TTL
})

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

# Define color mappings
deterministic_color_map = {
    'ecmwf_ifs025': 'orange',
    'ecmwf_aifs025': 'red',
    'bom_access_global': 'green',
    'gfs_global': 'grey',
    'cma_grapes_global': 'purple',
    'ukmo_global_deterministic_10km': 'cyan'
}

ensemble_color_map = {
    'ecmwf_ifs_ensemble': '#FF8C42',
    'gfs_ensemble': '#B8B8B8',
    'bom_access_global_ensemble': '#5FFF8C'
}

# Column name mapping
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

def get_yaxis_title(column):
    """Get appropriate y-axis title for a given column"""
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
    """Accumulate precipitation over specified hours"""
    result_df = df.copy()
    precip_cols = [col for col in df.columns if variable in col]
    
    for col in precip_cols:
        new_col = col.replace(variable, f'{variable}_{hours}h')
        result_df[new_col] = df[col].rolling(window=hours, min_periods=1).sum()
    
    return result_df

# Cached data loading functions
@cache.memoize(timeout=CACHE_TTL * 2)
def load_site_data():
    """Load predefined site locations from CSV"""
    logger.info("📍 Loading site data")
    return pd.read_csv('./siteList.csv', skipinitialspace=True, usecols=['site', 'lat', 'lon'])

@cache.memoize(timeout=CACHE_TTL * 2)
def get_nearest_station_data(lat, lon):
    """Fetch observational data from nearest weather station"""
    logger.info(f"🔍 Fetching station data near {lat:.2f}, {lon:.2f}")
    try:
        stations = Stations().nearby(lat, lon).fetch(1)
        
        if stations.empty:
            logger.warning(f"No stations found near {lat}, {lon}")
            return None
        
        station_id = stations.index[0]
        station_name = stations['name'][0]
        station_lat = stations['latitude'][0]
        station_lon = stations['longitude'][0]
        
        end = datetime.today()
        start = end - timedelta(days=1)
        
        hourly_data = Hourly(station_id, start, end).fetch()
        
        if hourly_data.empty:
            logger.warning(f"No data available for station {station_id}")
            return None
        
        hourly_data["station_name"] = station_name
        hourly_data["station_lat"] = station_lat
        hourly_data["station_lon"] = station_lon
        
        logger.info(f"✅ Fetched {len(hourly_data)} records from {station_name}")
        return hourly_data
    except Exception as e:
        logger.error(f"❌ Error fetching station data: {str(e)}")
        return None

@cache.memoize(timeout=CACHE_TTL)
def fetch_hourly_data(lat, lon, location_name, variables):
    """Fetch hourly forecast data with caching"""
    logger.info(f"📥 Fetching hourly data for {location_name}")
    try:
        data = om_extract.getData([str(lat)], [str(lon)], [location_name], variables=variables)
        logger.info(f"✅ Fetched hourly data: {data.shape if data is not None else 'None'}")
        return data
    except Exception as e:
        logger.error(f"❌ Error fetching hourly data: {str(e)}")
        return None

@cache.memoize(timeout=CACHE_TTL)
def fetch_daily_data(lat, lon, location_name, variables):
    """Fetch daily forecast data with caching"""
    logger.info(f"📥 Fetching daily data for {location_name}")
    try:
        data = om_extract.getDailyData([str(lat)], [str(lon)], [location_name], variables=variables)
        logger.info(f"✅ Fetched daily data: {data.shape if data is not None else 'None'}")
        return data
    except Exception as e:
        logger.error(f"❌ Error fetching daily data: {str(e)}")
        return None

@cache.memoize(timeout=CACHE_TTL)
def fetch_ensemble_data(lat, lon, location_name, variables):
    """Fetch ensemble forecast data with caching"""
    logger.info(f"📥 Fetching ensemble data for {location_name}")
    try:
        data = om_extract.getEnsembleData([str(lat)], [str(lon)], [location_name], variables=variables)
        logger.info(f"✅ Fetched ensemble data: {data.shape if data is not None else 'None'}")
        return data
    except Exception as e:
        logger.error(f"❌ Error fetching ensemble data: {str(e)}")
        return None

# Layout components
def create_sidebar():
    """Create sidebar with configuration options"""
    site_data = load_site_data()
    
    return dbc.Col([
        html.H4("Configuration", className="mb-3"),
        
        # Forecast type
        dbc.Label("Forecast Type"),
        dcc.RadioItems(
            id='forecast-type',
            options=[
                {'label': ' Deterministic', 'value': 'Deterministic'},
                {'label': ' Ensemble', 'value': 'Ensemble'}
            ],
            value='Deterministic',
            className="mb-3"
        ),
        
        # Timezone
        dbc.Label("Timezone"),
        dcc.Dropdown(
            id='timezone-select',
            options=[{'label': tz, 'value': tz} for tz in TIMEZONES],
            value='UTC',
            clearable=False,
            className="mb-3"
        ),
        
        # Location mode
        dbc.Label("Location Selection"),
        dcc.RadioItems(
            id='location-mode',
            options=[
                {'label': ' Predefined Sites', 'value': 'predefined'},
                {'label': ' Select from Map', 'value': 'map'}
            ],
            value='predefined',
            className="mb-3"
        ),
        
        # Site selection (for predefined mode)
        html.Div([
            dbc.Label("Select Site"),
            dcc.Dropdown(
                id='site-select',
                options=[{'label': site, 'value': site} for site in site_data['site'].tolist()],
                value='Brisbane' if 'Brisbane' in site_data['site'].tolist() else site_data['site'].tolist()[0],
                clearable=False,
                className="mb-3"
            ),
        ], id='site-selector-div'),
        
        # Manual coordinate input (for map mode)
        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Latitude"),
                    dbc.Input(id='lat-input', type='number', value=-27.47, step=0.01, min=-90, max=90),
                ], width=6),
                dbc.Col([
                    dbc.Label("Longitude"),
                    dbc.Input(id='lon-input', type='number', value=153.03, step=0.01, min=-180, max=180),
                ], width=6),
            ], className="mb-3"),
        ], id='coord-input-div', style={'display': 'none'}),
        
        html.Hr(),
        
        # Variable selection (deterministic mode)
        html.Div([
            dbc.Label("Select Variable"),
            dcc.Dropdown(
                id='variable-select',
                options=[{'label': get_yaxis_title(var), 'value': var} for var in hourly_params + daily_params],
                value='temperature_2m',
                clearable=False,
                className="mb-3"
            ),
            
            # Precipitation accumulation
            html.Div([
                dbc.Label("Precipitation Accumulation"),
                dcc.Dropdown(
                    id='precip-accum',
                    options=[
                        {'label': 'Hourly', 'value': 'none'},
                        {'label': '3-hour', 'value': '3'},
                        {'label': '6-hour', 'value': '6'},
                        {'label': '12-hour', 'value': '12'},
                        {'label': '24-hour', 'value': '24'},
                    ],
                    value='none',
                    clearable=False,
                    className="mb-3"
                ),
            ], id='precip-accum-div', style={'display': 'none'}),
        ], id='deterministic-controls'),
        
        # Ensemble controls
        html.Div([
            dbc.Label("Select Variable"),
            dcc.Dropdown(
                id='ensemble-variable-select',
                options=[{'label': get_yaxis_title(var), 'value': var} for var in hourly_params],
                value='temperature_2m',
                clearable=False,
                className="mb-3"
            ),
            
            dbc.Label("Select Ensemble Models"),
            dcc.Checklist(
                id='ensemble-models',
                options=[
                    {'label': ' ECMWF IFS Ensemble', 'value': 'ecmwf_ifs_ensemble'},
                    {'label': ' GFS Ensemble', 'value': 'gfs_ensemble'},
                    {'label': ' BOM ACCESS Ensemble', 'value': 'bom_access_global_ensemble'},
                ],
                value=['ecmwf_ifs_ensemble'],
                className="mb-3"
            ),
            
            dbc.Label("Exceedance Threshold"),
            dbc.Input(id='exceedance-threshold', type='number', value=25, step=0.1, className="mb-3"),
        ], id='ensemble-controls', style={'display': 'none'}),
        
        html.Hr(),
        html.Small("⚡ Built with Dash", className="text-muted"),
        
    ], width=3, className="bg-light p-3", style={'height': '100vh', 'overflow-y': 'auto'})

def create_main_content():
    """Create main content area"""
    return dbc.Col([
        # Header
        html.H2("Weather Forecast Dashboard", className="mb-4"),
        
        # Loading spinner
        dcc.Loading(
            id="loading-main",
            type="default",
            children=[
                # Map
                html.Div([
                    dl.Map(
                        id='map',
                        center=[-27.47, 153.03],
                        zoom=10,
                        children=[
                            dl.TileLayer(),
                            dl.Marker(id='location-marker', position=[-27.47, 153.03])
                        ],
                        style={'width': '100%', 'height': '400px'},
                        className="mb-4"
                    )
                ], id='map-div'),
                
                # Chart container
                html.Div([
                    dcc.Graph(id='forecast-chart', style={'height': '600px'})
                ], className="mb-4"),
                
                # Stats/Info
                html.Div(id='info-div', className="mb-4")
            ]
        )
    ], width=9, className="p-3")

# App layout
app.layout = dbc.Container([
    dcc.Store(id='selected-coords', data={'lat': -27.47, 'lon': 153.03}),
    dcc.Interval(id='performance-timer', interval=1000, max_intervals=1),
    dbc.Row([
        create_sidebar(),
        create_main_content()
    ])
], fluid=True, className="p-0")

# Callbacks
@app.callback(
    [Output('site-selector-div', 'style'),
     Output('coord-input-div', 'style'),
     Output('map-div', 'style')],
    Input('location-mode', 'value')
)
def toggle_location_mode(mode):
    """Toggle between predefined sites and map selection"""
    if mode == 'predefined':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}, {'display': 'block'}

@app.callback(
    [Output('deterministic-controls', 'style'),
     Output('ensemble-controls', 'style')],
    Input('forecast-type', 'value')
)
def toggle_forecast_controls(forecast_type):
    """Toggle between deterministic and ensemble controls"""
    if forecast_type == 'Deterministic':
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}

@app.callback(
    Output('precip-accum-div', 'style'),
    Input('variable-select', 'value')
)
def toggle_precip_controls(variable):
    """Show precipitation accumulation options when precipitation is selected"""
    if variable == 'precipitation':
        return {'display': 'block'}
    return {'display': 'none'}

@app.callback(
    Output('selected-coords', 'data'),
    [Input('site-select', 'value'),
     Input('lat-input', 'value'),
     Input('lon-input', 'value'),
     Input('location-mode', 'value')]
)
def update_coordinates(site, lat, lon, mode):
    """Update selected coordinates based on site or manual input"""
    if mode == 'predefined' and site:
        site_data = load_site_data()
        site_row = site_data[site_data['site'] == site]
        if not site_row.empty:
            return {
                'lat': float(site_row['lat'].values[0]),
                'lon': float(site_row['lon'].values[0]),
                'name': site
            }
    return {'lat': lat, 'lon': lon, 'name': f"Custom ({lat:.4f}, {lon:.4f})"}

@app.callback(
    Output('location-marker', 'position'),
    Input('selected-coords', 'data')
)
def update_marker(coords):
    """Update map marker position"""
    return [coords['lat'], coords['lon']]

@app.callback(
    [Output('forecast-chart', 'figure'),
     Output('info-div', 'children')],
    [Input('selected-coords', 'data'),
     Input('forecast-type', 'value'),
     Input('variable-select', 'value'),
     Input('ensemble-variable-select', 'value'),
     Input('ensemble-models', 'value'),
     Input('exceedance-threshold', 'value'),
     Input('timezone-select', 'value'),
     Input('precip-accum', 'value')]
)
def update_forecast(coords, forecast_type, det_variable, ens_variable, ens_models, threshold, timezone, precip_accum):
    """Update forecast chart based on selections"""
    start_time = time.time()
    
    lat = coords['lat']
    lon = coords['lon']
    location_name = coords.get('name', f"({lat:.4f}, {lon:.4f})")
    
    try:
        if forecast_type == 'Deterministic':
            # Fetch deterministic data
            variable = det_variable
            
            # Determine if hourly or daily
            if variable in daily_params:
                df = fetch_daily_data(lat, lon, location_name, [variable])
            else:
                df = fetch_hourly_data(lat, lon, location_name, [variable])
            
            if df is None or df.empty:
                return go.Figure().add_annotation(text="No data available", showarrow=False), "No data"
            
            # Apply precipitation accumulation if needed
            if variable == 'precipitation' and precip_accum != 'none':
                df = accumulate_precipitation(df, variable, int(precip_accum))
                variable = f'precipitation_{precip_accum}h'
            
            # Convert timezone
            if timezone != 'UTC':
                df.index = df.index.tz_localize('UTC').tz_convert(timezone)
            
            # Create figure
            fig = go.Figure()
            
            # Add model traces
            for col in df.columns:
                if variable in col and '_member_' not in col:
                    model_name = col.split('_')[0] if '_' in col else col
                    color = deterministic_color_map.get(model_name, 'blue')
                    
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df[col],
                        mode='lines',
                        name=model_name.upper(),
                        line=dict(color=color, width=2)
                    ))
            
            # Try to add observations
            obs_data = get_nearest_station_data(lat, lon)
            if obs_data is not None:
                obs_col = column_mapping.get(variable, variable)
                if obs_col in obs_data.columns:
                    if timezone != 'UTC':
                        obs_data.index = obs_data.index.tz_localize('UTC').tz_convert(timezone)
                    
                    fig.add_trace(go.Scatter(
                        x=obs_data.index,
                        y=obs_data[obs_col],
                        mode='markers',
                        name='Observations',
                        marker=dict(color='black', size=6)
                    ))
            
            fig.update_layout(
                title=f"{get_yaxis_title(variable)} - {location_name}",
                xaxis_title=f"Time ({timezone})",
                yaxis_title=get_yaxis_title(variable),
                hovermode='x unified',
                template='plotly_white',
                height=600
            )
            
        else:  # Ensemble
            variable = ens_variable
            df = fetch_ensemble_data(lat, lon, location_name, [variable])
            
            if df is None or df.empty:
                return go.Figure().add_annotation(text="No data available", showarrow=False), "No data"
            
            # Convert timezone
            if timezone != 'UTC':
                df.index = df.index.tz_localize('UTC').tz_convert(timezone)
            
            # Create figure
            fig = go.Figure()
            
            # Add ensemble members and percentiles for each model
            for model in ens_models:
                color = ensemble_color_map.get(model, '#888888')
                
                # Get member columns
                member_cols = [col for col in df.columns if variable in col and model in col and '_member_' in col]
                
                if member_cols:
                    # Add individual members
                    for col in member_cols:
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df[col],
                            mode='lines',
                            name=f'{model} member',
                            line=dict(color=hex_to_rgba(color, 0.2), width=1),
                            showlegend=False,
                            hovertemplate=f'{model}<br>%{{y:.1f}}<extra></extra>'
                        ))
                    
                    # Calculate percentiles
                    ensemble_data = df[member_cols]
                    p10 = ensemble_data.quantile(0.1, axis=1)
                    p50 = ensemble_data.quantile(0.5, axis=1)
                    p90 = ensemble_data.quantile(0.9, axis=1)
                    
                    # Add percentile traces
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=p90,
                        mode='lines',
                        name=f'{model} P90',
                        line=dict(color=color, dash='dash', width=1),
                        showlegend=True
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=p50,
                        mode='lines',
                        name=f'{model} Median',
                        line=dict(color=color, width=3),
                        showlegend=True
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=p10,
                        mode='lines',
                        name=f'{model} P10',
                        line=dict(color=color, dash='dash', width=1),
                        fill='tonexty',
                        fillcolor=hex_to_rgba(color, 0.2),
                        showlegend=True
                    ))
                    
                    # Add exceedance probability
                    if threshold is not None:
                        exceed = (ensemble_data > threshold).sum(axis=1) / len(member_cols) * 100
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=exceed,
                            mode='lines',
                            name=f'{model} P(>{threshold})',
                            line=dict(color=color, dash='dot', width=2),
                            yaxis='y2'
                        ))
            
            fig.update_layout(
                title=f"{get_yaxis_title(variable)} - Ensemble Forecast - {location_name}",
                xaxis_title=f"Time ({timezone})",
                yaxis_title=get_yaxis_title(variable),
                yaxis2=dict(
                    title="Exceedance Probability (%)",
                    overlaying='y',
                    side='right',
                    range=[0, 100]
                ),
                hovermode='x unified',
                template='plotly_white',
                height=600
            )
        
        duration = time.time() - start_time
        info = html.Div([
            html.P(f"⏱️ Load time: {duration:.2f}s", className="text-muted"),
            html.P(f"📍 Location: {location_name} ({lat:.4f}, {lon:.4f})", className="text-muted"),
        ])
        
        return fig, info
        
    except Exception as e:
        logger.error(f"❌ Error updating forecast: {str(e)}", exc_info=True)
        return go.Figure().add_annotation(text=f"Error: {str(e)}", showarrow=False), f"Error: {str(e)}"

# Run server
if __name__ == '__main__':
    port = int(os.getenv('PORT', 8050))
    app.run_server(debug=DEBUG_MODE, host='0.0.0.0', port=port)
