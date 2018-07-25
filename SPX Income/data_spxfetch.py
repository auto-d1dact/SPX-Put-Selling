# Import required libraries
import datetime as dt

import numpy as np
import pandas as pd
import pandas.stats.moments as st

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

def get_daily_data():
    spx_daily = historical_data('SPX')

    vix_daily = pd.read_csv('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=VIX&apikey=5HZEUI5AFJB06BUK&datatype=csv&outputsize=full', index_col = 0)
    
    daily_df = np.round(vix_daily[['open','close']].join(spx_daily,how = 'inner', lsuffix='_vix').sort_index(),3)
    daily_df.columns = ['VIX Open', 'VIX Close','SPX Open','SPX Close','Daily Return','Intraday Return',
                        'Overnight Return','Daily Vol','Intraday Vol','Overnight Vol','Daily Annual Vol',
                        'Intraday Annual Vol','Overnight Annual Vol',
                        'Open-Close Difference','Daily Dollar Vol','Daily Dollar Std',
                        'Daily Dollar Std Direction']
    
    vf_df = pd.read_csv('http://173.212.203.121/noko.csv', index_col = 0)[['F1','F2','F3']]
    vf_df.index = pd.to_datetime(vf_df.index)
    
    vix_df = vix_daily[['close']].join(vf_df, how = 'inner').sort_index()
    vix_df.columns = ['VIX','F1','F2','F3']
    
    contango_ratio = []
    
    vix_df.index = pd.to_datetime(vix_df.index)
    for i, row in vix_df.iterrows():
        weights = maturities(i.date())
        curr_ratio = weights[0]*(row.VIX/row.F1) + weights[1]*(row.F1/row.F2)
        contango_ratio.append(round(curr_ratio,3))
    
    vix_df['Contango'] = contango_ratio
    
    return daily_df, vix_df

def get_intraday_data():
    spx_intraday_link = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=SPX&interval=1min&apikey=5HZEUI5AFJB06BUK&datatype=csv'#&outputsize=full'
    spx_intraday = pd.read_csv(spx_intraday_link, index_col = 0)[['open','high','low','close']]
    
    vix_intraday_link = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=VIX&interval=1min&apikey=5HZEUI5AFJB06BUK&datatype=csv'#&outputsize=full'
    vix_intraday = pd.read_csv(vix_intraday_link, index_col = 0)[['open','high','low','close']]
    
    intraday_df = np.round(vix_intraday.join(spx_intraday, how='inner', lsuffix='_vix', rsuffix='_spx'),2).sort_index()
    intraday_df.columns = ['VIX Open','VIX High','VIX Low', 'VIX Close', 'SPX Open', 'SPX High', 'SPX Low', 'SPX Close']
    
    rolling_window = 20
    
    intraday_vol = intraday_df[['SPX Close']]
    intraday_vol['Log Return'] = np.log(intraday_vol['SPX Close']/intraday_vol['SPX Close'].shift(1))
    intraday_vol['Return Std'] = intraday_vol['Log Return'].rolling(window=rolling_window,center=False).std()
    intraday_vol['Dollar Std'] = intraday_vol['Return Std']*intraday_vol['SPX Close']
    intraday_vol['Dollar Std Move'] = (intraday_vol['SPX Close'] - intraday_vol['SPX Close'].shift(1))/intraday_vol['Dollar Std'].shift(1)
    intraday_df['Dollar Std Move'] = intraday_vol['Dollar Std Move']
    
    return intraday_df