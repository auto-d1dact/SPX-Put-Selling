# -*- coding: utf-8 -*-
"""
Created on Wed Aug  1 16:01:12 2018

@author: Fang

functions list:
    
    maturities(dt.datetime()) --> [float(front_wgt), float(back_wgt)]
    
    optionslam_scrape(str[ticker]) --> dict[earnings]
    
    yahoo_table_parse(str[raw_html_table]) --> DataFrame[ticker]
    
    yahoo_earnings(dt.datetime()) --> DataFrame[earnings_on_date]
    
    fundamentals(str[ticker]) --> DataFrame[stock_fundamentals]
    
    get_fundas(list[ticker_lst]) --> DataFrame[stock_fundamentals]
    
    historical_data(str[ticker], int[day_number], int[rolling_window], outsize[str]) --> DataFrame[daily_stock_data]
    
    current_volatility(list[ticker_lst], int[roll]) --> DataFrame[stock_volatilities]
    
    all_options(str[ticker], bool[greeks]) --> DataFrame[options_chains]
    
    earnings_condor(str[ticker], int[max_gap], int[dte_thresh], float[|money_thresh| <= 1]) -- DataFrame[condors], DataFrame[puts], DataFrame[calls]
    
    write_excel(str[filename], list[str[sheetnames]], list[dataframes]) --> void()
    
    curr_stock_data(str[ticker]) --> DataFrame[stock_info]
    
    curr_batch_quotes(list_of_string[tickers]) --> DataFrame[stock_info]
        
"""

# Note to import from .py files, must follow structure
# from <.py filename excluding '.py'> import <class name>
# Optionslam creds: aspringfastlaner Options2018

# Importing necessary models
import smtplib
import pandas as pd
import numpy as np
import datetime as dt
import pandas.stats.moments as st
from pandas import ExcelWriter
import matplotlib.pyplot as plt
import os
import seaborn as sns
import matplotlib.dates as dates
# import matplotlib.ticker as ticker
from lxml import html
import requests
import webbrowser
from bs4 import BeautifulSoup as bs
import json
import csv
import sched, time
import pandas_datareader as datareader
from pandas_datareader.data import Options
from alpha_vantage.timeseries import TimeSeries
#ts = TimeSeries(key='5HZEUI5AFJB06BUK',output_format='pandas')
#key2 = '6ZAZOL7YF8VPXND7'
import matplotlib.pyplot as plt
import urllib.request as urlreq
from collections import OrderedDict
import statsmodels.formula.api as sm


import plotly.plotly as py
import plotly.graph_objs as go

from pandas_datareader.data import Options
import py_vollib
from py_vollib.black_scholes_merton.implied_volatility import *
from py_vollib.black_scholes_merton.greeks.analytical import *

import quandl as qd
qd.ApiConfig.api_key = 'dzmzEExntfap7SNx5p6t'


def maturities(date):
    
    # Calculate today, but note that since we are adjusting for lookback bias, we need to change the current date to one day prior
    today = date
    curr_month = today.month
    curr_year = today.year
    
    # Finding Prev Third Wed
    curr_eigth_day = dt.date(curr_year,curr_month,7)
    curr_second_day = dt.date(curr_year,curr_month,3).weekday()
    curr_third_fri = curr_eigth_day - dt.timedelta(curr_second_day) + dt.timedelta(14)
    last_third_wed = curr_third_fri - dt.timedelta(30)
    
    # Finding Next Third Wed
    if curr_month == 12:
        next_month = 2
        next_year = curr_year + 1
    elif curr_month == 11:
        next_month = 1
        next_year = curr_year + 1
    else:
        next_month = curr_month + 2
        next_year = curr_year
    next_eigth_day = dt.date(next_year,next_month,7)
    next_second_day = dt.date(next_year,next_month,3).weekday()
    next_third_fri = next_eigth_day - dt.timedelta(next_second_day) + dt.timedelta(14)
    next_third_wed = next_third_fri - dt.timedelta(30)
    
    # Finding Cur Third Wed
    if curr_month == 12:
        next_month = 1
        next_year = curr_year + 1
    else:
        next_month = curr_month + 1
        next_year = curr_year
    next_eigth_day = dt.date(next_year,next_month,7)
    next_second_day = dt.date(next_year,next_month,3).weekday()
    next_third_fri = next_eigth_day - dt.timedelta(next_second_day) + dt.timedelta(14)
    curr_third_wed = next_third_fri - dt.timedelta(30)
    
    # Finding Term: When current date is after expiry, should be 100% of spot/f1
    if today < curr_third_wed:
        dte = curr_third_wed - today
        term = curr_third_wed - last_third_wed
    else:
        dte = next_third_wed - today
        term = next_third_wed - curr_third_wed
    # print (float(dte.days)/term.days)
    front_weight = float(dte.days)/term.days
    back_weight = 1 - front_weight
    return [front_weight, back_weight]


'''
Function for pulling implied volatility from option slam for single ticker
'''

def optionslam_scrape(ticker):
    site = 'https://www.optionslam.com/earnings/stocks/' + ticker
    res = requests.get(site)
    soup = bs(requests.get(site).text, "lxml")
    soup = soup.prettify()
    earnings_dict = {'Ticker': ticker}
    
    # Check if there's weekly options
    curr7_implied = "Current 7 Day Implied Movement:"
    implied_move_weekly = "Implied Move Weekly:"
    nextearnings = "Next Earnings Date:"
    if curr7_implied not in soup:
        return 'No Weeklies'
    
    # Parsing if weekly options exist
    # Next earnings date and before or after
    earnings_start_string = "Next Earnings Date:"
    earnings_end_string = '</font>'
    raw_earnings_string = (soup.split(earnings_start_string))[1].split(earnings_end_string)[0].replace('\n','').strip()
    
    try:
        earnings_date = str((raw_earnings_string.split('<b>'))[1].split('<font size="-1">')).split("'")[1].strip()
    except:
        return 'Error Parsing'
    
    earnings_time = str(raw_earnings_string[-2:].strip()).strip()
    
    earnings_dict['Date'] = earnings_date
    earnings_dict['Earnings Time'] = earnings_time
    
    # Parsing 7 day implied move if weekly option exists
    ending_string = '<font size="-2">'
    curr_7 = (soup.split(curr7_implied))[1].split(ending_string)[0].replace('\n','').strip("").split("<td>")[-1].strip()
    earnings_dict['Current 7 Day Implied'] = curr_7
    
    # Parsing Weekly Implied move if weekly option exists
    if implied_move_weekly in soup:
        weekly_implied = (soup.split(implied_move_weekly))[1].split(ending_string)[0].replace('\n','').strip("").split("<td>")[-1].strip()
    else:
        weekly_implied = ''
    earnings_dict["Implied Move Weekly"] = weekly_implied
    
    return earnings_dict

def yahoo_table_parse(raw_html_table):
    tickers = []
    call_times = []
    implied_7_day = []
    implied_weekly = []
    eps = []
    i = 1
    end_row = 10
    for row in raw_html_table.find_all('tr'):
        # Individual row stores current row item and delimits on '\n'
        individual_row = str(row).split('\n')
        row_items = individual_row[0].split('</span>')[:3]

        if i == 1:
            i += 1
            continue
        tick = row_items[0].split('data-symbol="')[1].split('"')[0]
        os_check = optionslam_scrape(tick)

        if type(os_check) == str:
            continue
        else:
            tickers.append(tick)
            call_times.append(row_items[0].split('data-symbol="')[1].split('"')[-1].replace('>',''))
            eps.append(row_items[1].split('</td>')[1].split('>')[1])
            
            try:
                implied_7 = float(os_check['Current 7 Day Implied'].replace('%',''))
            except:
                implied_7 = os_check['Current 7 Day Implied'].replace('%','')
                
            try:
                implied_week = float(os_check['Implied Move Weekly'].replace('%',''))
            except:
                implied_week = os_check['Implied Move Weekly'].replace('%','')
                
            implied_7_day.append(implied_7)
            implied_weekly.append(implied_week)


    return pd.DataFrame({'Tickers': tickers, 'Call Times': call_times, 'EPS': eps,
                         'Current 7 Day Implied': implied_7_day,
                         'Implied Move Weekly': implied_weekly})


def yahoo_earnings(date):
    # Yahoo Earnings Calendar Check

    today = date.strftime('%Y-%m-%d')
    tables = []
    no_tables = False
    for i in range(6):
        if no_tables:
            break
        yahoo_url = 'https://finance.yahoo.com/calendar/earnings?day=' + today + '&offset={}&size=100'.format(int(i*100))
        res = requests.get(yahoo_url)
        soup = bs(requests.get(yahoo_url).text, "lxml")
        
        try:
            table = soup.find_all('table')[0]
            tables.append(yahoo_table_parse(table))
        except:
            print('No Table')
            no_tables = True

    return pd.concat(tables,axis = 0, ignore_index = True)

'''
Function for getting all relevant earnings for a given starting week (Monday in dt.datetime(YYYY, m, d) format)
Returns a dataframe with the earnings names, implied move, price, and earnings times.
'''
def weekly_earnings_check(start_datetime, days_forward):

    start_date = start_datetime

    weekly_earnings = []
    while start_date.weekday() < days_forward:
        try:
            temp_earnings = yahoo_earnings(start_date)
            temp_earnings['Earnings Date'] = start_date
#             temp_earnings['Last Close'] = 0
#             for idx, row in temp_earnings.iterrows():
#                 try:
#                     temp_earnings.loc[idx, 'Last Close'] = ts.get_daily(row['Tickers'])[0].tail(1)['close'][0]
#                 except:
#                     temp_earnings.loc[idx, 'Last Close'] = np.nan
            weekly_earnings.append(temp_earnings)
            start_date = start_date + dt.timedelta(1)
        except:
            start_date = start_date + dt.timedelta(1)

    earnings_df = pd.concat(weekly_earnings, axis = 0, ignore_index = True)
#     earnings_df = earnings_df[earnings_df['Last Close'] >= 20]
#     earnings_df['Lower Bound'] = np.round(earnings_df['Last Close']*(1 - earnings_df['Implied Move Weekly']/100),2)
#     earnings_df['Upper Bound'] = np.round(earnings_df['Last Close']*(1 + earnings_df['Implied Move Weekly']/100),2)
    earnings_df = earnings_df.sort_values(['Earnings Date','Call Times'])
    
    return earnings_df
    
def fundamentals(ticker):
    
    site = 'https://finance.yahoo.com/quote/{0}?p={0}'.format(ticker)

    res = requests.get(site)
    soup = bs(res.text, 'lxml')
    table = soup.find_all('table')[1]
    sum_dict = {}

    # Looping through the soup lxml text table format
    # and splitting each row as a individual string
    # and parsing string to retrieve the date,
    # open, and close information.


    for row in table.find_all('tr'):
        # Individual row stores current row item and delimits on '\n'
        individual_row = str(row).split('\n')[0]

        # row_items is parsed string for each current row where each
        # item in list is the date, open, high, low, close, and volume
        row_items = individual_row.split('<span data-reactid=')[1].split('"><!-- react-text: ')
        
        if len(row_items) > 1:
            sum_item = row_items[0].split('>')[1].split('<')[0]
            sum_value = row_items[1].split('-->')[1].split('<')[0]
        elif 'YIELD' in row_items[0]:
            try:
                temp_val = row_items[0].split('-value">')[1].split("</td>")[0]
                div_amount = float(temp_val.split(' ')[0])
                div_yield = float(temp_val.split(' ')[1].replace('(','').replace(')','').replace('%',''))

                sum_dict['Div'] = div_amount
                sum_dict['Yield'] = div_yield
            except:
                sum_dict['Div'] = np.nan
                sum_dict['Yield'] = np.nan
        elif 'Market Cap' in row_items[0]:
            sum_item = 'Market Cap (B)'
            mkt_cap = row_items[0].split('data-reactid="')[-1].split('>')[1].split('<')[0]
            mkt_cap_amount = float(mkt_cap[:-1])
            if mkt_cap[-1] == 'M':
                sum_value = mkt_cap_amount/1000
            else:
                sum_value = mkt_cap_amount
        else:
            sum_item = row_items[0].split('>')[1].split('<')[0]
            sum_value = row_items[0].split('data-reactid="')[-1].split('>')[1].split('<')[0]
        
        sum_dict[sum_item] = sum_value
    
    sum_dict['Days Since Last Earnings'] = (dt.datetime.today().date() - 
                                            stock_earnings(ticker)['Earnings Dates'][1].date()).days

    return pd.DataFrame(sum_dict, index = [ticker])

# Function to return fundametal data of a ticker list
def get_fundas(ticker_lst):
    fund_lst = []
    for tick in ticker_lst:
        try:
            fund_lst.append(fundamentals(tick))
        except:
            continue
    return pd.concat(fund_lst,axis = 0)

# Function historical data from alpha advantage
def historical_data(ticker, day_number = 252, rolling_window = 20, outsize = 'full'):
    alphavantage_link = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={0}&apikey=6ZAZOL7YF8VPXND7&datatype=csv&outputsize={1}'.format(ticker, outsize)
    stockframe = pd.read_csv(alphavantage_link, index_col = 0).sort_index()[['open', 'close']]
    stockframe['daily_ret'] = np.log(stockframe['close']/stockframe['close'].shift(1))
    stockframe['intra_ret'] = np.log(stockframe['close']/stockframe['open'])
    stockframe['ovrnt_ret'] = np.log(stockframe['open']/stockframe['close'].shift(1))
    stockframe['daily_vol'] = stockframe.daily_ret.rolling(window=rolling_window,center=False).std()
    stockframe['intra_vol'] = stockframe.intra_ret.rolling(window=rolling_window,center=False).std()
    stockframe['ovrnt_vol'] = stockframe.ovrnt_ret.rolling(window=rolling_window,center=False).std()
    stockframe['daily_ann'] = stockframe.daily_vol*np.sqrt(252)
    stockframe['intra_ann'] = stockframe.intra_vol*np.sqrt((24/6.5)*252)
    stockframe['ovrnt_ann'] = stockframe.ovrnt_vol*np.sqrt((24/17.5)*252)
    stockframe['oc_diff'] = stockframe.close - stockframe.open
    stockframe['daily_dollar_vol'] = stockframe.daily_vol*stockframe.close.shift(1)
    stockframe['daily_dollar_std'] = np.abs(stockframe.oc_diff/stockframe.daily_dollar_vol)

    return stockframe.tail(day_number)

# Function for building a dataframe of volatilities
# Daily, Intraday, Overnight
def current_volatility(ticker_list, roll = 20):
    
    rows = []
    failed_tickers = []
    
    def failed_check(failed_lst,rows):
        if len(failed_lst) == 0:
            return failed_lst, rows
        else:
            new_lst = []
            new_rows = rows
            for tick in failed_lst:
                try: 
                    curr_vol = historical_data(tick, outsize = 'compact').tail(1)[['daily_ann','intra_ann','ovrnt_ann','close',
                                                                                   'daily_dollar_vol']]
                    curr_vol.index.name = 'Tickers'
                    curr_vol.index = [tick]
                    new_rows.append(curr_vol)
                except:
                    new_lst.append(tick)
            return failed_check(new_lst, rows)

    for tick in ticker_list:
        try: 
            curr_vol = historical_data(tick, outsize = 'compact').tail(1)[['daily_ann','intra_ann','ovrnt_ann','close',
                                                                           'daily_dollar_vol']]
            curr_vol.index.name = 'Tickers'
            curr_vol.index = [tick]
            rows.append(curr_vol)
        except:
            failed_tickers.append(tick)
            
    failed_lst, rows = failed_check(failed_tickers, rows)
        
    return pd.concat(rows, axis = 0)

def all_options(ticker, greeks = True):
    tape = Options(ticker, 'yahoo')
    data = tape.get_all_data().reset_index()
    
    data['Moneyness'] = np.abs(data['Strike'] - data['Underlying_Price'])/data['Underlying_Price']
    
    data['DTE'] = (data['Expiry'] - dt.datetime.today()).dt.days
    data = data[['Strike', 'DTE', 'Type', 'IV', 'Vol','Open_Int', 'Moneyness', 'Root', 'Underlying_Price',
                 'Last','Bid','Ask']]
    data['Mid'] = (data['Ask'] - data['Bid'])/2 + data['Bid']
    
    if greeks:
        year = 365
        strikes = data['Strike'].values
        time_to_expirations = data['DTE'].values
        ivs = data['IV'].values
        underlying = data['Underlying_Price'].values[0]
        types = data['Type'].values
    
        # Make sure nothing thows up
        assert len(strikes) == len(time_to_expirations)
    
        sigmas = data['IV']
        deltas = []
        gammas = []
        thetas = []
        vegas = []
        for sigma, strike, time_to_expiration, flag in zip(sigmas, strikes, time_to_expirations, types):
    
            # Constants
            S = underlying
            K = strike
            t = time_to_expiration/float(year)
            r = 0.005 / 100
            q = 0 / 100
    
            try:
                delta = py_vollib.black_scholes_merton.greeks.analytical.delta(flag[0], S, K, t, r, sigma, q)
                deltas.append(delta)
            except:
                delta = 0.0
                deltas.append(delta)
    
            try:
                gamma = py_vollib.black_scholes_merton.greeks.analytical.gamma(flag[0], S, K, t, r, sigma, q)
                gammas.append(gamma)
            except:
                gamma = 0.0
                gammas.append(gamma)
    
            try:
                theta = py_vollib.black_scholes_merton.greeks.analytical.theta(flag[0], S, K, t, r, sigma, q)
                thetas.append(theta)
            except:
                theta = 0.0
                thetas.append(theta)
    
            try:
                vega = py_vollib.black_scholes_merton.greeks.analytical.vega(flag[0], S, K, t, r, sigma, q)
                vegas.append(vega)
            except:
                vega = 0.0
                vegas.append(vega)
    
        data['Delta'] = deltas
        data['Gamma'] = gammas
        data['Theta'] = thetas
        data['Vega'] = vegas

    return data.reset_index()[data.columns]#data.dropna().reset_index()[data.columns]


def earnings_condor(tick, max_gap, dte_thresh, money_thresh):
    chain = all_options(tick)
    chain = chain[chain['DTE'] <= dte_thresh]
    chain = chain.reset_index()[chain.columns]
    chain = chain[chain['Moneyness'] <= money_thresh]
    chain_puts = chain[(chain['Type'] == 'put') & (chain['Strike'] < chain['Underlying_Price'].values[0])]
    chain_calls = chain[(chain['Type'] == 'call') & (chain['Strike'] > chain['Underlying_Price'].values[0])]


    put_spread_prem = []
    put_spread_delta = []
    put_spread_gamma = []
    put_spread_vega = []
    put_spread_theta = []
    put_spread_short_strike = []
    put_spread_long_strike = []
    put_spread_max_loss = []
    for idx, row in chain_puts.sort_values('Strike', ascending = False).iterrows():
        curr_short_strike = row.Strike
        curr_short_prem = row.Bid
        curr_short_delta = row.Delta
        curr_short_gamma = row.Gamma
        curr_short_vega = row.Vega
        curr_short_theta = row.Theta

        temp_longs = chain_puts[(chain_puts['Strike'] < curr_short_strike) &
                                (chain_puts['Strike'] >= curr_short_strike - max_gap)]

        for temp_idx, temp_row in temp_longs.iterrows():
            curr_long_strike = temp_row.Strike
            curr_long_prem = temp_row.Ask
            curr_long_delta = temp_row.Delta
            curr_long_gamma = temp_row.Gamma
            curr_long_vega = temp_row.Vega
            curr_long_theta = temp_row.Theta

            curr_spread_prem = curr_short_prem - curr_long_prem
            curr_spread_delta = -curr_short_delta + curr_long_delta
            curr_spread_gamma = -curr_short_gamma + curr_long_gamma
            curr_spread_vega = -curr_short_vega + curr_long_vega
            curr_spread_theta = -curr_short_theta + curr_long_theta
            curr_spread_maxloss = (curr_short_strike - curr_long_strike - curr_spread_prem)*100

            put_spread_prem.append(curr_spread_prem)
            put_spread_delta.append(curr_spread_delta)
            put_spread_gamma.append(curr_spread_gamma)
            put_spread_vega.append(curr_spread_vega)
            put_spread_theta.append(curr_spread_theta)
            put_spread_short_strike.append(curr_short_strike)
            put_spread_long_strike.append(curr_long_strike)
            put_spread_max_loss.append(curr_spread_maxloss)

    put_spreads_df = pd.DataFrame(OrderedDict({'put Combo': range(len(put_spread_prem)),
                                               'Short Put Strike': put_spread_short_strike,
                                               'Long Put Strike': put_spread_long_strike,
                                               'put Spread Premium': put_spread_prem,
                                               'put Spread Maxloss': put_spread_max_loss,
                                               'put Spread Delta': put_spread_delta,
                                               'put Spread Gamma': put_spread_gamma,
                                               'put Spread Vega': put_spread_vega,
                                               'put Spread Theta': put_spread_theta}),
                                  index = range(len(put_spread_prem)))

    call_spread_prem = []
    call_spread_delta = []
    call_spread_gamma = []
    call_spread_vega = []
    call_spread_theta = []
    call_spread_short_strike = []
    call_spread_long_strike = []
    call_spread_max_loss = []
    for idx, row in chain_calls.sort_values('Strike', ascending = True).iterrows():
        curr_short_strike = row.Strike
        curr_short_prem = row.Bid
        curr_short_delta = row.Delta
        curr_short_gamma = row.Gamma
        curr_short_vega = row.Vega
        curr_short_theta = row.Theta

        temp_longs = chain_calls[(chain_calls['Strike'] > curr_short_strike) &
                                (chain_calls['Strike'] <= curr_short_strike + max_gap)]

        for temp_idx, temp_row in temp_longs.iterrows():
            curr_long_strike = temp_row.Strike
            curr_long_prem = temp_row.Ask
            curr_long_delta = temp_row.Delta
            curr_long_gamma = temp_row.Gamma
            curr_long_vega = temp_row.Vega
            curr_long_theta = temp_row.Theta

            curr_spread_prem = curr_short_prem - curr_long_prem
            curr_spread_delta = -curr_short_delta + curr_long_delta
            curr_spread_gamma = -curr_short_gamma + curr_long_gamma
            curr_spread_vega = -curr_short_vega + curr_long_vega
            curr_spread_theta = -curr_short_theta + curr_long_theta
            curr_spread_maxloss = -(curr_short_strike - curr_long_strike + curr_spread_prem)*100

            call_spread_prem.append(curr_spread_prem)
            call_spread_delta.append(curr_spread_delta)
            call_spread_gamma.append(curr_spread_gamma)
            call_spread_vega.append(curr_spread_vega)
            call_spread_theta.append(curr_spread_theta)
            call_spread_short_strike.append(curr_short_strike)
            call_spread_long_strike.append(curr_long_strike)
            call_spread_max_loss.append(curr_spread_maxloss)

    call_spreads_df = pd.DataFrame(OrderedDict({'call Combo': range(len(call_spread_prem)),
                                               'Short call Strike': call_spread_short_strike,
                                               'Long call Strike': call_spread_long_strike,
                                               'call Spread Premium': call_spread_prem,
                                               'call Spread Maxloss': call_spread_max_loss,
                                               'call Spread Delta': call_spread_delta,
                                               'call Spread Gamma': call_spread_gamma,
                                               'call Spread Vega': call_spread_vega,
                                               'call Spread Theta': call_spread_theta}),
                                  index = range(len(call_spread_prem)))

    put_combos = []
    call_combos = []
    condor_prems = []
    condor_maxloss = []
    condor_delta = []
    condor_gamma = []
    condor_vega = []
    condor_theta = []
    put_short = []
    put_long = []
    call_short = []
    call_long = []

    for idxc, rowc in call_spreads_df.iterrows():
        for idxp, rowp in put_spreads_df.iterrows():
            p_s = put_spreads_df[put_spreads_df['put Combo'] == rowp['put Combo']]['Short Put Strike'].values[0]
            p_l = put_spreads_df[put_spreads_df['put Combo'] == rowp['put Combo']]['Long Put Strike'].values[0]
            c_s = call_spreads_df[call_spreads_df['call Combo'] == rowc['call Combo']]['Short call Strike'].values[0]
            c_l = call_spreads_df[call_spreads_df['call Combo'] == rowc['call Combo']]['Long call Strike'].values[0]

            put_short.append(p_s)
            put_long.append(p_l)
            call_short.append(c_s)
            call_long.append(c_l)

            curr_prem = round(rowp['put Spread Premium'] + rowc['call Spread Premium'],2)

            condor_prems.append(curr_prem)
            condor_maxloss.append(100*(max(p_s - p_l, c_l - c_s) - curr_prem))
            condor_delta.append(rowp['put Spread Delta'] + rowc['call Spread Delta'])
            condor_gamma.append(rowp['put Spread Gamma'] + rowc['call Spread Gamma'])
            condor_vega.append(rowp['put Spread Vega'] + rowc['call Spread Vega'])
            condor_theta.append(rowp['put Spread Theta'] + rowc['call Spread Theta'])

    condors_df = pd.DataFrame(OrderedDict({'P Short Strike': put_short,
                                           'P Long Strike': put_long,
                                           'C Short Strike': call_short,
                                           'C Long Strike': call_long,
                                           'Premium': condor_prems,
                                           'Maxloss': condor_maxloss,
                                           'Delta': condor_delta,
                                           'Gamma': condor_gamma,
                                           'Vega': condor_vega,
                                           'Theta': condor_theta}),
                                  index = range(len(condor_prems)))
    condors_df['RiskRewardRatio'] = round((100*condors_df['Premium'])/condors_df['Maxloss'],2)
    put_spreads_df['RiskRewardRatio'] = round((100*put_spreads_df['put Spread Premium'])/put_spreads_df['put Spread Maxloss'],2)
    call_spreads_df['RiskRewardRatio'] = round((100*call_spreads_df['call Spread Premium'])/call_spreads_df['call Spread Maxloss'],2)
    condors_df['Underlying Price'] = chain['Underlying_Price'].values[0]
    
    return condors_df, put_spreads_df, call_spreads_df


def write_excel(filename, sheetnames, df_list):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    for i, df in enumerate(df_list):
        
        df.to_excel(writer, sheet_name = sheetnames[i])

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    return

def curr_stock_data(ticker):
    yahoo_url = 'https://finance.yahoo.com/quote/{0}/history?p={0}'.format(ticker)

    soup = bs(requests.get(yahoo_url).text, "lxml")

    table = soup.find_all('table')[0]

    i = 0

    for row in table.find_all('tr'):
        if i == 2:
            break
        else:
            individual_row = str(row).split('\n')
            i += 1

    curr_svxy = [float(x.split('>')[-1]) for x in individual_row[0].split('</span>')[1:-2]]
    
    return curr_svxy

def curr_batch_quotes(tickerlst):
    lst_string = str(tickerlst).replace('[','').replace(']','').replace(' ','').replace("'",'')
    av_link = 'https://www.alphavantage.co/query?function=BATCH_STOCK_QUOTES&symbols={0}&apikey=APIKEY=5HZEUI5AFJB06BUK&datatype=csv'.format(lst_string)
    df = pd.read_csv(av_link, index_col = 0)
    return df