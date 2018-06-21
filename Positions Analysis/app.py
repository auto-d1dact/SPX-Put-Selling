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
from py_vollib.black_scholes_merton.implied_volatility import *
from py_vollib.black_scholes_merton.greeks.analytical import *
from data_fetcher_pos import *


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

# Tickers
tickers = [dict(label=str(ticker), value=str(ticker))
           for ticker in tickers]

# Labels
price_change_labels = [(lambda x: '{}'.format(np.round(x, 
                        2)) if int(np.round(x, 
                          2)*100)%5 == 0 else (''))(x) for x in np.arange(-0.51, 0.51, 0.01)]

dfe_labels = [(lambda x: '{}'.format(x) if x%5 == 0 else (''))(x) for x in range(0,101,1)]


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
                'Risk Analysis of Positions',
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
        
        ################# Input for Summary Layout ########################
        html.Div([
            html.Div([
                html.Label('Select ticker:'),
                dcc.Dropdown(
                    id='ticker_dropdown',
                    options=tickers,
                    value='SPY',
                )
            ],
                className='three columns',
            ),
            html.Div([
                html.Label('DTE:'),
                dcc.Input(
                    id='ticker_dte',
                    type='number',
                    value=20,
                ),
            ],
                className='three columns',
            ),
            html.Div([
                html.Label('Moneyness:'),
                dcc.Input(
                    id='moneyness_filter',
                    type='number',
                    value=0.1,
                ),
            ],
                className='three columns',
            ),
            html.Div([
                html.Label('Query Summary:'),
                html.Button('Submit Query', id='query_button'),
                html.Label('Display Summary:'),
                html.Button('Update Tables', id='show_button'),
            ],
                className='three columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        ################# Summaries Layout ########################
        html.Div([
            html.H4(
                'Call Summary Table',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
            html.Div(id='call_summary',
                     children ='Wait for update to display table',
                     style={'text-align': 'center',
                            'font-size': '75%'})
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ),   
            
        html.Div([
            html.H4(
                'Put Summary Table',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
            html.Div(id='put_summary',
                     children ='Wait for update to display table',
                     style={'text-align': 'center',
                            'font-size': '75%'})
        ],
            className='row',
            style={'margin-bottom': '20',
                   'text-align': 'center'}
        ), 
        
        ################# Input for Positions Entry Layout ########################
        html.Div([
            html.H4(
                'Position Entry',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
            
        html.Div([
            html.Div([
                html.Label('Legs:'),
                html.P('Leg 1:')
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='one columns',
            ),
            html.Div([
                html.Label('Expiry:'),
                dcc.DatePickerSingle(
                    id='expiry1',
                    date=dt.date.today(),
                ),
            ],
                className='two columns',
            ),
            html.Div([
                html.Label('Type:'),
                dcc.Dropdown(
                    id='type1',
                    options=[{'label': 'c', 'value': 'c'},
                             {'label': 'p', 'value': 'p'},
                             {'label': 'none', 'value': 'na'}],
                    value='c',
                )
            ],
                className='two columns',
            ),
            html.Div([
                html.Label('Strike:'),
                dcc.Input(
                    id='strike1',
                    type='number'
                ),
            ],
                className='two columns',
            ),
            html.Div([
                html.Label('Int. Rate:'),
                dcc.Input(
                    id='interest1',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                html.Label('Price:'),
                dcc.Input(
                    id='price1',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                html.Label('Position:'),
                dcc.Input(
                    id='position1',
                    type='number',
                    value=0,
                ),
            ],
                className='one columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        html.Div([
            html.Div([
                html.P('Leg 2:')
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='one columns',
            ),
            html.Div([
                dcc.DatePickerSingle(
                    id='expiry2',
                    date=dt.date.today(),
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Dropdown(
                    id='type2',
                    options=[{'label': 'c', 'value': 'c'},
                             {'label': 'p', 'value': 'p'},
                             {'label': 'none', 'value': 'na'}],
                    value='c',
                )
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='strike2',
                    type='number'
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='interest2',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='price2',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='position2',
                    type='number',
                    value=0,
                ),
            ],
                className='one columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        html.Div([
            html.Div([
                html.P('Leg 3:')
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='one columns',
            ),
            html.Div([
                dcc.DatePickerSingle(
                    id='expiry3',
                    date=dt.date.today(),
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Dropdown(
                    id='type3',
                    options=[{'label': 'c', 'value': 'c'},
                             {'label': 'p', 'value': 'p'},
                             {'label': 'none', 'value': 'na'}],
                    value='c',
                )
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='strike3',
                    type='number'
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='interest3',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='price3',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='position3',
                    type='number',
                    value=0,
                ),
            ],
                className='one columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        html.Div([
            html.Div([
                html.P('Leg 4:')
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='one columns',
            ),
            html.Div([
                dcc.DatePickerSingle(
                    id='expiry4',
                    date=dt.date.today(),
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Dropdown(
                    id='type4',
                    options=[{'label': 'c', 'value': 'c'},
                             {'label': 'p', 'value': 'p'},
                             {'label': 'none', 'value': 'na'}],
                    value='c',
                )
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='strike4',
                    type='number'
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='interest4',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='price4',
                    type='number',
                    value=0,
                ),
            ],
                className='two columns',
            ),
            html.Div([
                dcc.Input(
                    id='position4',
                    type='number',
                    value=0,
                ),
            ],
                className='one columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        #################### Analsys Tools ##########################
        html.Div([
            html.H4(
                'Analysis Tools',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
        
        html.Div([
            html.Label('Price Change Slider:',
                       style={'text-align': 'left'}),
            dcc.RangeSlider(
                    id='price_changes',
                    marks={k: v for k, v in zip(np.arange(-0.51,0.51,0.01),price_change_labels)},
                    min=-0.5,
                    max=0.5,
                    step=0.01,
                    value=[-0.05, 0.05]
                    )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
                
        html.Div([
            html.Label('Volatility 3-Surface Range:',
                       style={'text-align': 'left'}),
            dcc.RangeSlider(
                    id='vol_range',
                    marks={k: v for k, v in zip(np.arange(-0.51,0.51,0.01),price_change_labels)},
                    min=-0.5,
                    max=0.5,
                    step=0.01,
                    value=[0.0, 0.05]
                    )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        
        html.Div([
            html.Label('Days from Expiration Range:',
                       style={'text-align': 'left'}),
            dcc.RangeSlider(
                    id='dte_range',
                    marks={k: v for k, v in zip(range(101),dfe_labels)},
                    min=0,
                    max=100,
                    step=0.01,
                    value=[0, 20]
                    )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
                            
        html.Div([
            html.Div([
                html.Label('Skew Type:'),
                dcc.Dropdown(
                    id='skew',
                    options=[{'label': 'flat', 'value': 'flat'},
                             {'label': 'right', 'value': 'right'},
                             {'label': 'left', 'value': 'left'},
                             {'label': 'smile', 'value': 'smile'}],
                    value='flat',
                )
            ],
                className='four columns',
                style={'text-align': 'center'}
            ),
            html.Div([
                html.Label('Underlying Price:'),
                dcc.Input(
                    id='underlying',
                    type='number'
                ),
            ],
                className='four columns',
                style={'text-align': 'center'}
            ),
            html.Div([
                html.Label('Price Spacing for Surface:'),
                dcc.Input(
                    id='spacing',
                    type='number',
                    value=0,
                ),
            ],
                className='four columns',
                style={'text-align': 'center'}
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        html.Div([
                html.Button('Run Analysis', id='analysis_button'),
                html.Button('Update Surfaces', id='display_button')
            ],
                className='row',
                style={'margin-bottom': '20',
                       'text-align': 'center'}
            ),

        ################################ Surface Plots Layout #########################
       
        html.Div([
            html.Div([
                dcc.Graph(id='pnl_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='six columns'
            ),
            html.Div([
                dcc.Graph(id='return_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='six columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
            
        html.Div([
            html.Div([
                dcc.Graph(id='delta_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='six columns'
            ),
            html.Div([
                dcc.Graph(id='gamma_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='six columns'
            )   
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        
        html.Div([
            html.Div([
                dcc.Graph(id='theta_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='six columns'
            ),
            html.Div([
                dcc.Graph(id='vega_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='six columns'
            )
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
# Cache raw data
@app.callback(
        Output('raw_container', 'hidden'),
        [Input('query_button', 'n_clicks')],
        [State('ticker_dropdown','value'),
         State('moneyness_filter','value'),
         State('ticker_dte','value')])
def cache_raw_data_options(n_clicks, ticker, moneyness, dte):

    global calls, puts
    calls, puts = option_filter(ticker, moneyness, dte)
    columns = list(calls.columns)
    calls['Strike'] = calls.index
    puts['Strike'] = puts.index
    calls = np.round(calls[['Strike'] + columns],2)
    puts = np.round(puts[['Strike'] + columns],2)
    print('Loaded raw data')
    return 'loaded'

@app.callback(
        Output('filtered_container', 'hidden'),
        [Input('analysis_button', 'n_clicks')],
        [State('expiry1','date'),
         State('type1','value'),
         State('strike1','value'),
         State('interest1','value'),
         State('price1','value'),
         State('position1', 'value'),
         State('expiry2','date'),
         State('type2','value'),
         State('strike2','value'),
         State('interest2','value'),
         State('price2','value'),
         State('position2', 'value'),
         State('expiry3','date'),
         State('type3','value'),
         State('strike3','value'),
         State('interest3','value'),
         State('price3','value'),
         State('position3', 'value'),
         State('expiry4','date'),
         State('type4','value'),
         State('strike4','value'),
         State('interest4','value'),
         State('price4','value'),
         State('position4', 'value'),
         State('underlying', 'value'),
         State('price_changes', 'value'),
         State('vol_range', 'value'),
         State('dte_range', 'value'),
         State('skew', 'value'),
         State('spacing','value')])
def cache_raw_data_sim(n_clicks, expiry1, type1, strike1, interest1, price1, position1,
                       expiry2, type2, strike2, interest2, price2, position2,
                       expiry3, type3, strike3, interest3, price3, position3,
                       expiry4, type4, strike4, interest4, price4, position4,
                       underlying, price_range, vol_range, dte_range, skew_type,
                       spacing):

    global pnl_outmeshes, pct_outmeshes, delta_outmeshes, gamma_outmeshes, theta_outmeshes, vega_outmeshes
    global priceGrid, dteGrid, v_changes, df
    
    day_spacing = dte_range[1] - dte_range[0] + 1
    
    price_axis = np.linspace(price_range[0], price_range[1], spacing)
    dte_axis = np.linspace(dte_range[0], dte_range[1], day_spacing)
    v_changes = np.linspace(vol_range[0], vol_range[1], 3)
    
    priceGrid, dteGrid = np.meshgrid(price_axis, dte_axis)
    
    # Setting up data feed
    dtes = [(dt.datetime.strptime(expiry1, '%Y-%m-%d').date() - dt.date.today()).days,
            (dt.datetime.strptime(expiry2, '%Y-%m-%d').date() - dt.date.today()).days,
            (dt.datetime.strptime(expiry3, '%Y-%m-%d').date() - dt.date.today()).days,
            (dt.datetime.strptime(expiry4, '%Y-%m-%d').date() - dt.date.today()).days]
    types = [type1, type2, type3, type4]
    strikes = [strike1, strike2, strike3, strike4]
    interests = [interest1, interest2, interest3, interest4]
    prices = [price1, price2, price3, price4]
    positions = [position1, position2, position3, position4]
    underlyings = [underlying, underlying, underlying, underlying]
    df = pd.DataFrame({'DTE': dtes, 'Type': types, 'Strike': strikes,
                       'Cost': prices, 'Underlying_Price': underlyings, 
                       'Interest': interests, 'Pos': positions}, index = range(4))
    df = df[df['Pos'] != 0]
    positions = df['Pos'].tolist()
                
    sigmas = []
    for premium, strike, time_to_expiration, flag, interest in zip(df['Cost'], 
                                                                   df['Strike'], 
                                                                   df['DTE'],
                                                                   df['Type'],
                                                                   df['Interest']):
        # Constants
        P = premium
        S = df['Underlying_Price'].values[0]
        K = strike
        t = time_to_expiration/float(365)
        r = interest / 100
        q = 0 / 100
        try:
            sigma = py_vollib.black_scholes_merton.implied_volatility.implied_volatility(P, S, K, t, r, q, flag)
            sigmas.append(sigma)
        except:
            sigma = 0.0
            sigmas.append(sigma)
    
    df['Calc IV'] = sigmas
    
    # Creating Mesh Grids
    
    pnl_outmeshes= []
    pct_outmeshes = []
    delta_outmeshes = []
    gamma_outmeshes = []
    theta_outmeshes = []
    vega_outmeshes = []
    
    for v_change in v_changes:
    
        pnl_out_values_lst = []
        pct_out_values_lst = []
        delta_out_values_lst = []
        gamma_out_values_lst = []
        theta_out_values_lst = []
        vega_out_values_lst = []
        for p_arrays, d_arrays in zip(priceGrid, dteGrid):
            pnl_current_values_sublist = []
            pct_current_values_sublist = []
            delta_current_values_sublist = []
            gamma_current_values_sublist = []
            theta_current_values_sublist = []
            vega_current_values_sublist = []
            
            for price_delta, dte_delta in zip(p_arrays, d_arrays):
                current_sim = position_sim(df, positions, price_delta, 
                                           v_change, dte_delta, 'Calc IV',
                                           'All', skew_type)
                pnl_current_values_sublist.append(current_sim['PnL'].values[0])
                pct_current_values_sublist.append(current_sim['Percent Return'].values[0])
                delta_current_values_sublist.append(current_sim['Simulated Delta'].values[0])
                gamma_current_values_sublist.append(current_sim['Simulated Gamma'].values[0])
                theta_current_values_sublist.append(current_sim['Simulated Theta'].values[0])
                vega_current_values_sublist.append(current_sim['Simulated Vega'].values[0])
                
                
            pnl_out_values_lst.append(pnl_current_values_sublist)
            pct_out_values_lst.append(pct_current_values_sublist)
            delta_out_values_lst.append(delta_current_values_sublist)
            gamma_out_values_lst.append(gamma_current_values_sublist)
            theta_out_values_lst.append(theta_current_values_sublist)
            vega_out_values_lst.append(vega_current_values_sublist)
            
        pnl_out_values_mesh = np.array(pnl_out_values_lst)
        pnl_outmeshes.append(pnl_out_values_mesh)
        
        pct_out_values_mesh = np.array(pct_out_values_lst)
        pct_outmeshes.append(pct_out_values_mesh)
        
        delta_out_values_mesh = np.array(delta_out_values_lst)
        delta_outmeshes.append(delta_out_values_mesh)
        
        gamma_out_values_mesh = np.array(gamma_out_values_lst)
        gamma_outmeshes.append(gamma_out_values_mesh)
        
        theta_out_values_mesh = np.array(theta_out_values_lst)
        theta_outmeshes.append(theta_out_values_mesh)
        
        vega_out_values_mesh = np.array(vega_out_values_lst)
        vega_outmeshes.append(vega_out_values_mesh)
    
    print('Loaded raw data')
    return 'loaded'

# Displaying outputs

@app.callback(
    Output('call_summary', 'children'),
    [Input('show_button', 'n_clicks')],
    [State('raw_container','hidden')])
def update_output_calls(n_clicks, hidden):
    if hidden == 'loaded':
        return generate_table(calls)
    
@app.callback(
    Output('put_summary', 'children'),
    [Input('show_button', 'n_clicks')],
    [State('raw_container','hidden')])
def update_output_calls(n_clicks, hidden):
    if hidden == 'loaded':
        return generate_table(puts)
    
#    
#    
# Make main surface plot
@app.callback(Output('pnl_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def pnl_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pnl_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pnl_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pnl_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='PnL Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        xaxis=dict(
                            title='Underlying Price',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        yaxis=dict(
                            title='DTE Change',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        zaxis=dict(
                            title = 'PnL',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        )
                    )
                )

        data = [surface1, surface2, surface3]
        figure = dict(data=data, layout=layout)
        return figure

# Make main surface plot
@app.callback(Output('return_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def pct_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pct_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pct_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pct_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Return Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        xaxis=dict(
                            title='Underlying Price',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        yaxis=dict(
                            title='DTE Change',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        zaxis=dict(
                            title = 'Percent Return',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        )
                    )
                )

        data = [surface1, surface2, surface3]
        figure = dict(data=data, layout=layout)
        return figure

# Make main surface plot
@app.callback(Output('delta_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def delta_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = delta_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = delta_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = delta_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Delta Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        xaxis=dict(
                            title='Underlying Price',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        yaxis=dict(
                            title='DTE Change',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        zaxis=dict(
                            title = 'Delta',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        )
                    )
                )

        data = [surface1, surface2, surface3]
        figure = dict(data=data, layout=layout)
        return figure
    
# Make main surface plot
@app.callback(Output('gamma_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def gamma_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = gamma_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = gamma_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = gamma_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Gamma Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        xaxis=dict(
                            title='Underlying Price',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        yaxis=dict(
                            title='DTE Change',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        zaxis=dict(
                            title = 'Gamma',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        )
                    )
                )

        data = [surface1, surface2, surface3]
        figure = dict(data=data, layout=layout)
        return figure

# Make main surface plot
@app.callback(Output('theta_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def theta_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = theta_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = theta_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = theta_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Theta Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        xaxis=dict(
                            title='Underlying Price',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        yaxis=dict(
                            title='DTE Change',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        zaxis=dict(
                            title = 'Theta',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        )
                    )
                )

        data = [surface1, surface2, surface3]
        figure = dict(data=data, layout=layout)
        return figure

# Make main surface plot
@app.callback(Output('vega_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def theta_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = vega_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = vega_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*df['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = vega_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Vega Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        xaxis=dict(
                            title='Underlying Price',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        yaxis=dict(
                            title='DTE Change',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        ),
                        zaxis=dict(
                            title = 'Vega',
                            gridcolor='rgb(255, 255, 255)',
                            zerolinecolor='rgb(255, 255, 255)',
                            showbackground=True,
                            backgroundcolor='rgb(230, 230,230)'
                        )
                    )
                )

        data = [surface1, surface2, surface3]
        figure = dict(data=data, layout=layout)
        return figure


if __name__ == '__main__':
    #app.server.run(debug=True, threaded=True, use_reloader=False)
    app.run_server(debug = True)