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

from py_vollib.black_scholes_merton.implied_volatility import *
from py_vollib.black_scholes_merton.greeks.analytical import *
from data_collect import *


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
    

def generate_table(dataframe):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(len(dataframe))]
    )

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
                'Earnings Screening',
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
        
        ################# Input for Earnings DF Layout ########################
        html.Div([
            html.H4(
                'Upcoming Earnings',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
        
        html.Div([
            html.Div([
                html.Label('Starting Date:',
                           style={'text-align': 'center'}),
                dcc.DatePickerSingle(
                    id='startdate',
                    date=dt.date.today(),
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='three columns',
            ),
            html.Div([
                html.Label('Days Forward:',
                           style={'text-align': 'left'}),
                dcc.Slider(
                    id='forward_days',
                    marks={i: '{}'.format(i) for i in range(11)},
                    min=0,
                    max=10,
                    step=1,
                    value=0
                )
            ],
                className='six columns',
                style={'margin-bottom': '20'}
            ),
            html.Div([
                html.Label('Earnings Query:'),
                html.Button('Submit Earnings Query', id='earnings_query'),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='three columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
		
		html.Div([
            html.Div([
                html.Label('Max Strike Gap:'),
                dcc.Input(
                    id='max_gap',
                    type='number',
                    value=5
                )
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='two columns',
            ),
            html.Div([
                html.Label('DTE Threshold:'),
                dcc.Input(
                    id='dte_thresh',
                    type='number',
                    value=5
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='two columns',
            ),
            html.Div([
                html.Label('Strike Filter Type:'),
                dcc.Input(
                    id='strike_filter',
                    type='text',
                    value='bounds'
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='two columns',
            ),
            
            html.Div([
                html.Label('Moneyness Threshold:'),
                dcc.Input(
                    id='money_thresh',
                    type='number',
                    value=0.1
                )
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='two columns',
            ),
			html.Div([
                html.Label('Strike Adjustment:'),
                dcc.Input(
                    id='bounds_adj',
                    type='number',
                    value=0,
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='two columns',
            ),
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        ################# Earnings DF Layout ########################
        html.Div([
            html.Button('Update Earnings Table', id='earnings_show'),
            dasht.DataTable(
                    # Initialise the rows
                    rows=[{}],
                    row_selectable=True,
                    filterable=True,
                    sortable=True,
                    selected_row_indices=[],
                    id='e_table'
                    ),
            html.Div(id='selected-indexes')
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ),
        
        ################# Input for Condors DF Layout ########################
        html.Div([
            html.H4(
                'Potential Condors',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
                       
            
        html.Div([
            html.Div([
                html.Label('Delta Threshold:'),
                dcc.Input(
                    id='delta_thresh',
                    type='number',
                    value=0.03
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='four columns',
            ),
            html.Div([
                html.Label('Minimum Premium:'),
                dcc.Input(
                    id='minimum_prem',
                    type='number',
                    value=0.15,
                ),
            ],
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='four columns',
            ),
            html.Div([
                html.Label('Risk Reward Threshold:'),
                dcc.Input(
                    id='rr_thresh',
                    type='number',
                    value=0.2,
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
                            
        ################# Condors DF Layout ########################
        
        html.Div([
            html.Button('Update Condors Table', id='condors_show'),
            dasht.DataTable(
                    # Initialise the rows
                    rows=[{}],
                    row_selectable=True,
                    filterable=True,
                    sortable=True,
                    selected_row_indices=[],
                    id='c_table'
                    ),
            html.Div(id='selected-indexes')
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ), 
        
        # Temporary hack for live dataframe caching
        # 'hidden' set to 'loaded' triggers next callback
        html.P(
            hidden='',
            id='raw_container',
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

# Cache raw data
@app.callback(
        Output('raw_container', 'hidden'),
        [Input('earnings_query', 'n_clicks')],
        [State('startdate','date'),
         State('forward_days','value'),
         State('max_gap','value'),
         State('dte_thresh','value'),
         State('strike_filter','value'),
         State('money_thresh','value'),
		 State('bounds_adj','value')])
def cache_earnings(n_clicks, startdate, fwd_days, maxgap, dtethresh,
                   strikefilter, moneythresh, boundsadj):

    global earnings_df, condors_df
    start_date = dt.datetime.strptime(startdate, '%Y-%m-%d')
    earnings_df = earnings(start_date, fwd_days)
    
    condors_df = condor_screener(earnings_df, max_gap = maxgap, dte_thresh = dtethresh, 
                                 money_thresh = moneythresh, delta_thresh = 0.03, 
                                 minimum_prem = 0.1, bounds_adj = boundsadj, 
                                 rr_thresh = 0.1, strike_filter = strikefilter)
    
    print('Loaded raw data')
    return 'loaded'


@app.callback(
        Output('e_table', 'rows'), 
        [Input('earnings_show', 'n_clicks')],
        [State('raw_container', 'hidden')])
def update_e_table(n_clicks, hidden):
    if hidden == 'loaded':
        return earnings_df.to_dict('records')

@app.callback(
        Output('c_table', 'rows'), 
        [Input('condors_show', 'n_clicks')],
        [State('raw_container', 'hidden'),
		 State('delta_thresh','value'),
         State('minimum_prem','value'),
         State('rr_thresh','value')])
def update_c_table(n_clicks, hidden, deltathresh, 
                   minimumprem, rrthresh):
    if hidden == 'loaded':
        filtered_condors = condors_df[(abs(condors_df['Delta']) <= deltathresh) & 
                                      (condors_df['Premium'] >= minimumprem) & 
                                      (condors_df['RiskRewardRatio'] >= rrthresh)]
        return filtered_condors.to_dict('records')

if __name__ == '__main__':
    #app.server.run(debug=True, threaded=True, use_reloader=False)
    app.run_server(port=6050, debug = True)