# Import required libraries
import datetime as dt

import numpy as np
import pandas as pd
from pandas_datareader.data import Options
from alpha_vantage.timeseries import TimeSeries
from py_vollib.black_scholes_merton.implied_volatility import *
from alpha_vantage.timeseries import TimeSeries
ts = TimeSeries(key='5HZEUI5AFJB06BUK',output_format='pandas')
import py_vollib
from py_vollib.black_scholes_merton.implied_volatility import *
from py_vollib.black_scholes_merton.greeks.analytical import *

from trading_calendar import USTradingCalendar



# Get time delta
def get_time_delta(today, date_list, trading_calendar=True):

    delta_list = []

    if trading_calendar:
        year = 252
        calendar = USTradingCalendar()

        for date in date_list:
            trading_holidays = calendar.holidays(today, date).tolist()
            delta = np.busday_count(today, date, holidays=trading_holidays) + 1
            delta_list.append(delta)
    else:
        year = 365

        for date in date_list:
            delta = abs((today - date).days) + 1
            delta_list.append(delta)

    delta_list = np.array(delta_list)
    normalized = delta_list / float(year)

    return delta_list, normalized


# Get tape
def get_raw_data(ticker):
    tape = Options(ticker, 'yahoo')
    data = tape.get_all_data()
    return data


# Get volatility matrix
def get_filtered_data(data, calculate_iv=True, call=True, put=False,
                      volume_threshold=1, above_below=False,
                      rf_interest_rate=0.0, dividend_rate=0.0,
                      trading_calendar=True, market=True,
                      days_to_expiry=60):

    if call and put:
        raise Exception('Must specify either call or put.')
    if not call and not put:
        raise Exception('Must specify either call or put.')
    if call:
        flag = 'c'
        typ = 'call'
    if put:
        flag = 'p'
        typ = 'put'

    if not above_below:
        above_below = 1E9  # Very large number, good enough for our purposes

    underlying = data['Underlying_Price'][0]

    # Filter dataframe
    df = data[(data.index.get_level_values('Type') == typ)
              & (data['Vol'] >= volume_threshold)
              & (data.index.get_level_values('Strike') < (underlying + above_below + 1))
              & (data.index.get_level_values('Strike') > (underlying - above_below - 1))
              & (data.index.get_level_values('Expiry') <= 
                 (dt.datetime.today() + dt.timedelta(days = days_to_expiry)))]

    # Get columns
    if typ == 'call':
        premiums = df['Ask']  # Always assume user wants to get filled price
    else:
        premiums = df['Bid']

    if not market:
        premiums = df['Last']  # Last executed price vs Bid/Ask price

    strikes = df.index.get_level_values('Strike').values
    expiries = df.index.get_level_values('Expiry').to_pydatetime()
    plotting, time_to_expirations = get_time_delta(dt.datetime.today(
    ), expiries, trading_calendar)  # Can get slow if too many expiries
    ivs = df['IV'].values

    # Make sure nothing thows up
    assert len(premiums) == len(strikes)
    assert len(strikes) == len(time_to_expirations)

    if calculate_iv:

        sigmas = []
        for premium, strike, time_to_expiration in zip(premiums, strikes, time_to_expirations):

            # Constants
            P = premium
            S = underlying
            K = strike
            t = time_to_expiration
            r = rf_interest_rate / 100
            q = dividend_rate / 100
            try:
                sigma = implied_volatility(P, S, K, t, r, q, flag)
                sigmas.append(sigma)
            except:
                sigma = 0.0
                sigmas.append(sigma)

        ivs = np.array(sigmas)

    return strikes, plotting, ivs

# Function historical data from alpha advantage
def historical_data(ticker, day_number = 252, rolling_window = 22, outsize = 'full'):
    alphavantage_link = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={0}&apikey=5HZEUI5AFJB06BUK&datatype=csv&outputsize={1}'.format(ticker, outsize)
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
    stockframe['daily_dollar_std_direction'] = stockframe.oc_diff/stockframe.daily_dollar_vol

    return stockframe.tail(day_number)

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

# Function for pulling options for a given ticker
def option_filter(ticker, moneyness_thresh, dte_thresh):
    fwd_date = dt.datetime.today() + dt.timedelta(days = dte_thresh)
    tape = Options(ticker, 'yahoo')
    data = tape.get_options_data(month = fwd_date.month, year = fwd_date.year).reset_index()
    data['Moneyness'] = np.abs(data['Strike'] - data['Underlying_Price'])/data['Underlying_Price']
    
    data['DTE'] = (data['Expiry'] - dt.datetime.today()).dt.days
    data = data[['Strike', 'DTE', 'Type', 'IV', 'Vol','Open_Int', 'Moneyness', 'Root', 'Underlying_Price',
                 'Last','Bid','Ask']]
    data['Mid'] = data['Ask'] - data['Bid']

    filtered_data = data[(data['Moneyness'] <= moneyness_thresh) &
                         (data['DTE'] <= dte_thresh)].reset_index()[data.columns]
    put_ivs = filtered_data[filtered_data.Type == 'put'].pivot(index='Strike', columns='DTE', 
                                                               values='IV').dropna()
    call_ivs = filtered_data[filtered_data.Type == 'put'].pivot(index='Strike', columns='DTE', 
                                                                values='IV').dropna()
    hv_data = current_volatility([ticker])

    put_ivs['Close'] = hv_data['close'][0]
    call_ivs['Close'] = hv_data['close'][0]
    put_ivs['Daily HV'] = hv_data['daily_ann'][0]
    call_ivs['Daily HV'] = hv_data['daily_ann'][0]
    put_ivs['Intra HV'] = hv_data['intra_ann'][0]
    call_ivs['Intra HV'] = hv_data['intra_ann'][0]
    put_ivs['Overnight HV'] = hv_data['ovrnt_ann'][0]
    call_ivs['Overnight HV'] = hv_data['ovrnt_ann'][0]
    put_ivs['Daily Dollar Vol'] = hv_data['daily_dollar_vol'][0]
    call_ivs['Daily Dollar Vol'] = hv_data['daily_dollar_vol'][0]
    
    put_ivs['Moneyness'] = np.abs(put_ivs.index - put_ivs['Close'])/put_ivs['Close']
    call_ivs['Moneyness'] = np.abs(call_ivs.index - call_ivs['Close'])/call_ivs['Close']

    call_ivs.index.name = ticker + ' Call Strike'
    put_ivs.index.name = ticker + ' Put Strike'
    return call_ivs, put_ivs

def greek_calc(ticker, dte_ub, dte_lb, prem_price_use = 'Mid', delta_filter = 0.2, expiry_set = 0):
    fwd_date = dt.datetime.today() + dt.timedelta(days = dte_ub)
    tape = Options(ticker, 'yahoo')
    options_chain = tape.get_options_data(month = fwd_date.month, year = fwd_date.year).reset_index()
    options_chain = options_chain[['Strike','Expiry','Type','Last','Bid','Ask','Vol','Open_Int','IV','Underlying_Price']]
    df = options_chain
    df['DTE'] = (df['Expiry'] - dt.datetime.today()).dt.days
    df['Mid'] = (df['Ask'] + df['Bid'])/2
    df = df[(df['DTE'] <= dte_ub) & (df['DTE'] >= dte_lb)]
    df = df.reset_index()[df.columns]
    
    year = 365
    premiums = df[prem_price_use].values # 'Last' or 'Mid'
    strikes = df['Strike'].values
    time_to_expirations = df['DTE'].values
    ivs = df['IV'].values
    underlying = df['Underlying_Price'].values[0]
    types = df['Type'].values

    # Make sure nothing thows up
    assert len(premiums) == len(strikes)
    assert len(strikes) == len(time_to_expirations)

    sigmas = []
    deltas = []
    gammas = []
    thetas = []
    vegas = []
    for premium, strike, time_to_expiration, flag in zip(premiums, strikes, time_to_expirations, types):

        # Constants
        P = premium
        S = underlying
        K = strike
        t = time_to_expiration/float(year)
        r = 0.005 / 100
        q = 0 / 100
        try:
            sigma = py_vollib.black_scholes_merton.implied_volatility.implied_volatility(P, S, K, t, r, q, flag[0])
            sigmas.append(sigma)
        except:
            sigma = 0.0
            sigmas.append(sigma)

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

    ivs = np.array(sigmas)
    df['Calc IV'] = ivs
    df['Delta'] = deltas
    df['Gamma'] = gammas
    df['Theta'] = thetas
    df['Vega'] = vegas
    df = df.dropna()

    expiry_filter = df.sort_values('DTE')['DTE'].drop_duplicates().values[min(expiry_set, 
                                                                              len(df.sort_values('DTE')['DTE'].drop_duplicates()))]

    calls = df[(abs(df['Delta']) >= delta_filter) & 
               (df['Type'] == 'call') & 
               (df['DTE'] == expiry_filter)].reset_index()[df.columns]
    puts = df[(abs(df['Delta']) >= delta_filter) & 
              (df['Type'] == 'put') & 
              (df['DTE'] == expiry_filter)].reset_index()[df.columns]
    
    return calls, puts

def price_sim(options_df, price_change, vol_change, days_change, iv_tag = 'Calc IV', output = 'All',
              skew = 'flat'):
    '''
    output types can be: All, Price, Delta, Gamma, Vega, Theta
    skew types can be: flat, left, right, smile
    '''
    year = 365
    strikes = options_df['Strike'].values
    time_to_expirations = options_df['DTE'].values
    ivs = options_df[iv_tag].values
    underlying = options_df['Underlying_Price'].values[0]
    types = options_df['Type'].values

    # Tweaking changes
    prices = []
    deltas = []
    gammas = []
    thetas = []
    vegas = []
    for sigma, strike, time_to_expiration, flag in zip(ivs, strikes, time_to_expirations, types):

        # Constants
        S = underlying*(1 + price_change)
        t = max(time_to_expiration - days_change, 0)/float(year)
        K = strike
        r = 0.005 / 100
        q = 0 / 100
        
        if skew == 'flat':
            sigma = sigma + vol_change
        elif skew == 'right':
            sigma = sigma + vol_change + vol_change*(K/S - 1)
        elif skew == 'left':
            sigma = sigma + vol_change - vol_change*(K/S - 1)
        else:
            sigma = sigma + vol_change + vol_change*abs(K/S - 1)
        
        if (output == 'All') or (output == 'Price'):
            if days_change == time_to_expiration:
                if flag == 'call':
                    price = max(S - K, 0.0)
                else:
                    price = max(K - S, 0.0)
                prices.append(price)
            else:
                try:
                    price = py_vollib.black_scholes_merton.black_scholes_merton(flag[0], S, K, t, r, sigma, q)
                    prices.append(price)
                except:
                    price = 0.0
                    prices.append(price)
                    
        if (output == 'All') or (output == 'Delta'):
            try:
                delta = py_vollib.black_scholes_merton.greeks.analytical.delta(flag[0], S, K, t, r, sigma, q)
                deltas.append(delta)
            except:
                delta = 0.0
                deltas.append(delta)
        
        if (output == 'All') or (output == 'Gamma'):
            try:
                gamma = py_vollib.black_scholes_merton.greeks.analytical.gamma(flag[0], S, K, t, r, sigma, q)
                gammas.append(gamma)
            except:
                gamma = 0.0
                gammas.append(gamma)
            
        if (output == 'All') or (output == 'Theta'):
            try:
                theta = py_vollib.black_scholes_merton.greeks.analytical.theta(flag[0], S, K, t, r, sigma, q)
                thetas.append(theta)
            except:
                theta = 0.0
                thetas.append(theta)
        
        if (output == 'All') or (output == 'Vega'):
            try:
                vega = py_vollib.black_scholes_merton.greeks.analytical.vega(flag[0], S, K, t, r, sigma, q)
                vegas.append(vega)
            except:
                vega = 0.0
                vegas.append(vega)
            
    df = options_df[['Strike','DTE','Type','Cost','Underlying_Price']]
    if (output == 'All') or (output == 'Price'):
        df['Simulated Price'] = prices
        df['Price Change'] = df['Simulated Price']/df['Cost'] - 1
    if (output == 'All') or (output == 'Delta'):
        df['Delta'] = deltas
    if (output == 'All') or (output == 'Gamma'):
        df['Gamma'] = gammas
    if (output == 'All') or (output == 'Theta'):
        df['Theta'] = thetas
    if (output == 'All') or (output == 'Vega'):
        df['Vega'] = vegas
    df = df.dropna()
    return df

def position_sim(position_df, holdings, price_change, vol_change, dte_change, iv_tag = 'Calc IV', output = 'All',
                 skew = 'flat'):
    position = position_df
    position['Pos'] = holdings
    position_dict = {}
    position_dict['Total Cost'] = sum(position['Cost']*position['Pos'])
    #position_dict['Original Delta'] = sum(position['Delta']*position['Pos'])
    #position_dict['Original Gamma'] = sum(position['Gamma']*position['Pos'])
    #position_dict['Original Theta'] = sum(position['Theta']*position['Pos'])
    #position_dict['Original Vega'] = sum(position['Vega']*position['Pos'])
    
    if (output == 'PnL') or (output == 'Percent Return'):
        simulation = price_sim(position, price_change, vol_change, dte_change, iv_tag, 'Price', skew)
    else:
        simulation = price_sim(position, price_change, vol_change, dte_change, iv_tag, output, skew)
    
    if (output == 'All') or (output == 'PnL') or (output == 'Percent Return'):
        position_dict['Simulated Price'] = sum(simulation['Simulated Price']*position['Pos'])
        position_dict['PnL'] = sum(simulation['Simulated Price']*position['Pos']) - position_dict['Total Cost']
        if position_dict['Total Cost'] > 0:
            position_dict['Percent Return'] = position_dict['PnL']/position_dict['Total Cost']
        else:
            position_dict['Percent Return'] = -position_dict['PnL']/position_dict['Total Cost']
            
    if (output == 'All') or (output == 'Delta'):
        position_dict['Simulated Delta'] = sum(simulation['Delta']*position['Pos'])
        
    if (output == 'All') or (output == 'Gamma'):
        position_dict['Simulated Gamma'] = sum(simulation['Gamma']*position['Pos'])
        
    if (output == 'All') or (output == 'Theta'):
        position_dict['Simulated Theta'] = sum(simulation['Theta']*position['Pos'])
        
    if (output == 'All') or (output == 'Vega'):
        position_dict['Simulated Vega'] = sum(simulation['Vega']*position['Pos'])
    
    outframe = pd.DataFrame(position_dict, index = [vol_change])
    return outframe