# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 17:26:52 2018

@author: Fang
"""

# Note to import from .py files, must follow structure
# from <.py filename excluding '.py'> import <class name>

# Importing necessary models
import pandas as pd
import numpy as np
from six.moves import urllib
import time
import datetime as dt

# Using plotly api_key credentials
# plotly.tools.set_credentials_file(username='aspiringfastlaner', api_key='')

cookier = urllib.request.HTTPCookieProcessor()
opener = urllib.request.build_opener(cookier)
urllib.request.install_opener(opener)

class datacollect:
        
    # Use six to import urllib so it is working for Python2/3
    
    # If you don't want to use six, please comment out the line above
    # and use the line below instead (for Python3 only).
    #import urllib.request, urllib.parse, urllib.error

    '''
    Starting on May 2017, Yahoo financial has terminated its service on
    the well used EOD data download without warning. This is confirmed
    by Yahoo employee in forum posts.
    Yahoo financial EOD data, however, still works on Yahoo financial pages.
    These download links uses a "crumb" for authentication with a cookie "B".
    This code is provided to obtain such matching cookie and crumb.
    '''
    
    # Downloading directly from yahoo finance spx or vvix data
    def yahoo_historical(ticker = 'SPX'):
        # Using requests to ping yahoo finance to retrieve 
        # historical data table
        
        # Cookie and corresponding crumb
        _cookie = None
        _crumb = None
        def get_crumb():
            '''
            This function perform a query and extract the matching cookie and crumb.
            '''
    
            # Perform a Yahoo financial lookup on SP500
            req = urllib.request.Request('https://finance.yahoo.com/quote/^GSPC', 
                                         headers =  {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'})
            f = urllib.request.urlopen(req)
            alines = f.read().decode('utf-8')
    
            # Extract the crumb from the response
            global _crumb
            cs = alines.find('CrumbStore')
            cr = alines.find('crumb', cs + 10)
            cl = alines.find(':', cr + 5)
            q1 = alines.find('"', cl + 1)
            q2 = alines.find('"', q1 + 1)
            crumb = alines[q1 + 1:q2]
            _crumb = crumb
    
            # Extract the cookie from cookiejar
            global cookier, _cookie
            for c in cookier.cookiejar:
                if c.domain != '.yahoo.com':
                    continue
                if c.name != 'B':
                    continue
            _cookie = c.value
    
            # Print the cookie and crumb
            # print('Cookie:', _cookie)
            # print('Crumb:', _crumb)
            return _crumb

        if ticker == 'VVIX':
            site = 'https://query1.finance.yahoo.com/v7/finance/download/%5EVVIX?period1=1167811200&period2=' + str(int(time.time())) + '&interval=1d&events=history&crumb=' + get_crumb().replace('\\','')
        else:
            site = 'https://query1.finance.yahoo.com/v7/finance/download/%5EGSPC?period1=-630950400&period2=' + str(int(time.time())) + '&interval=1d&events=history&crumb=' + get_crumb().replace('\\','')

        df = pd.read_csv(site)
        return df

    # Reading in Data
    # Reading VIX data from CBOE directly
    # VIX is stored as 3 separate files on CBOE's website
    #   2004 to present : http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vixcurrent.csv
    #   1990 to 2003    : http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vixarchive.xls
    #   1986 to 2003 VXO: http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vxoarchive.xls

    # First read raw files directly 
    vix_present = pd.read_csv('http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vixcurrent.csv').dropna()
    # vix_old = pd.read_excel('http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vixarchive.xls').dropna()
    vxo_old = pd.read_excel('http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vxoarchive.xls').dropna()

    # Function for cleaning CBOE VIX data
    def clean_cboe(df):
        df.columns = ['Date','Open','High','Low','Close']
        df = df[1:]
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index(pd.DatetimeIndex(df['Date']))
        return df[['Open','High','Low','Close']]

    # Applying clean_cboe to vix data
    vix_present = clean_cboe(vix_present)
    # vix_old = clean_cboe(vix_old)
    vxo_old = clean_cboe(vxo_old)

    # Currently the vix_old dataframe doesn't have the Open prices so VXO will be used to proxy VIX prior
    # to 2003
    vix = pd.concat([vxo_old,vix_present],axis = 0)

    # Reading SKEW Index data directly from CBOE
    skew = pd.read_csv('https://www.cboe.com/publish/scheduledtask/mktdata/datahouse/skewdailyprices.csv')
    skew_raw = skew.copy()
    skew.columns = ['Date','Skew','na1','na2']
    skew = skew[1:]
    skew['Date'] = pd.to_datetime(skew['Date'])
    skew = skew.set_index(pd.DatetimeIndex(skew['Date']))[['Skew']]
    skew['skew'] = -(pd.to_numeric(skew['Skew'], downcast='float') - 100)/10
    del skew['Skew']

    # Reading in SPX Data
    spx = yahoo_historical()
    spx = spx.set_index(pd.DatetimeIndex(spx['Date']))[['Open','High','Low','Close','Adj Close']]

    # Reading in VVIX Data
    # vvix = yahoo_historical('VVIX')
    # vvix = vvix.set_index(pd.DatetimeIndex(vvix['Date']))[['Open','High','Low','Close','Adj Close']]

    # Joining all index together to one dataframe
    spx = spx[['Open','Close']]
    spx.columns = ['SPX ' + s for s in spx.columns.tolist()]

    vix = vix[['Open','Close']]
    vix.columns = ['VIX ' + s for s in vix.columns.tolist()]

    # vvix = vvix[['Open','Close']]
    # vvix.columns = ['VVIX ' + s for s in vvix.columns.tolist()]

    #
    df = pd.concat([spx,vix,skew],axis = 1).dropna() # Currently excluding VVIX

    # An error in data: 2000-10-18 VIX Close value is a string, converting to float
    df['VIX Close'][2714] = 32.5

    # Fixing VIX values so that they are floats
    df['VIX Close'] = df['VIX Close'].astype('float')
    df['VIX Open'] = df['VIX Open'].astype('float')

    # Adjusting VIX so that it's on 252 trading days
    df['Daily VIX Open'] = np.sqrt(((df['VIX Open']*df['VIX Open'])/365)*1.5)/100
    df['Daily VIX Close'] = np.sqrt(((df['VIX Close']*df['VIX Close'])/365)*1.5)/100

    # Cleaning up unused dataframes
    del skew, spx, vix, vix_present, vxo_old
    
    def vixterm():
        vix = datacollect.df[['VIX Close']]
        v1 = pd.read_csv('http://www.quandl.com/api/v1/datasets/CHRIS/CBOE_VX1.csv')
        v2 = pd.read_csv('http://www.quandl.com/api/v1/datasets/CHRIS/CBOE_VX2.csv')
        v1 = v1.set_index(pd.DatetimeIndex(v1['Trade Date']))[['Settle']]
        v2 = v2.set_index(pd.DatetimeIndex(v2['Trade Date']))[['Settle']]
        v1.index.name = 'Date'
        v2.index.name = 'Date'
        v1.columns = ['V1']
        v2.columns = ['V2']
        vixdf = pd.concat([vix,v1,v2], axis = 1)
        
        # Previous Third Wed Days
        
        # Getting Previous Eight Day
        vixdf['month'] = vixdf.index.month
        vixdf['year'] = vixdf.index.year
        vixdf['day'] = 7
        vixdf['eigth_day'] = pd.to_datetime(vixdf[['day', 'month', 'year']])
        # Getting Previous Third Weekday
        vixdf['day'] = 3
        vixdf['third_weekday'] = pd.to_datetime(vixdf[['day', 'month', 'year']]).dt.weekday
        vixdf['prev_wed'] = vixdf['eigth_day'] - pd.to_timedelta(vixdf['third_weekday'], unit = 'day') + dt.timedelta(14) - dt.timedelta(30)
        #df['START_DATE'] + df['MONTHS'].values.astype("timedelta64[M]")
        
        # Current Third Wed Days
        
        # Getting Previous Eight Day
        vixdf['month'] = np.where(vixdf.index.month < 12, vixdf.index.month + 1, 1)
        vixdf['year'] = np.where(vixdf.index.month < 12, vixdf.index.year, vixdf.index.year + 1)
        vixdf['day'] = 7
        vixdf['eigth_day'] = pd.to_datetime(vixdf[['day', 'month', 'year']])
        # Getting Previous Third Weekday
        vixdf['day'] = 3
        vixdf['third_weekday'] = pd.to_datetime(vixdf[['day', 'month', 'year']]).dt.weekday
        vixdf['curr_wed'] = vixdf['eigth_day'] - pd.to_timedelta(vixdf['third_weekday'], unit = 'day') + dt.timedelta(14) - dt.timedelta(30)
        
        # Next Third Wed Days
        
        # Getting Previous Eight Day
        vixdf['month'] = np.where(vixdf['month'] < 12, vixdf['month'] + 1, 1)
        vixdf['year'] = np.where(vixdf.index.month < 11, vixdf.index.year, vixdf.index.year + 1)
        vixdf['day'] = 7
        vixdf['eigth_day'] = pd.to_datetime(vixdf[['day', 'month', 'year']])
        # Getting Previous Third Weekday
        vixdf['day'] = 3
        vixdf['third_weekday'] = pd.to_datetime(vixdf[['day', 'month', 'year']]).dt.weekday
        vixdf['next_wed'] = vixdf['eigth_day'] - pd.to_timedelta(vixdf['third_weekday'], unit = 'day') + dt.timedelta(14) - dt.timedelta(30)
        
        # (vixdf.index - vixdf['curr_wed']).dt.days
        vixdf['dte'] = np.where(vixdf.index <= vixdf['curr_wed'], (vixdf['curr_wed'] - vixdf.index).dt.days, 
                                (vixdf['next_wed'] - vixdf.index).dt.days)
        vixdf['term'] = np.where(vixdf.index <= vixdf['curr_wed'], (vixdf['curr_wed'] - vixdf['prev_wed']).dt.days, 
                                (vixdf['next_wed'] - vixdf['curr_wed']).dt.days)
        vixdf['spot wgt'] = vixdf['dte']/vixdf['term']
        vixdf['front wgt'] = 1 - vixdf['spot wgt']
        vixdf['Contango'] = vixdf['spot wgt']*(vixdf['VIX Close']/vixdf['V1']) + vixdf['front wgt']*(vixdf['V1']/vixdf['V2'])
        
        vixdf = vixdf[['VIX Close', 'V1', 'V2', 'Contango']]
        return vixdf
    
    curr_table = pd.concat([df[['SPX Close']], vixterm()], axis = 1)
    curr_table['RV'] = ((np.log(curr_table['SPX Close'].shift(-1))-np.log(curr_table['SPX Close'])).rolling(20).std()*np.sqrt(252)*100).shift(1)
