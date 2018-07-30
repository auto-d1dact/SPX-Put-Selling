# Import required libraries
import os
import datetime as dt

import numpy as np
import pandas as pd
import plotly.plotly as py
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import dash_table_experiments as dasht


from data_vixfetch import *


# Setup app
# server = flask.Flask(__name__)
# server.secret_key = os.environ.get('secret_key', 'secret')
# app = dash.Dash(__name__, server=server, url_base_pathname='/dash/gallery/volatility-surface', csrf_protect=False)
app = dash.Dash()

external_css = ["https://fonts.googleapis.com/css?family=Overpass:300,300i",
                "https://cdn.rawgit.com/plotly/dash-app-stylesheets/dab6f937fd5548cebf4c6dc7e93a10ac438f5efb/dash-technical-charting.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

if 'DYNO' in os.environ:
    app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })


# Make app layout
app.layout = html.Div(
    [
        html.Div([
            html.Img(
                src="http://fchen.info/wp-content/uploads/2016/10/fclogo2.png",
                className='two columns',
                style={
                    'height': '60',
                    'width': '60',
                    'float': 'left',
                    'position': 'relative',
                },
            ),
            html.H1(
                'Intraday SVXY Signals',
                className='eight columns',
                style={'text-align': 'center'}
            ),
            html.Img(
                src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe.png",
                className='two columns',
                style={
                    'height': '60',
                    'width': '135',
                    'float': 'right',
                    'position': 'relative',
                },
            ),
        ],
            className='row'
        ),
        html.Div([
            html.Label('Updated SVXY Data:'),
            dasht.DataTable(
                    # Initialise the rows
                    rows=[{}],
                    row_selectable=True,
                    filterable=True,
                    sortable=True,
                    selected_row_indices=[],
                    id='data_table'
                    ),
            html.Div(id='selected-indexes')
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ),
        html.Hr(style={'margin': '0', 'margin-bottom': '5'}),
        html.Div([
            html.H4(
                'Delayed VIX Term Structure',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
        html.Div([
            dcc.Graph(id='intraday_vol_plot', style={'max-height': '600', 'height': '60vh'}),
            dcc.Interval(
                    id='interval-component',
                    interval=120*1000, # in milliseconds
                    n_intervals=0
                    )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            html.H4(
                'Daily SVXY Plot',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
        html.Div([
            dcc.Graph(id='intraday_svxy_plot', style={'max-height': '600', 'height': '60vh'}),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
         
#        html.Div([
#                html.Label('Select Update:'),
#                dcc.Dropdown(
#                    id='update_dropdown',
#                    options=tickers,
#                    value='update',
#                ),
#            ],
#                className='row',
#            ),
        # Temporary hack for live dataframe caching
        # 'hidden' set to 'loaded' triggers next callback
        html.P(
            hidden='',
            id='raw_container',
            style={'display': 'none'}
        ),
#        html.P(
#            hidden='',
#            id='filtered_container',
#            style={'display': 'none'}
#        )
    ],
    style={
        'width': '85%',
        'max-width': '1200',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'font-family': 'overpass',
        'background-color': '#FFFFFF',
        'padding': '40',
        'padding-top': '20',
        'padding-bottom': '20',
    },
)

#%%
# Cache raw data
@app.callback(Output('raw_container', 'hidden'),
              [Input('interval-component', 'n_intervals')])
def cache_raw_data(n):

    global intraday, svxy_latest, svxy_data, vix
    intraday = intraday_vix_data()
    vix = vix_data()    
    svxy_latest = curr_svxy_data()
    svxy_data = svxy_data()
    
    print('Loaded raw data')

    return 'loaded'

@app.callback(Output('data_table', 'rows'),
              [Input('raw_container', 'hidden')])
def update_table_live(hidden):
    
    if hidden == 'loaded':
        
        curr_contango = 1 - intraday[['Last']].pct_change().dropna().head(2)
        contango = sum(curr_contango['Last'] * maturities(intraday.loc[0,'Expiration'].date()))
        
        
        table_dict = {'Open':[svxy_latest[0]],
                      'High':[svxy_latest[1]],
                      'Low':[svxy_latest[2]],
                      'Last':[svxy_latest[3]],
                      'Current Contango':[np.round(contango,2)],
                      'Last Close Contango': np.round(vix.tail(1)['Contango'].values[0],4),
                      'Return from Open':[100*np.round(svxy_latest[-1]/svxy_latest[0] - 1,4)]}
        
        table = pd.DataFrame(table_dict)
        table = table[['Last','Open','Return from Open','Current Contango',
                       'Last Close Contango','High','Low']]
        return table.to_dict('records')

# Multiple components can update everytime interval gets fired.
@app.callback(Output('intraday_vol_plot', 'figure'),
              [Input('raw_container', 'hidden')])
def update_graph_live(hidden):
    
    if hidden == 'loaded':
        trace1 = go.Scatter(
                x = intraday.Expiration,
                y = intraday.Last,
                hoverinfo='name+x+y',
                mode = 'lines+markers',
                name = 'VX')
        
        layout = {
            'margin': {
                'l': 60,
                'r': 10,
                'b': 60,
                't': 10,
            },
            'paper_bgcolor': '#FAFAFA',
            "hovermode": "closest",
            "xaxis": {
                "title": "Maturity",
            },
            "yaxis": {
                "title": "Price",
                "side": "left"
            }
        }
            
        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure

# Multiple components can update everytime interval gets fired.
@app.callback(Output('intraday_svxy_plot', 'figure'),
              [Input('raw_container', 'hidden')])
def update_svxy_graph_live(hidden):
    
    if hidden == 'loaded':
        trace1 = go.Scatter(
                x = svxy_data.index,
                y = svxy_data.close,
                hoverinfo='name+x+y',
                mode = 'lines+markers',
                name = 'SVXY Intraday')
        
        layout = {
            'margin': {
                'l': 60,
                'r': 10,
                'b': 60,
                't': 10,
            },
            'paper_bgcolor': '#FAFAFA',
            "hovermode": "closest",
            "xaxis": {
                "title": "Time",
            },
            "yaxis": {
                "title": "Price",
                "side": "left"
            }
        }
            
        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure


if __name__ == '__main__':
    app.server.run(port=7000, debug=True, threaded=True, use_reloader=False)
