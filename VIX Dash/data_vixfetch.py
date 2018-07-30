# Import required libraries
import datetime as dt

import numpy as np
import pandas as pd
from lxml import html as ht
import requests
import webbrowser
from bs4 import BeautifulSoup as bs


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

def vix_data():

    vix_daily = pd.read_csv('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=VIX&apikey=BJ6Y8NWZZE9Q8O59&datatype=csv&outputsize=full', index_col = 0)

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
    
    return vix_df

def intraday_vix_data():

    delayed_cboe_url = 'http://www.cboe.com/delayedquote/futures-quotes'
    soup = bs(requests.get(delayed_cboe_url).text, "lxml")

    table = soup.find_all('table')[1]

    intraday_vx_dict = {}

    intraday_vx_dict['Symbol'] = []
    intraday_vx_dict['Expiration'] = []
    intraday_vx_dict['Last'] = []
    intraday_vx_dict['Change'] = []
    intraday_vx_dict['High'] = []
    intraday_vx_dict['Low'] = []
    intraday_vx_dict['Settlement'] = []
    intraday_vx_dict['Volume'] = []
    intraday_vx_dict['Int'] = []

    i = 1
    for row in table.find_all('tr'):
        # Individual row stores current row item and delimits on '\n'
        individual_row = str(row).split('\n')
        curr_items = list(map(lambda x: x.replace('\r',''),
                              list(map(lambda x: x.replace(' ', ''), 
                                       list(filter(lambda x: '<' not in x, 
                                                   individual_row))))))
        if i == 1:
            i += 1
            continue
        intraday_vx_dict['Symbol'].append(curr_items[0])
        intraday_vx_dict['Expiration'].append(dt.datetime.strptime(curr_items[1], '%m/%d/%Y'))
        intraday_vx_dict['Last'].append(float(curr_items[2]))
        intraday_vx_dict['Change'].append(float(curr_items[3]))
        intraday_vx_dict['High'].append(float(curr_items[4]))
        intraday_vx_dict['Low'].append(float(curr_items[5]))
        intraday_vx_dict['Settlement'].append(float(curr_items[6]))
        intraday_vx_dict['Volume'].append(float(curr_items[7]))
        intraday_vx_dict['Int'].append(int(curr_items[8]))

    intraday_vx = pd.DataFrame(intraday_vx_dict)[['Symbol', 'Expiration', 'Last', 
                                                  'Settlement', 'Change', 'High', 
                                                  'Low', 'Int', 'Volume']]

    intraday_vx = intraday_vx[~intraday_vx["Symbol"].str.contains('VX')].reset_index()[intraday_vx.columns]

    yahoo_url = 'https://finance.yahoo.com/quote/%5EVIX/history?p=^VIX'

    soup = bs(requests.get(yahoo_url).text, "lxml")

    table = soup.find_all('table')[0]

    i = 0

    for row in table.find_all('tr'):
        if i == 2:
            break
        else:
            individual_row = str(row).split('\n')
            i += 1

    vix = [float(x.split('>')[-1]) for x in individual_row[0].split('</span>')[1:-2]]
    
    curr_vix = pd.DataFrame({'High': [vix[1]],
                              'Low': [vix[2]],
                              'Last': [vix[-1]],
                              'Expiration': [dt.datetime.today().date()],
                              'Symbol': ['VIX']})
    
    intraday_vx = pd.concat([curr_vix,intraday_vx],axis = 0)
    intraday_vx.Expiration = pd.to_datetime(intraday_vx.Expiration)
    intraday_vx = intraday_vx.reset_index()[intraday_vx.columns]
    return intraday_vx

def svxy_data():

    svxy_intraday_link = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=SVXY&interval=1min&apikey=BJ6Y8NWZZE9Q8O59&datatype=csv&outputsize=full'
    svxy_intraday = pd.read_csv(svxy_intraday_link, index_col = 0)[['open','high','low','close']]
    svxy_intraday.index = pd.to_datetime(svxy_intraday.index)
    svxy_intraday = svxy_intraday[svxy_intraday.index.day == dt.datetime.today().day]
    return svxy_intraday

def curr_svxy_data():
    yahoo_url = 'https://finance.yahoo.com/quote/SVXY/history?p=SVXY'

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