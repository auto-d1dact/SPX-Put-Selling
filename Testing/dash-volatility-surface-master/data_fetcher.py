# Import required libraries
import datetime as dt

import numpy as np
import pandas as pd
from pandas_datareader.data import Options
from alpha_vantage.timeseries import TimeSeries
from py_vollib.black_scholes_merton.implied_volatility import *
from alpha_vantage.timeseries import TimeSeries
ts = TimeSeries(key='YOUR_API_KEY',output_format='pandas')

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
def historical_data(ticker, day_number = 252, rolling_window = 20, outsize = 'full'):
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