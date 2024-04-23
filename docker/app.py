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

params = ['shortwave_radiation','wind_speed_10m','temperature_2m','cloud_cover']

# Define valid usernames and passwords
VALID_USERNAME_PASSWORD_PAIRS = {
    'helios': 'lpeach',
    # Add more username/password pairs as needed
}


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Add basic authentication
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# App layout
app.layout = dbc.Container(fluid=True, children=[
    html.H1(children='Helios Forecasting Dashboard'),
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
    dbc.Row(children=[
        dbc.Col(md=6, children=[
            dcc.Dropdown(
                id='site-dropdown',
                options=[
                    {'label': site, 'value': site} for site in scatter_geo_df['site']
                ],
                value='Brisbane'  # Default value
            ),
        ]),
        dbc.Col(md=6, children=[
            dcc.Dropdown(
                 id='column-dropdown',
                 options=[
                     {'label': column, 'value': column} for column in params
                 ],
                 value=params[0],)  # Default value
            # Your other components go here
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
    df = om_extract.getData( [str(mySite.lat.values[0])] , [str(mySite.lon.values[0])]  ,[selected_site], variables = ['shortwave_radiation','wind_speed_10m','temperature_2m','cloud_cover'] )
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
        title=f'Time Series Line Plot - {selected_site}',
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
    fig.update_yaxes(title_text=selected_column)

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
    app.run_server(debug=True)
