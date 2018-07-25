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

from tickers import tickers
from data_spxfetch import *


# Setup app
# server = flask.Flask(__name__)
# server.secret_key = os.environ.get('secret_key', 'secret')
# app = dash.Dash(__name__, server=server, url_base_pathname='/dash/gallery/volatility-surface', csrf_protect=False)
app = dash.Dash(__name__)
server = app.server

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
        ################# Live Graphing ########################
        html.Div([
                html.Div(id='live-update-text',
                         className='twelve columns',
                         style={'text-align': 'center'}),
            ],
                className='row',
                style={'margin-bottom': '20'}
            ),
        
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
                    interval=30*1000, # in milliseconds
                    n_intervals=0
                    )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        
        ################# Options Tables ########################
        html.Div([
            html.H4(
                'Condors and Spreads Tables',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
    
        html.Div([
            html.Div([
                html.Label('Max Spread Width:'),
                dcc.Input(
                    id='maxgap',
                    type='number',
                    value=20
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='four columns',
            ),
            html.Div([
                html.Label('Max DTE:'),
                dcc.Input(
                    id='dtethresh',
                    type='number',
                    value=5,
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='four columns',
            ),
            html.Div([
                html.Label('% Distance from ATM:'),
                dcc.Input(
                    id='moneythresh',
                    type='number',
                    value=0.02,
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='four columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
    
        html.Div([
            html.Label('Condors Table:'),
            dasht.DataTable(
                    # Initialise the rows
                    rows=[{}],
                    row_selectable=True,
                    filterable=True,
                    sortable=True,
                    selected_row_indices=[],
                    id='condors_table'
                    ),
            html.Div(id='selected-indexes')
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ),
    
        html.Div([
            html.Label('Put Spreads Table:'),
            dasht.DataTable(
                    # Initialise the rows
                    rows=[{}],
                    row_selectable=True,
                    filterable=True,
                    sortable=True,
                    selected_row_indices=[],
                    id='puts_table'
                    ),
            html.Div(id='selected-indexes')
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ),
    
        html.Div([
            html.Label('Call Spreads Table:'),
            dasht.DataTable(
                    # Initialise the rows
                    rows=[{}],
                    row_selectable=True,
                    filterable=True,
                    sortable=True,
                    selected_row_indices=[],
                    id='calls_table'
                    ),
            html.Div(id='selected-indexes')
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ),
        
        ################# Daily Plots ########################
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
              [Input('maxgap', 'value'),
               Input('dtethresh','value'),
               Input('moneythresh','value')])
def cache_raw_data(max_gap,dte_thresh,money_thresh):

    global daily_df, vix_df, condors, puts, calls
    daily_df, vix_df = get_daily_data()
    
    condors, puts, calls = earnings_condor('^SPX', max_gap, dte_thresh, money_thresh)
    print('Loaded raw data')

    return 'loaded'

@app.callback(Output('live-update-text', 'children'),
              [Input('raw_container', 'hidden')])
def update_metrics(hidden):
    if hidden == 'loaded':
        vix,spx,daily,intra,ovrnt,dollar=(round(daily_df.tail(1)['VIX Close'][0],2),
                                          round(daily_df.tail(1)['SPX Close'][0],2),
                                          round(daily_df.tail(1)['Daily Annual Vol'][0],2),
                                          round(daily_df.tail(1)['Intraday Annual Vol'][0],2),
                                          round(daily_df.tail(1)['Overnight Annual Vol'][0],2),
                                          round(daily_df.tail(1)['Daily Dollar Vol'][0],2))
        style = {'padding': '5px', 'fontSize': '16px'}
        return [
            html.Span('Last VIX Close: {0:.2f}'.format(vix), style=style),
            html.Span('Last SPX Close: {0:.2f}'.format(spx), style=style),
            html.Span('Daily Annual. Vol: {0:0.2f}'.format(daily), style=style),
            html.Span('Intraday Annual. Vol: {0:0.2f}'.format(intra), style=style),
            html.Span('Overnight Annual. Vol: {0:0.2f}'.format(ovrnt), style=style),
            html.Span('Daily Dollar Vol: {0:0.2f}'.format(dollar), style=style)
        ]

# Multiple components can update everytime interval gets fired.
@app.callback(Output('intraday_vol_plot', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    intraday_data = get_intraday_data().dropna()
    
    trace1 = go.Bar(
		x=intraday_data.index,
		y=intraday_data['Dollar Std Move'],
		name='Intraday Dollar Vol')
    trace2 = go.Scatter(
		x=intraday_data.index,
		y=intraday_data['SPX Close'],
		mode='lines+markers',
		yaxis='y2',
		name='SPX Close')
    trace3 = go.Scatter(
		x=intraday_data.index,
		y=intraday_data['VIX Close'],
		mode='lines+markers',
		yaxis='y3',
		name='VIX Close')
    
    layout = go.Layout(
            yaxis=dict(
                    rangemode="tozero",
                    title='Dollar Std Return'),
            yaxis2=dict(
                    title='Close',
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    zeroline=False,
                    showline=False,
                    ticks='',
                    showticklabels=False
                    ),
            yaxis3=dict(
                    title='Close',
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    zeroline=False,
                    showline=False,
                    ticks='',
                    showticklabels=False
                    )
            )
    data = [trace1, trace2, trace3]
    figure = dict(data=data, layout=layout)
    return figure

# Make side std plot
@app.callback(Output('daily_spx_plot', 'figure'),
              [Input('raw_container', 'hidden')])
def make_dollar_std_plot(hidden):

    if hidden == 'loaded':
        
        trace1 = go.Bar(
                x=daily_df.index,
                y=daily_df['Daily Dollar Std Direction'],
                name='Intraday Dollar Vol')
        
        trace2 = go.Scatter(
                x=daily_df.index,
                y=daily_df['SPX Close'],
                mode='lines+markers',
                yaxis='y2',
                name='SPX Close')
        
        trace3 = go.Scatter(
                x=daily_df.index,
                y=daily_df['VIX Close'],
                mode='lines+markers',
                yaxis='y3',
                name='VIX Close')
        
        layout = go.Layout(
            yaxis=dict(
                    rangemode="tozero",
                    title='Dollar Std Return'),
            yaxis2=dict(
                    title='Close',
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    zeroline=False,
                    showline=False,
                    ticks='',
                    showticklabels=False
                    ),
            yaxis3=dict(
                    title='Close',
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    zeroline=False,
                    showline=False,
                    ticks='',
                    showticklabels=False
                    )
            )

        data = [trace1, trace2, trace3]
        figure = dict(data=data, layout=layout)
        return figure

# Make side scatter plot
@app.callback(Output('daily_vix_plot', 'figure'),
              [Input('raw_container', 'hidden')])
def make_vix_line_plot(hidden):

    if hidden == 'loaded':
        
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
                side='right',
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks=''
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
    
@app.callback(
        Output('condors_table', 'rows'),
        [Input('raw_container', 'hidden')])
def update_condors_table(hidden):
    if hidden == 'loaded':
        return condors.to_dict('records')
    
@app.callback(
        Output('puts_table', 'rows'),
        [Input('raw_container', 'hidden')])
def update_puts_table(hidden):
    if hidden == 'loaded':
        return puts.to_dict('records')
    
@app.callback(
        Output('calls_table', 'rows'),
        [Input('raw_container', 'hidden')])
def update_calls_table(hidden):
    if hidden == 'loaded':
        return calls.to_dict('records')

if __name__ == '__main__':
    # app.server.run(debug=True, threaded=True, use_reloader=False)
	app.run_server(debug = True)