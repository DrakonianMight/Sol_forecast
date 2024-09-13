import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_auth
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import om_extract as om_extract  # Assuming this is your module for extracting data

# Static hourly parameters
hourly_params = ['shortwave_radiation', 'wind_speed_10m', 'wind_gusts_10m', 'temperature_2m', 'cloud_cover']
# Static daily parameters
daily_params = ['temperature_2m_max', 'temperature_2m_min']

# Define a color mapping for each possible column
color_map = {
    'ecmwf_ifs025': 'orange',
    'ecmwf_aifs025': 'red',
    'bom_access_global': 'green',
    'gfs_global': 'grey',
    'cma_grapes_global': 'purple',
    'ukmo_global_deterministic_10km': 'cyan'
}

# Get list of sites and locations
scatter_geo_df = pd.read_csv('./siteList.csv', skipinitialspace=True, usecols=['site', 'lat', 'lon'])

# Define valid usernames and passwords
VALID_USERNAME_PASSWORD_PAIRS = {
    'helios': 'lpeach',
    'guest': 'w34th3r!!'
}

app = dash.Dash(__name__, external_stylesheets=[{
    "href": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
}, dbc.themes.ZEPHYR])

from dash_bootstrap_templates import load_figure_template
load_figure_template('ZEPHYR')

# Add basic authentication
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

def get_yaxis_title(column):
    title_dict = {
        'shortwave_radiation': 'Shortwave Radiation (W/m²)',
        'wind_speed_10m': 'Wind Speed at 10m (m/s)',
        'wind_gusts_10m': 'Wind Gusts at 10m (m/s)',
        'temperature_2m': 'Temperature at 2m (°C)',
        'cloud_cover': 'Cloud Cover (%)',
        'temperature_2m_max': 'Max Temperature at 2m (°C)',
        'temperature_2m_min': 'Min Temperature at 2m (°C)',
    }
    return title_dict.get(column, column)

# App layout
app.layout = dbc.Container(fluid=True, children=[
    html.Div(
        children=[
            html.H1(
                children='Helios Forecasting Dashboard',
                className="header-title",
                style={'textAlign': 'left', 'color': 'white'}
            ),
            html.P(
                children='Welcome to the Helios Forecasting Dashboard. We produce site-based weather forecasts.',
                className="header-description",
                style={'textAlign': 'left', 'color': 'white'}
            ),
        ],
        className="header-div",
        style={'padding': '20px', 'backgroundColor': '#555555', 'width': '100%'}
    ),
    html.H3(children='Site Forecast', style={'textAlign': 'left'}),
    dbc.Row(children=[
        dbc.Col(md=6, children=[
            dcc.Dropdown(
                id='site-dropdown',
                options=[
                    {'label': site, 'value': site} for site in scatter_geo_df['site']
                ],
                value='Brisbane',  # Default value
                style={'marginBottom': '10px'}  # Add padding
            ),
        ]),
        dbc.Col(md=6, children=[
            dcc.Dropdown(
                 id='column-dropdown',
                 options=[],  # Options will be populated dynamically
                 multi=True,  # Allow multi-select
                 style={'marginBottom': '10px'}
            ),
        ]),
    ]),
    dbc.Row(children=[
        dbc.Col(md=6, children=[
            dcc.Graph(
                id='scatter-geo-plot',
                figure={
                    'data': [
                        go.Scattermapbox(
                            lon=scatter_geo_df['lon'],
                            lat=scatter_geo_df['lat'],
                            text=scatter_geo_df['site'],
                            mode='markers',
                            marker=dict(size=10)
                        )
                    ],
                    'layout': go.Layout(
                        title='Click to select a site',
                        mapbox_style="open-street-map",
                        mapbox=dict(
                            center=dict(
                                lat=scatter_geo_df['lat'].mean(),
                                lon=scatter_geo_df['lon'].mean()
                            ),
                            zoom=3
                        ),
                        margin=dict(l=25, r=25, t=25, b=25)
                    )
                }
            ),
        ]),
        dbc.Col(md=6, children=[
            dcc.Graph(
                id='time-series-plot',
                figure={
                    'layout': go.Layout(
                        margin=dict(l=25, r=25, t=25, b=25),
                        template="simple_white"
                    )
                }
            )
        ]),
    ]),
])

# Callback to update dropdown and plot based on site and selected variables
@app.callback(
    [Output('column-dropdown', 'options'),
     Output('time-series-plot', 'figure')],
    [Input('site-dropdown', 'value'),
     Input('column-dropdown', 'value')]
)
def update_variables_and_plot(selected_site, selected_columns):
    # Combine hourly and daily variables
    all_variables = [('Hourly: ' + var, var, 'hourly') for var in hourly_params] + \
                    [('Daily: ' + var, var, 'daily') for var in daily_params]

    # Generate dropdown options with clearly separated hourly and daily variables
    dropdown_options = [{'label': label, 'value': var} for label, var, data_type in all_variables]

    # Default to all variables if none is selected
    selected_columns = selected_columns or [all_variables[0][1]]

    # Create a figure object
    fig = go.Figure()

    # Loop through each selected column and plot the time series
    for selected_column in selected_columns:
        # Determine if the selected column is from hourly or daily data
        selected_data_type = next(data_type for label, var, data_type in all_variables if var == selected_column)

        # Get data based on whether it's hourly or daily
        if selected_data_type == 'hourly':
            # Retrieve data from hourly dataset
            df = om_extract.getData([str(scatter_geo_df[scatter_geo_df['site'] == selected_site]['lat'].values[0])],
                                    [str(scatter_geo_df[scatter_geo_df['site'] == selected_site]['lon'].values[0])],
                                    [selected_site],
                                    variables=hourly_params)
        elif selected_data_type == 'daily':
            # Retrieve data from daily dataset
            df = om_extract.getDailyData([str(scatter_geo_df[scatter_geo_df['site'] == selected_site]['lat'].values[0])],
                                    [str(scatter_geo_df[scatter_geo_df['site'] == selected_site]['lon'].values[0])],
                                    [selected_site], variables=daily_params)

        # Filter the dataframe for the selected column
        df = df[[col for col in df.columns if selected_column in col]]

        # Add traces for each column
        for col in df.columns:
            # Remove the parameter name from the variable name in the plot (for a cleaner legend)
            cleaned_col = col.replace(selected_column, '').strip('_')

            # Get color for the column from the color map
            color = color_map.get(cleaned_col, 'black')  # Default to black if no color is found

            fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=cleaned_col, line=dict(color=color)))

    # Update layout of the plot to include gridlines
    fig.update_layout(
        title=f'Time Series - {selected_site}',
        yaxis_title="Selected Variables",
        legend=dict(
            title='Model',
            font=dict(size=10),
            orientation="h",
            yanchor="bottom",
            y=-0.75,
            xanchor="left",
            x=0
        ),
        xaxis=dict(showgrid=True),  # Enable gridlines for x-axis
        yaxis=dict(showgrid=True),  # Enable gridlines for y-axis
        hovermode="x unified",
        margin=dict(l=30, r=30, t=30, b=30),
        template="simple_white"
    )

    return dropdown_options, fig

# Callback to update site selection based on map click
@app.callback(
    Output('site-dropdown', 'value'),
    [Input('scatter-geo-plot', 'clickData')]
)
def update_dropdown(clickData):
    if clickData is None:
        return 'Brisbane'
    else:
        selected_site = clickData['points'][0]['text']
        return selected_site

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
