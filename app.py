import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import random

# Sample data (you can replace this with your own data)
df = pd.read_csv('indicators.csv')
available_indicators = df['Indicator Name'].unique()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        # Map with markers (use scattermapbox trace)
        dcc.Graph(id='map-with-markers'),
    ], style={'width': '50%', 'display': 'inline-block'}),
    
    html.Div([
        # Line chart 1
        dcc.Graph(id='line-chart1'),
        
        # Line chart 2
        dcc.Graph(id='line-chart2'),
    ], style={'width': '50%', 'display': 'inline-block'}),
    
    # Dropdown for selecting indicators (optional)
    dcc.Dropdown(
        id='indicator-dropdown',
        options=[{'label': i, 'value': i} for i in available_indicators],
        value='Fertility rate, total (births per woman)'
    )
])

@app.callback(
    dash.dependencies.Output('line-chart1', 'figure'),
    [dash.dependencies.Input('map-with-markers', 'clickData')]
)
def update_line_chart1(clickData):
    # Extract data from the clicked marker (e.g., country name)
    # Update line chart 1 data accordingly
    # Example: X.append(X[-1] + 1), Y.append(Y[-1] + Y[-1] * random.uniform(-0.1, 0.1))
    # You can replace this with your own logic
    
    # Return updated line chart 1 figure
    return {
        'data': [go.Scatter(x=X1, y=Y1, mode='lines+markers')],
        'layout': {'title': 'Life Expectancy vs. Fertility Rate'}
    }

@app.callback(
    dash.dependencies.Output('line-chart2', 'figure'),
    [dash.dependencies.Input('map-with-markers', 'clickData')]
)
def update_line_chart2(clickData):
    # Extract data from the clicked marker (e.g., country name)
    # Update line chart 2 data accordingly
    # Example: X.append(X[-1] + 1), Y.append(Y[-1] + Y[-1] * random.uniform(-0.1, 0.1))
    # You can replace this with your own logic
    
    # Return updated line chart 2 figure
    return {
        'data': [go.Scatter(x=X2, y=Y2, mode='lines+markers')],
        'layout': {'title': 'Some Other Indicator'}
    }

if __name__ == '__main__':
    app.run_server(debug=True)