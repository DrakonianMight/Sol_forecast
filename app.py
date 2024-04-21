import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html, Input, Output

import plotly.express as px

from om_extract import getData

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
application = app.server
app.title='ForeSight Forecast'



app.layout = html.Div([
    html.H4('Forecast'),
    dcc.Graph(id="time-series-chart"),
    html.P("Select site:"),
    dcc.Dropdown(
        id="site",
        options=locs.site,
        value="Brisbane",
        clearable=False,
    ),
])


@app.callback(Output("time-series-chart", "figure"), 
              Input("site", "value"))
def display_time_series(site):
    data = getData(lat, lon, sites)
    sitedata = data[data.site == 'Brisbane']
    sitedata = sitedata.loc[:, sitedata.columns != 'site']
    fig = px.line(sitedata, x=sitedata.index, y = sitedata.columns)
    return fig


if __name__ == '__main__': 
    app.run_server(debug = True, host = '0.0.0.0',  port = 8050)