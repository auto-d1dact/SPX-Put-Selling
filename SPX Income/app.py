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

from tickers import tickers
from data_spxfetch import *


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


# Tickers
tickers = [dict(label=str(ticker), value=str(ticker))
           for ticker in tickers]


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
                'Intraday SPX Movements',
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
        html.Hr(style={'margin': '0', 'margin-bottom': '5'}),
        html.Div([
            html.H4(
                'Intraday Vol Plot',
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
                    interval=10*1000, # in milliseconds
                    n_intervals=0
                    )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            html.H4(
                'Daily SPX/VIX Plot',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
        html.Div([
            dcc.Graph(id='daily_spx_plot', style={'max-height': '600', 'height': '60vh'}),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            html.H4(
                'Daily VIX & Contango Plot',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
        html.Div([
            dcc.Graph(id='daily_vix_plot', style={'max-height': '600', 'height': '60vh'}),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
                html.Label('Select ticker:'),
                dcc.Dropdown(
                    id='ticker_dropdown',
                    options=tickers,
                    value='SPY',
                ),
            ],
                className='row',
            ),
        # Temporary hack for live dataframe caching
        # 'hidden' set to 'loaded' triggers next callback
        html.P(
            hidden='',
            id='raw_container',
            style={'display': 'none'}
        ),
        html.P(
            hidden='',
            id='filtered_container',
            style={'display': 'none'}
        )
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
## Cache raw data
@app.callback(Output('raw_container', 'hidden'),
              [Input('ticker_dropdown', 'value')])
def cache_raw_data(ticker):

    global daily_df, vix_df
    daily_df, vix_df = get_daily_data()
    print('Loaded raw data')

    return 'loaded'

# Multiple components can update everytime interval gets fired.
@app.callback(Output('intraday_vol_plot', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    intraday_data = get_intraday_data().tail(50)

    trace1 = {
        'name':'Intraday Dollar Vol',
        "type": 'bar',
        'mode': 'markers',
        'x': intraday_data.index,
        'y': intraday_data['Dollar Std Move'],
        'boxpoints': 'outliers',
        'marker': {'color': '#00aaff', 'opacity': 0.8}
    }
    
    trace2 = {
        "type": 'scatter',
        'mode': 'lines+markers',
        'name': 'SPX Close',
        'x': intraday_data.index,
        'y': intraday_data['SPX Close'],
        'yaxis': 'y2',
        'marker': {'color': '#ff7f0e', 'opacity': 0.8}
    }
    
    trace3 = {
        "type": 'scatter',
        'mode': 'lines+markers',
        'name': 'VIX Close',
        'x': intraday_data.index,
        'y': intraday_data['VIX Close'],
        'yaxis': 'y3',
        'marker': {'color': '#9467bd', 'opacity': 0.8}
    }
    
    
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
            "title": "Date",
        },
        "yaxis": {
            "rangemode": "tozero",
            "title": "Dollar Return Std.",
            "side": "left"
        },
        "yaxis2": {
            "title": "SPX",
            "overlaying": "y",
            "side": "right"},
        "yaxis3": {
            "title": "VIX",
            'autorange':'True',
            'showgrid':'False',
            'zeroline':'False',
            'showline':'False',
            'ticks':'',
            'showticklabels':'False',
            "overlaying": "y",
            "side": "right"}
    }
        
    data = [trace1, trace2, trace3]
    figure = dict(data=data, layout=layout)
    return figure

# Make side std plot
@app.callback(Output('daily_spx_plot', 'figure'),
              [Input('raw_container', 'hidden')])
def make_dollar_std_plot(hidden):

    if hidden == 'loaded':


        trace1 = {
            'name':'Intraday Dollar Vol',
            "type": 'bar',
            'mode': 'markers',
            'x': daily_df.index,
            'y': daily_df['Daily Dollar Std Direction'],
            'boxpoints': 'outliers',
            'marker': {'color': '#00aaff', 'opacity': 0.8}
        }
        
        trace2 = {
            "type": 'scatter',
            'mode': 'lines+markers',
            'name': 'SPX Close',
            'x': daily_df.index,
            'y': daily_df['SPX Close'],
            'yaxis': 'y2',
            'marker': {'color': '#ff7f0e', 'opacity': 0.8}
        }
        
        trace3 = {
            "type": 'scatter',
            'mode': 'lines+markers',
            'name': 'VIX Close',
            'x': daily_df.index,
            'y': daily_df['VIX Close'],
            'yaxis': 'y3',
            'marker': {'color': '#9467bd', 'opacity': 0.8}
        }
        
        
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
                "title": "Date",
            },
            "yaxis": {
                "rangemode": "tozero",
                "title": "Dollar Return Std.",
                "side": "left"
            },
            "yaxis2": {
                "title": "SPX",
                "overlaying": "y",
                "side": "right"},
            "yaxis3": {
                "title": "VIX",
                'autorange':'True',
                'showgrid':'False',
                'zeroline':'False',
                'showline':'False',
                'ticks':'',
                'showticklabels':'False',
                "overlaying": "y",
                "side": "right"}
        }

        data = [trace1, trace2, trace3]
        figure = dict(data=data, layout=layout)
        return figure

# Make side scatter plot
@app.callback(Output('daily_vix_plot', 'figure'),
              [Input('raw_container', 'hidden')])
def make_vix_line_plot(hidden):

    if hidden == 'loaded':
        
        typ = 'scatter'
        
        trace1 = go.Scatter(
                x=vix_df.index,
                y=vix_df.VIX,
                mode='lines+markers',
                name="VIX",
                hoverinfo='y',
                line=dict(
                    shape='linear'
                )
            )
        trace2 = go.Scatter(
                x=vix_df.index,
                y=vix_df.F1,
                mode='lines+markers',
                name="F1",
                hoverinfo='y',
                line=dict(
                    shape='linear'
                )
            )
        trace3 = go.Scatter(
                x=vix_df.index,
                y=vix_df.F2,
                mode='lines+markers',
                name="F2",
                hoverinfo='y',
                line=dict(
                    shape='linear'
                )
            )
        trace4 = go.Scatter(
                x=vix_df.index,
                y=vix_df.Contango,
                mode='lines+markers',
                name="Contango",
                hoverinfo='y',
                yaxis='y2',
                line=dict(
                    shape='linear'
                )
            )

        layout = dict(
            yaxis=dict(
                title='VIX'
            ),
            yaxis2=dict(
                title='Contango',
                overlaying='y',
                side='right'
            ),
            legend=dict(
                y=1,
                font=dict(
                    size=16
                )
            )
        )

        data = [trace1, trace2, trace3, trace4]
        figure = dict(data=data, layout=layout)
        return figure
    

if __name__ == '__main__':
    app.server.run(port=7000, debug=True, threaded=True, use_reloader=False)
