import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_auth
import pandas as pd
import plotly.graph_objs as go

import plotly.express as px

import om_extract as om_extract


# get list of sites and locations
scatter_geo_df = pd.read_csv('./siteList.csv' ,skipinitialspace=True,usecols= ['site','lat','lon'])

params = ['shortwave_radiation','wind_speed_10m', 'wind_gusts_10m','temperature_2m','cloud_cover']

# Define valid usernames and passwords
VALID_USERNAME_PASSWORD_PAIRS = {
    'helios': 'lpeach',
    'guest': 'shenanigans'}
    # Add more username/password pairs as needed


app = dash.Dash(__name__, external_stylesheets=[{  "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },dbc.themes.ZEPHYR])

from dash_bootstrap_templates import load_figure_template
load_figure_template('ZEPHYR')


# Add basic authentication
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)


def get_yaxis_title(column):
    # Define a dictionary that maps column names to y-axis titles
    title_dict = {
        'shortwave_radiation': 'Shortwave Radiation (W/m²)',
        'wind_speed_10m': 'Wind Speed at 10m (m/s)',
        'wind_gusts_10m': 'Wind Gusts at 10m (m/s)',
        'temperature_2m': 'Temperature at 2m (°C)',
        'cloud_cover': 'Cloud Cover (%)',

        # Add more mappings as needed
    }

    # Return the corresponding y-axis title if it exists, otherwise return the column name
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
                children='Welcome to the Helios Forecasting Dashboard. We produce site based weather forecasts.',
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
                 options=[
                     {'label': get_yaxis_title(column), 'value': column} for column in ['shortwave_radiation', 'wind_speed_10m', 'wind_gusts_10m', 'temperature_2m', 'cloud_cover']
                 ],
                 value=params[0],  # Default value
                 style={'marginBottom': '10px'}  # Add padding
            ),
            # Your other components go here
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
                    template="simple_white"  # Adjust as needed
                    )
                }
            )
        ]),
    ]),
])


# Callback to update the plot based on dropdown selection
@app.callback(
    Output('time-series-plot', 'figure'),
    [Input('site-dropdown', 'value'),
     Input('column-dropdown', 'value')]
)
def update_plot(selected_site, selected_column):

    mySite = scatter_geo_df[scatter_geo_df['site'] == selected_site]

    # Get data for the selected site
    df = om_extract.getData( [str(mySite.lat.values[0])] , [str(mySite.lon.values[0])]  ,[selected_site], variables = ['shortwave_radiation','wind_speed_10m', 'wind_gusts_10m','temperature_2m','cloud_cover'] )
    colName = df.columns[[selected_column in c for c in df.columns]]
    # Create a dictionary mapping original column names to modified names
    new_legend_names = {c: c.replace(selected_column, '') for c in colName}

    df = df[df.columns[[selected_column in c for c in df.columns]]]
    df.columns = [new_legend_names[c] for c in df.columns]
    df = df.drop([col for col in df.columns if df[col].apply(type).eq(type(None)).any()], axis=1)

    # Create a new figure
    fig = go.Figure()

    # Add a scatter trace for each column
    for col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col))

    # Update the layout
    fig.update_layout(
        title=f'Time Series - {selected_site}',
        yaxis_title=get_yaxis_title(selected_column),
        legend=dict(
            title='Model',
            font=dict(
                size=10,  # Adjust as needed
            ),
            orientation="h",
            yanchor="bottom",
            y=-.75,
            xanchor="left",
            x=0
        ),
        hovermode="x unified",
        margin=dict(l=30, r=30, t=30, b=30),
        template="simple_white"  # Adjust as needed
    )

    # Update the hover template for each trace
    for trace in fig.data:
        trace.hovertemplate = '<b>%{y}</b><br>%{fullData.name}<extra></extra>'

    # Update the y-axis label
    fig.update_yaxes(title_text=get_yaxis_title(selected_column))

    return fig

# Callback to update dropdown selection based on marker click
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
    app.run_server(debug = True, host = '0.0.0.0',  port = 8050)
