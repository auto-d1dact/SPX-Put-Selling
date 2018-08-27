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
from py_vollib.black_scholes_merton.implied_volatility import *
from py_vollib.black_scholes_merton.greeks.analytical import *
from data_fetcher_pos import *

# Setup app
# server = flask.Flask(__name__)
# server.secret_key = os.environ.get('secret_key', 'secret')
# app = dash.Dash(__name__, server=server, url_base_pathname='/dash/gallery/volatility-surface', csrf_protect=False)
app = dash.Dash(__name__)
# server = app.server

# Tickers
tickers = [dict(label=str(ticker), value=str(ticker))
           for ticker in tickers]

external_css = ["https://fonts.googleapis.com/css?family=Overpass:300,300i",
                "https://cdn.rawgit.com/plotly/dash-app-stylesheets/dab6f937fd5548cebf4c6dc7e93a10ac438f5efb/dash-technical-charting.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

if 'DYNO' in os.environ:
    app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })
    
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
        
        #### Options Table
        html.Div([
            html.H4(
                'Query Options',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
            
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
                html.Label('DTE UB'),
                dcc.Input(
                    id='dte_ub',
                    type='number',
                    value=50,
                ),
            ],
                className='three columns',
            ),
    
            html.Div([
                html.Label('DTE UB'),
                dcc.Input(
                    id='dte_lb',
                    type='number',
                    value=20,
                ),
            ],
                className='three columns',
            ),
    
            html.Div([
                html.Label('Moneyness'),
                dcc.Input(
                    id='moneyness',
                    type='number',
                    value=0.03,
                ),
            ],
                className='three columns',
            ),
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
    
        html.Div([
                html.Button('Query Yahoo Options', id='query_yahoo'),
                html.Button('Display Queried Options', id='display_table')
            ],
                className='row',
                style={'margin-bottom': '20',
                       'text-align': 'center'}
            ),
            
            
        html.Div([
            html.Label('Delayed Options Data:'),
            dasht.DataTable(
                    # Initialise the rows
                    rows=[{}],
                    row_selectable=True,
                    filterable=True,
                    sortable=True,
                    selected_row_indices=[],
                    id='options_table'
                    ),
            html.Div(id='selected-indexes')
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
                html.Label('Fields'),
                html.P('Contract Indices:')
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='three columns',
            ),
            html.Div([
                html.Label('User Input:'),
                dcc.Input(
                        id='contract_ids',
                        placeholder='Enter contract indices from table above (only spaces and int)',
                        type='text',
                        value=''
                        )
            ],
                className='nine columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        html.Div([
            html.Div([
                html.P('Corresponding Positions:')
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='three columns',
            ),
            html.Div([
                dcc.Input(
                        id='contract_positions',
                        placeholder='Enter positions corresponding to contracts (only spaces and int)',
                        type='text',
                        value=''
                        )
            ],
                className='nine columns',
            )
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        
        html.Div([
            html.Div([
                html.P('Number of Shares:')
            ],  
                style={'text-align': 'center',
                       'vertical-align': 'middle',
                       'display': 'table-cell'},
                className='three columns',
            ),
            html.Div([
                dcc.Input(
                    id='number_of_shares',
                    type='number',
                    value=0,
                ),
            ],
                className='nine columns',
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
                className='three columns',
                style={'text-align': 'center'}
            ),
            html.Div([
                html.Label('Interest Rate:'),
                dcc.Input(
                    id='interest_rate',
                    type='number',
                    value=0.0193
                ),
            ],
                className='two columns',
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
                className='three columns',
                style={'text-align': 'center'}
            ),
            
            html.Div([
                html.Label('Used Price:'),
                dcc.RadioItems(
                    id='price_selector',
                    options=[
                        {'label': 'Mid', 'value': 'Mid'},
                        {'label': 'Last', 'value': 'Last'},
                    ],
                    value='Mid',
                    labelStyle={'display': 'inline-block'},
                ),
            ],
                className='two columns',
            ),
            html.Div([
                html.Label('Day Format:'),
                dcc.RadioItems(
                    id='date_format',
                    options=[
                        {'label': 'Calendar', 'value': 'calendar'},
                        {'label': 'Trading', 'value': 'trading'},
                    ],
                    value='trading',
                    labelStyle={'display': 'inline-block'},
                ),
            ],
                className='two columns',
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
                className='twelve columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
            
        html.Div([
            html.Div([
                dcc.Graph(id='return_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='twelve columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
            
        html.Div([
            html.Div([
                dcc.Graph(id='delta_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='twelve columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
            
        html.Div([
            html.Div([
                dcc.Graph(id='gamma_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='twelve columns'
            )   
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        
        html.Div([
            html.Div([
                dcc.Graph(id='theta_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='twelve columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
            
        html.Div([
            html.Div([
                dcc.Graph(id='vega_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='twelve columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
            
        html.Div([
            html.Div([
                dcc.Graph(id='rho_surface', style={'max-height': '600', 'height': '60vh'}),
            ],
                className='twelve columns'
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
            #hidden='',
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
        [Input('query_yahoo', 'n_clicks')],
        [State('ticker_dropdown','value'),
         State('dte_ub','value'),
         State('dte_lb','value'),
         State('moneyness','value')])
def cache_raw_data_options(n_clicks, ticker, dte_ub, dte_lb, moneyness):

    global yahoo_data
    yahoo_data = all_options(ticker, dte_ub, dte_lb, moneyness = 0.03)
    print('Loaded raw data')
    return 'loaded'


@app.callback(Output('options_table', 'rows'),
              [Input('display_table', 'n_clicks')],
              [State('raw_container','hidden'),
               State('price_selector','value'),
               State('date_format','value'),
               State('interest_rate', 'value')])
def update_options_table(n_clicks, hidden,prem_price_use,day_format,interest_rate):
    
    if hidden == 'loaded':
        table = greek_calc(yahoo_data, prem_price_use, day_format, interest_rate).reset_index()
        return table.to_dict('records')

#
@app.callback(
        Output('filtered_container', 'hidden'),
        [Input('analysis_button', 'n_clicks')],
        [State('interest_rate', 'value'),
         State('price_changes', 'value'),
         State('vol_range', 'value'),
         State('dte_range', 'value'),
         State('skew', 'value'),
         State('spacing','value'),
         State('contract_ids','value'),
         State('contract_positions','value'),
         State('number_of_shares','value'),
         State('price_selector','value'),
         State('date_format','value')])
def cache_raw_data_sim(n_clicks, interest_rate, price_range, vol_range, dte_range, skew_type,
                       spacing, contract_ids, contract_pos, shares, price_selector,
                       date_format):

    global pnl_outmeshes, pct_outmeshes, delta_outmeshes, gamma_outmeshes, theta_outmeshes, vega_outmeshes, rho_outmeshes
    global priceGrid, dteGrid, v_changes, df
    
    day_spacing = dte_range[1] - dte_range[0] + 1
    
    indices = [int(x) for x in contract_ids.split(' ')]
    positions = [int(x) for x in contract_pos.split(' ')]
    
    price_axis = np.linspace(price_range[0], price_range[1], spacing)
    dte_axis = np.linspace(dte_range[0], dte_range[1], day_spacing)
    v_changes = np.linspace(vol_range[0], vol_range[1], 3)
    
    priceGrid, dteGrid = np.meshgrid(price_axis, dte_axis)
        
    # Creating Mesh Grids
    
    pnl_outmeshes= []
    pct_outmeshes = []
    delta_outmeshes = []
    gamma_outmeshes = []
    theta_outmeshes = []
    vega_outmeshes = []
    rho_outmeshes = []
    
    for v_change in v_changes:
    
        pnl_out_values_lst = []
        pct_out_values_lst = []
        delta_out_values_lst = []
        gamma_out_values_lst = []
        theta_out_values_lst = []
        vega_out_values_lst = []
        rho_out_values_lst = []
        for p_arrays, d_arrays in zip(priceGrid, dteGrid):
            pnl_current_values_sublist = []
            pct_current_values_sublist = []
            delta_current_values_sublist = []
            gamma_current_values_sublist = []
            theta_current_values_sublist = []
            vega_current_values_sublist = []
            rho_current_values_sublist = []
    
            for price_delta, dte_delta in zip(p_arrays, d_arrays):
                current_sim = position_sim(yahoo_data.loc[indices], positions, shares, price_delta, 
                                           v_change, dte_delta,
                                           'All', skew_type, price_selector, date_format,
                                           interest_rate)
                pnl_current_values_sublist.append(current_sim['PnL'].values[0])
                pct_current_values_sublist.append(current_sim['Percent Return'].values[0])
                delta_current_values_sublist.append(current_sim['Simulated Delta'].values[0])
                gamma_current_values_sublist.append(current_sim['Simulated Gamma'].values[0])
                theta_current_values_sublist.append(current_sim['Simulated Theta'].values[0])
                vega_current_values_sublist.append(current_sim['Simulated Vega'].values[0])
                rho_current_values_sublist.append(current_sim['Simulated Rho'].values[0])
    
    
            pnl_out_values_lst.append(pnl_current_values_sublist)
            pct_out_values_lst.append(pct_current_values_sublist)
            delta_out_values_lst.append(delta_current_values_sublist)
            gamma_out_values_lst.append(gamma_current_values_sublist)
            theta_out_values_lst.append(theta_current_values_sublist)
            vega_out_values_lst.append(vega_current_values_sublist)
            rho_out_values_lst.append(rho_current_values_sublist)
    
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
        
        rho_out_values_mesh = np.array(rho_out_values_lst)
        rho_outmeshes.append(rho_out_values_mesh)
    
    print('Loaded raw data')
    return 'loaded'
##
## Displaying outputs
#
##    
## Make main surface plot
@app.callback(Output('pnl_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def pnl_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pnl_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pnl_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pnl_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='PnL Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        aspectmode = 'manual',
                        aspectratio = dict(x = 2,
                                           y = 2,
                                           z = 1),
                        camera = dict(up = dict(x = 0,
                                                y = 0,
                                                z = 1),
                                      center = dict(x = 0,
                                                    y = 0,
                                                    z = 0),
                                      eye = dict(x = 1,
                                                 y = 1,
                                                 z = 0.5)),
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
        surface1 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pct_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pct_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = pct_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Return Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        aspectmode = 'manual',
                        aspectratio = dict(x = 2,
                                           y = 2,
                                           z = 1),
                        camera = dict(up = dict(x = 0,
                                                y = 0,
                                                z = 1),
                                      center = dict(x = 0,
                                                    y = 0,
                                                    z = 0),
                                      eye = dict(x = 1,
                                                 y = 1,
                                                 z = 0.5)),
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
        surface1 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = delta_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = delta_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = delta_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Delta Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        aspectmode = 'manual',
                        aspectratio = dict(x = 2,
                                           y = 2,
                                           z = 1),
                        camera = dict(up = dict(x = 0,
                                                y = 0,
                                                z = 1),
                                      center = dict(x = 0,
                                                    y = 0,
                                                    z = 0),
                                      eye = dict(x = 1,
                                                 y = 1,
                                                 z = 0.5)),
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
        surface1 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = gamma_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = gamma_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = gamma_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Gamma Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        aspectmode = 'manual',
                        aspectratio = dict(x = 2,
                                           y = 2,
                                           z = 1),
                        camera = dict(up = dict(x = 0,
                                                y = 0,
                                                z = 1),
                                      center = dict(x = 0,
                                                    y = 0,
                                                    z = 0),
                                      eye = dict(x = 1,
                                                 y = 1,
                                                 z = 0.5)),
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
        surface1 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = theta_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = theta_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = theta_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Theta Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        aspectmode = 'manual',
                        aspectratio = dict(x = 2,
                                           y = 2,
                                           z = 1),
                        camera = dict(up = dict(x = 0,
                                                y = 0,
                                                z = 1),
                                      center = dict(x = 0,
                                                    y = 0,
                                                    z = 0),
                                      eye = dict(x = 1,
                                                 y = 1,
                                                 z = 0.5)),
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
def vega_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = vega_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = vega_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = vega_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Vega Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        aspectmode = 'manual',
                        aspectratio = dict(x = 2,
                                           y = 2,
                                           z = 1),
                        camera = dict(up = dict(x = 0,
                                                y = 0,
                                                z = 1),
                                      center = dict(x = 0,
                                                    y = 0,
                                                    z = 0),
                                      eye = dict(x = 1,
                                                 y = 1,
                                                 z = 0.5)),
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
    
# Make main surface plot
@app.callback(Output('rho_surface', 'figure'),
              [Input('display_button', 'n_clicks')],
              [State('filtered_container','hidden')])
def rho_surface_plot(n_clicks, hidden):

    if hidden == 'loaded':
        surface1 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = rho_outmeshes[0],
                              name = v_changes[0])

        surface2 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = rho_outmeshes[1],
                              name = v_changes[1])
    
        surface3 = go.Surface(x = (priceGrid + 1)*yahoo_data['Underlying_Price'].values[0], 
                              y = dteGrid, 
                              z = rho_outmeshes[2], 
                              name = v_changes[2])

        layout = go.Layout(
                    title='Rho Plot',
                    autosize=True,
                    showlegend = False,
                    scene=dict(
                        aspectmode = 'manual',
                        aspectratio = dict(x = 2,
                                           y = 2,
                                           z = 1),
                        camera = dict(up = dict(x = 0,
                                                y = 0,
                                                z = 1),
                                      center = dict(x = 0,
                                                    y = 0,
                                                    z = 0),
                                      eye = dict(x = 1,
                                                 y = 1,
                                                 z = 0.5)),
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
                            title = 'Rho',
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
	app.run_server(port = 5050, debug = True, threaded=True, use_reloader=False)
