import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

import plotly.express as px

from om_extract import getData

app = Dash(__name__)


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


app.run_server(debug=True, use_reloader=False)