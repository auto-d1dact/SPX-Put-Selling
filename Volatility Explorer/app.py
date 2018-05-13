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
import dash_table_experiments as dtable

from tickers import tickers
from data_fetcher import get_time_delta, get_raw_data, get_filtered_data, historical_data


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
                'Volatility Explorer for Day Trading Options',
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
            html.Div([
                html.Label('Select ticker:'),
                dcc.Dropdown(
                    id='ticker_dropdown',
                    options=tickers,
                    value='SPY',
                ),
                html.Div(id='last_price'),
                html.Div(id='daily_vol'),
                html.Div(id='intra_vol'),
                html.Div(id='ovrnt_vol')
            ],
                className='six columns',
            ),
            html.Div([
                html.Label('Option settings:'),
                dcc.RadioItems(
                    id='market_selector',
                    options=[
                        {'label': 'Market', 'value': 'market'},
                        {'label': 'Last', 'value': 'last'},
                    ],
                    value='market',
                    labelStyle={'display': 'inline-block'},
                ),
            ],
                className='two columns',
            ),
            html.Div([
                html.Div([
                    html.Label('Price threshold:'),
                    dcc.Slider(
                        id='price_slider',
                        min=0,
                        max=200,
                        value=20,
                    ),
                ]),
                html.Div([
                    html.Label('Volume threshold:'),
                    dcc.Slider(
                        id='volume_slider',
                        min=0,
                        max=10,
                        value=1,
                    )
                ]),
                html.Div([
                    html.Label('Expiry threshold:'),
                    dcc.Slider(
                        id='expiry_slider',
                        min=0,
                        max=300,
                        value=30,
                    )
                ]),
                html.Div([
                    html.Label('Historical Number of Days:'),
                    dcc.Slider(
                        id='numdays_slider',
                        min=2,
                        max=500,
                        value=100,
                    )
                ]),
                html.Div([
                    html.Label('HV Roll Days:'),
                    dcc.Slider(
                        marks={i: '{}'.format(i) for i in range(5,30)},
                        id='hvroll_slider',
                        min=5,
                        max=30,
                        value=20,
                    )
                ]),
            ],
                className='four columns'
            ),
        ],
            className='row',
            style={'margin-bottom': '10'}
        ),
        html.Div([
            html.Div([
                html.Label('Implied volatility settings:'),
                html.Div([
                    dcc.RadioItems(
                        id='iv_selector',
                        options=[
                            {'label': 'Calculate IV ', 'value': True},
                            {'label': 'Use given IV ', 'value': False},
                        ],
                        value=True,
                        labelStyle={'display': 'inline-block'},
                    ),
                    dcc.RadioItems(
                        id='calendar_selector',
                        options=[
                            {'label': 'Trading calendar ', 'value': True},
                            {'label': 'Annual calendar ', 'value': False},
                        ],
                        value=True,
                        labelStyle={'display': 'inline-block'},
                    )
                ],
                    style={'display': 'inline-block', 'margin-right': '10', 'margin-bottom': '10'}
                ),
                html.Div([
                    html.Div([
                        html.Label('Risk-free rate (%)'),
                        dcc.Input(
                            id='rf_input',
                            placeholder='Risk-free rate',
                            type='number',
                            value='0.0',
                            style={'width': '125'}
                        )
                    ],
                        style={'display': 'inline-block'}
                    ),
                    html.Div([
                        html.Label('Dividend rate (%)'),
                        dcc.Input(
                            id='div_input',
                            placeholder='Dividend interest rate',
                            type='number',
                            value='0.0',
                            style={'width': '125'}
                        )
                    ],
                        style={'display': 'inline-block'}
                    ),
                ],
                    style={'display': 'inline-block', 'position': 'relative', 'bottom': '10'}
                )
            ],
                className='six columns',
                style={'display': 'inline-block'}
            ),
            html.Div([
                html.Label('Chart settings:'),
                dcc.RadioItems(
                    id='log_selector',
                    options=[
                        {'label': 'Log surface', 'value': 'log'},
                        {'label': 'Linear surface', 'value': 'linear'},
                    ],
                    value='log',
                    labelStyle={'display': 'inline-block'}
                ),
                dcc.Checklist(
                    id='graph_toggles',
                    options=[
                        {'label': 'Flat shading', 'value': 'flat'},
                        {'label': 'Discrete contour', 'value': 'discrete'},
                        {'label': 'Error bars', 'value': 'box'},
                        {'label': 'Lock camera', 'value': 'lock'}
                    ],
                    values=['flat', 'box', 'lock'],
                    labelStyle={'display': 'inline-block'}
                )
            ],
                className='six columns'
            ),
        ],
            className='row'
        ),
        html.Div([
            dcc.Graph(id='iv_surface_call', style={'max-height': '600', 'height': '60vh'}),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            dcc.Graph(id='iv_surface_put', style={'max-height': '600', 'height': '60vh'}),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            dcc.Graph(id='hv_line_plot', style={'max-height': '600', 'height': '60vh'}),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            html.Div([
                dcc.Graph(id='std_historical_plot', style={'max-height': '400', 'height': '40vh'}),
            ],
                className='six columns'
            ),
            html.Div([
                dcc.Graph(id='hv_std_hist', style={'max-height': '400', 'height': '40vh'}),
            ],
                className='six columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            html.Div([
                dcc.Graph(id='iv_scatter_call', style={'max-height': '400', 'height': '40vh'}),
            ],
                className='six columns'
            ),
            html.Div([
                dcc.Graph(id='iv_scatter_put', style={'max-height': '400', 'height': '40vh'}),
            ],
                className='six columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
        html.Div([
            html.Div([
                dcc.Graph(id='iv_heatmap_call', style={'max-height': '400', 'height': '40vh'}),
            ],
                className='six columns'
            ),
            html.Div([
                dcc.Graph(id='iv_heatmap_put', style={'max-height': '400', 'height': '40vh'}),
            ],
                className='six columns'
            )
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


# Cache raw data
@app.callback(Output('raw_container', 'hidden'),
              [Input('ticker_dropdown', 'value')])
def cache_raw_data(ticker):

    global raw_data
    raw_data = get_raw_data(ticker)
    print('Loaded raw data')

    return 'loaded'


# Cache filtered data
@app.callback(Output('filtered_container', 'hidden'),
              [Input('raw_container', 'hidden'),
               Input('market_selector', 'value'),
               Input('ticker_dropdown', 'value'),
               Input('price_slider', 'value'),
               Input('volume_slider', 'value'),
               Input('expiry_slider', 'value'),
               Input('numdays_slider', 'value'),
               Input('hvroll_slider', 'value'),
               Input('iv_selector', 'value'),
               Input('calendar_selector', 'value'),
               Input('rf_input', 'value'),
               Input('div_input', 'value')])  # To be split
def cache_filtered_data(hidden, market, stock_ticker,
                        above_below, volume_threshold, expiration_threshold,
                        number_of_days, hv_rolldays,
                        calculate_iv, trading_calendar,
                        rf_interest_rate, dividend_rate):

    if hidden == 'loaded':
        
        # Options Data Call
        s_c, p_c, i_c = get_filtered_data(raw_data, calculate_iv=calculate_iv,
                                          call=True, put=False,
                                          above_below=float(above_below),
                                          volume_threshold=float(volume_threshold),
                                          rf_interest_rate=float(rf_interest_rate),
                                          dividend_rate=float(dividend_rate),
                                          trading_calendar=trading_calendar,
                                          market=market,
                                          days_to_expiry=int(expiration_threshold))
        
        s_p, p_p, i_p = get_filtered_data(raw_data, calculate_iv=calculate_iv,
                                          call=False, put=True,
                                          above_below=float(above_below),
                                          volume_threshold=float(volume_threshold),
                                          rf_interest_rate=float(rf_interest_rate),
                                          dividend_rate=float(dividend_rate),
                                          trading_calendar=trading_calendar,
                                        market=market,
                                        days_to_expiry=int(expiration_threshold))

        df_call = pd.DataFrame([s_c, p_c, i_c]).T
        df_put = pd.DataFrame([s_p, p_p, i_p]).T
        # Stock Price Calls
        historical = historical_data(stock_ticker, 
                                     day_number = number_of_days, 
                                     rolling_window = hv_rolldays, 
                                     outsize = 'full')
#        
        global filtered_data_call
        global filtered_data_put
        global hist_data
        
        filtered_data_call = df_call[df_call[2] > 0.0001]  # Filter invalid calculations with abnormally low IV
        filtered_data_put = df_put[df_put[2] > 0.0001]
        hist_data = historical[['daily_ann', 'intra_ann', 'ovrnt_ann',
                                'daily_dollar_std', 'daily_dollar_std_direction',
                                'close']]
        
        print('Loaded filtered data')

        return 'loaded'


# Make main surface plot
@app.callback(Output('iv_surface_call', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('log_selector', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('iv_surface_call', 'relayoutData')])
def make_call_surface_plot(hidden, ticker, log_selector, graph_toggles,
                           graph_toggles_state, iv_surface_layout):

    if hidden == 'loaded':

        if 'flat' in graph_toggles:
            flat_shading = True
        else:
            flat_shading = False

        trace1 = {
            "type": "mesh3d",
            'x': filtered_data_call[0],
            'y': filtered_data_call[1],
            'z': filtered_data_call[2],
            'intensity': filtered_data_call[2],
            'autocolorscale': False,
            "colorscale": [
                [0, "rgb(244,236,21)"], [0.3, "rgb(249,210,41)"], [0.4, "rgb(134,191,118)"], [
                    0.5, "rgb(37,180,167)"], [0.65, "rgb(17,123,215)"], [1, "rgb(54,50,153)"],
            ],
            "lighting": {
                "ambient": 1,
                "diffuse": 0.9,
                "fresnel": 0.5,
                "roughness": 0.9,
                "specular": 2
            },
            "flatshading": flat_shading,
            "reversescale": True,
        }

        layout = {
            "title": "{} Call Volatility Surface | {}".format(ticker, str(dt.datetime.now())),
            'margin': {
                'l': 10,
                'r': 10,
                'b': 10,
                't': 60,
            },
            'paper_bgcolor': '#FAFAFA',
            "hovermode": "closest",
            "scene": {
                "aspectmode": "manual",
                "aspectratio": {
                    "x": 2,
                    "y": 2,
                    "z": 1
                },
                'camera': {
                    'up': {'x': 0, 'y': 0, 'z': 1},
                    'center': {'x': 0, 'y': 0, 'z': 0},
                    'eye': {'x': 1, 'y': 1, 'z': 0.5},
                },
                "xaxis": {
                    "title": "Strike ($)",
                    "showbackground": True,
                    "backgroundcolor": "rgb(230, 230,230)",
                    "gridcolor": "rgb(255, 255, 255)",
                    "zerolinecolor": "rgb(255, 255, 255)"
                },
                "yaxis": {
                    "title": "Expiry (days)",
                    "showbackground": True,
                    "backgroundcolor": "rgb(230, 230,230)",
                    "gridcolor": "rgb(255, 255, 255)",
                    "zerolinecolor": "rgb(255, 255, 255)"
                },
                "zaxis": {
                    "rangemode": "tozero",
                    "title": "IV (σ)",
                    "type": log_selector,
                    "showbackground": True,
                    "backgroundcolor": "rgb(230, 230,230)",
                    "gridcolor": "rgb(255, 255, 255)",
                    "zerolinecolor": "rgb(255, 255, 255)"
                }
            },
        }

        if (iv_surface_layout is not None and 'lock' in graph_toggles_state):

            try:
                up = iv_surface_layout['scene']['up']
                center = iv_surface_layout['scene']['center']
                eye = iv_surface_layout['scene']['eye']
                layout['scene']['camera']['up'] = up
                layout['scene']['camera']['center'] = center
                layout['scene']['camera']['eye'] = eye
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure
    
# Make main surface plot
@app.callback(Output('iv_surface_put', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('log_selector', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('iv_surface_put', 'relayoutData')])
def make_put_surface_plot(hidden, ticker, log_selector, graph_toggles,
                          graph_toggles_state, iv_surface_layout):

    if hidden == 'loaded':

        if 'flat' in graph_toggles:
            flat_shading = True
        else:
            flat_shading = False

        trace1 = {
            "type": "mesh3d",
            'x': filtered_data_put[0],
            'y': filtered_data_put[1],
            'z': filtered_data_put[2],
            'intensity': filtered_data_put[2],
            'autocolorscale': False,
            "colorscale": [
                [0, "rgb(244,236,21)"], [0.3, "rgb(249,210,41)"], [0.4, "rgb(134,191,118)"], [
                    0.5, "rgb(37,180,167)"], [0.65, "rgb(17,123,215)"], [1, "rgb(54,50,153)"],
            ],
            "lighting": {
                "ambient": 1,
                "diffuse": 0.9,
                "fresnel": 0.5,
                "roughness": 0.9,
                "specular": 2
            },
            "flatshading": flat_shading,
            "reversescale": True,
        }

        layout = {
            "title": "{} Put Volatility Surface | {}".format(ticker, str(dt.datetime.now())),
            'margin': {
                'l': 10,
                'r': 10,
                'b': 10,
                't': 60,
            },
            'paper_bgcolor': '#FAFAFA',
            "hovermode": "closest",
            "scene": {
                "aspectmode": "manual",
                "aspectratio": {
                    "x": 2,
                    "y": 2,
                    "z": 1
                },
                'camera': {
                    'up': {'x': 0, 'y': 0, 'z': 1},
                    'center': {'x': 0, 'y': 0, 'z': 0},
                    'eye': {'x': 1, 'y': 1, 'z': 0.5},
                },
                "xaxis": {
                    "title": "Strike ($)",
                    "showbackground": True,
                    "backgroundcolor": "rgb(230, 230,230)",
                    "gridcolor": "rgb(255, 255, 255)",
                    "zerolinecolor": "rgb(255, 255, 255)"
                },
                "yaxis": {
                    "title": "Expiry (days)",
                    "showbackground": True,
                    "backgroundcolor": "rgb(230, 230,230)",
                    "gridcolor": "rgb(255, 255, 255)",
                    "zerolinecolor": "rgb(255, 255, 255)"
                },
                "zaxis": {
                    "rangemode": "tozero",
                    "title": "IV (σ)",
                    "type": log_selector,
                    "showbackground": True,
                    "backgroundcolor": "rgb(230, 230,230)",
                    "gridcolor": "rgb(255, 255, 255)",
                    "zerolinecolor": "rgb(255, 255, 255)"
                }
            },
        }

        if (iv_surface_layout is not None and 'lock' in graph_toggles_state):

            try:
                up = iv_surface_layout['scene']['up']
                center = iv_surface_layout['scene']['center']
                eye = iv_surface_layout['scene']['eye']
                layout['scene']['camera']['up'] = up
                layout['scene']['camera']['center'] = center
                layout['scene']['camera']['eye'] = eye
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure


# Make side heatmap plot
@app.callback(Output('iv_heatmap_call', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('iv_heatmap_call', 'relayoutData')])
def make_call_heat_plot(hidden, ticker, graph_toggles,
                           graph_toggles_state, iv_heatmap_layout):

    if hidden == 'loaded':

        if 'discrete' in graph_toggles:
            shading = 'contour'
        else:
            shading = 'heatmap'

        trace1 = {
            "type": "contour",
            'x': filtered_data_call[0],
            'y': filtered_data_call[1],
            'z': filtered_data_call[2],
            'connectgaps': True,
            'line': {'smoothing': '1'},
            'contours': {'coloring': shading},
            'autocolorscale': False,
            "colorscale": [
                [0, "rgb(244,236,21)"], [0.3, "rgb(249,210,41)"], [0.4, "rgb(134,191,118)"],
                [0.5, "rgb(37,180,167)"], [0.65, "rgb(17,123,215)"], [1, "rgb(54,50,153)"],
            ],
            # Add colorscale log
            "reversescale": True,
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
                'range': [],
                "title": "Call Strike ($)",
            },
            "yaxis": {
                'range': [],
                "title": "Expiry (days)",
            },
        }

        if (iv_heatmap_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_heatmap_layout['xaxis.range[0]']
                x_range_right = iv_heatmap_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_heatmap_layout['yaxis.range[0]']
                y_range_right = iv_heatmap_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure

# Make side heatmap plot
@app.callback(Output('iv_heatmap_put', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('iv_heatmap_put', 'relayoutData')])
def make_put_heat_plot(hidden, ticker, graph_toggles,
                           graph_toggles_state, iv_heatmap_layout):

    if hidden == 'loaded':

        if 'discrete' in graph_toggles:
            shading = 'contour'
        else:
            shading = 'heatmap'

        trace1 = {
            "type": "contour",
            'x': filtered_data_put[0],
            'y': filtered_data_put[1],
            'z': filtered_data_put[2],
            'connectgaps': True,
            'line': {'smoothing': '1'},
            'contours': {'coloring': shading},
            'autocolorscale': False,
            "colorscale": [
                [0, "rgb(244,236,21)"], [0.3, "rgb(249,210,41)"], [0.4, "rgb(134,191,118)"],
                [0.5, "rgb(37,180,167)"], [0.65, "rgb(17,123,215)"], [1, "rgb(54,50,153)"],
            ],
            # Add colorscale log
            "reversescale": True,
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
                'range': [],
                "title": "Put Strike ($)",
            },
            "yaxis": {
                'range': [],
                "title": "Expiry (days)",
            },
        }

        if (iv_heatmap_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_heatmap_layout['xaxis.range[0]']
                x_range_right = iv_heatmap_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_heatmap_layout['yaxis.range[0]']
                y_range_right = iv_heatmap_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure

# Make side scatter plot
@app.callback(Output('iv_scatter_call', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('iv_scatter_call', 'relayoutData')])
def make_call_scatter_plot(hidden, ticker, graph_toggles,
                           graph_toggles_state, iv_scatter_layout):

    if hidden == 'loaded':

        if 'discrete' in graph_toggles:
            shading = 'contour'
        else:
            shading = 'heatmap'

        if 'box' in graph_toggles:
            typ = 'box'
        else:
            typ = 'scatter'

        trace1 = {
            "type": typ,
            'mode': 'markers',
            'x': filtered_data_call[1],
            'y': filtered_data_call[2],
            'boxpoints': 'outliers',
            'marker': {'color': '#32399F', 'opacity': 0.2}
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
                "title": "Expiry (days)",
            },
            "yaxis": {
                "rangemode": "tozero",
                "title": "Call IV (σ)",
            },
        }

        if (iv_scatter_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_scatter_layout['xaxis.range[0]']
                x_range_right = iv_scatter_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_scatter_layout['yaxis.range[0]']
                y_range_right = iv_scatter_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure
    
    
# Make side scatter plot
@app.callback(Output('iv_scatter_put', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('iv_scatter_put', 'relayoutData')])
def make_put_scatter_plot(hidden, ticker, graph_toggles,
                          graph_toggles_state, iv_scatter_layout):

    if hidden == 'loaded':

        if 'discrete' in graph_toggles:
            shading = 'contour'
        else:
            shading = 'heatmap'

        if 'box' in graph_toggles:
            typ = 'box'
        else:
            typ = 'scatter'

        trace1 = {
            "type": typ,
            'mode': 'markers',
            'x': filtered_data_call[1],
            'y': filtered_data_call[2],
            'boxpoints': 'outliers',
            'marker': {'color': '#32399F', 'opacity': 0.2}
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
                "title": "Expiry (days)",
            },
            "yaxis": {
                "rangemode": "tozero",
                "title": "Put IV (σ)",
            },
        }

        if (iv_scatter_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_scatter_layout['xaxis.range[0]']
                x_range_right = iv_scatter_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_scatter_layout['yaxis.range[0]']
                y_range_right = iv_scatter_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure
    
# Make side std plot
@app.callback(Output('std_historical_plot', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('std_historical_plot', 'relayoutData')])
def make_dollar_std_plot(hidden, ticker, graph_toggles,
                         graph_toggles_state, iv_scatter_layout):

    if hidden == 'loaded':

        if 'discrete' in graph_toggles:
            shading = 'contour'
        else:
            shading = 'heatmap'

        typ = 'bar'

        trace1 = {
            "type": typ,
            'mode': 'markers',
            'x': hist_data.index,
            'y': hist_data.daily_dollar_std_direction,
            'boxpoints': 'outliers',
            'marker': {'color': '#00aaff', 'opacity': 0.8}
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
                "title": "Historical Dollar Return Std.",
            },
        }

        if (iv_scatter_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_scatter_layout['xaxis.range[0]']
                x_range_right = iv_scatter_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_scatter_layout['yaxis.range[0]']
                y_range_right = iv_scatter_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure

# Make side std hist plot
@app.callback(Output('hv_std_hist', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('hv_std_hist', 'relayoutData')])
def make_dollar_hist(hidden, ticker, graph_toggles,
                     graph_toggles_state, iv_scatter_layout):

    if hidden == 'loaded':

        if 'discrete' in graph_toggles:
            shading = 'contour'
        else:
            shading = 'heatmap'

        typ = 'histogram'

        trace1 = {
            "type": typ,
            'mode': 'markers',
            'histnorm': 'probability',
            'x': hist_data.daily_dollar_std_direction,
            'marker': {'color': '#00aaff', 'opacity': 0.8}
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
                "title": "Dollar Return Std.",
            },
            "yaxis": {
                "rangemode": "tozero",
                "title": "Percentage Distribution",
            },
            'bargap' : 0.2,
            'bargroupgap': 0.1
        }

        if (iv_scatter_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_scatter_layout['xaxis.range[0]']
                x_range_right = iv_scatter_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_scatter_layout['yaxis.range[0]']
                y_range_right = iv_scatter_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure
    
# Update Prices
@app.callback(Output('last_price', 'children'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value')])
def update_last_price(hidden, ticker):

    if hidden == 'loaded':
        last_price = '{} Last Price: ${}'.format(ticker, str(round(hist_data.tail(1).close[0], 2)))
        return last_price
    
# Update Daily Vol
@app.callback(Output('daily_vol', 'children'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value')])
def update_daily_vol(hidden, ticker):

    if hidden == 'loaded':
        last_price = '{} Daily HV: {}%'.format(ticker, str(round(hist_data.tail(1).daily_ann[0]*100, 2)))
        return last_price
    
# Update Intra Vol
@app.callback(Output('intra_vol', 'children'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value')])
def update_intra_vol(hidden, ticker):

    if hidden == 'loaded':
        last_price = '{} Intraday HV: {}%'.format(ticker, str(round(hist_data.tail(1).intra_ann[0]*100, 2)))
        return last_price

# Update Overnight Vol
@app.callback(Output('ovrnt_vol', 'children'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value')])
def update_overnight_vol(hidden, ticker):

    if hidden == 'loaded':
        last_price = '{} Overnight HV: {}%'.format(ticker, str(round(hist_data.tail(1).ovrnt_ann[0]*100, 2)))
        return last_price

# Make side scatter plot
@app.callback(Output('hv_line_plot', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('hv_line_plot', 'relayoutData')])
def make_hv_line_plot(hidden, ticker, graph_toggles,
                      graph_toggles_state, iv_scatter_layout):

    if hidden == 'loaded':
        
        typ = 'scatter'

        trace1 = {
            "type": typ,
            'mode': 'lines+markers',
            'name': 'Daily Vol',
            'x': hist_data.index,
            'y': hist_data.daily_ann,
            'marker': {'color': '#00c8c8', 'opacity': 0.8}
        }
        
        trace2 = {
            "type": typ,
            'mode': 'lines+markers',
            'name': 'Intraday Vol',
            'x': hist_data.index,
            'y': hist_data.intra_ann,
            'marker': {'color': '#c800c8', 'opacity': 0.8}
        }
        
        trace3 = {
            "type": typ,
            'mode': 'lines+markers',
            'name': 'Overnight Vol',
            'x': hist_data.index,
            'y': hist_data.ovrnt_ann,
            'marker': {'color': '#c8c800', 'opacity': 0.8}
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
                'showline': 'True',
                'showgrid': 'False',
                'showticklabels': 'True',
                'ticks': 'outside'
            },
            "yaxis": {
                "rangemode": "tozero",
                "title": "HV (σ)",
            },
        }

        if (iv_scatter_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_scatter_layout['xaxis.range[0]']
                x_range_right = iv_scatter_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_scatter_layout['yaxis.range[0]']
                y_range_right = iv_scatter_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1, trace2, trace3]
        figure = dict(data=data, layout=layout)
        return figure
    

if __name__ == '__main__':
    app.server.run(debug=True, threaded=True, use_reloader=False)
