# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 21:28:57 2018

@author: Fang
"""

import pandas as pd
import datetime as dt
import json
import numpy as np
from pandas.io.json import json_normalize
import urllib.request as urlreq

# Creating class for querying yahoo data
# yahoo_query(str[self.ticker], datetime.date([starting_date]), datetime.date([ending_date])):
class yahoo_query:
    
    # Initializing yahoo_query class with self.ticker and creating
    # relevant URL api calls to query relevant data
    def __init__(self, ticker, start_date, end_date = dt.datetime.today()):
        start_date_unix = int(start_date.timestamp())
        end_date_unix = int(end_date.timestamp())
        
        self.ticker = ticker
        self.minute_url = 'https://query1.finance.yahoo.com/v8/finance/chart/{0}?symbol={0}&interval=1m'.format(self.ticker)
        self.hist_price_url = 'https://query1.finance.yahoo.com/v8/finance/chart/{0}?symbol={0}&period1={1}&period2={2}&interval=1d'.format(self.ticker,start_date_unix,end_date_unix)
        self.options_url = 'https://query1.finance.yahoo.com/v7/finance/options/{}'.format(self.ticker)
        self.quick_summary_url = 'https://query1.finance.yahoo.com/v7/finance/quote?symbols={}'.format(self.ticker)
        self.earnings_management_url = 'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}?modules=assetProfile%2CearningsHistory'.format(self.ticker)
        self.fin_statements_url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={}&fields=ebitda,shortRatio,priceToSales".format(self.ticker)
    
    # Class method for querying yahoo minute data using
    # minute_url defined on initialization
    def minute_query(self):
        with urlreq.urlopen(self.minute_url) as url:
            data = json.loads(url.read().decode())
            self.minute_prices = pd.DataFrame(data['chart']['result'][0]['indicators']['quote'][0],
                                            index = [dt.datetime.utcfromtimestamp(int(x)) - 
                                                     dt.timedelta(hours = 4) for x in 
                                                     data['chart']['result'][0]['timestamp']])
            self.minute_prices.index = pd.to_datetime(self.minute_prices.index)
            self.minute_prices.columns = ["{0}_{1}".format(self.ticker, x) for x in self.minute_prices.columns]
            
    # Class method for querying yahoo historical prices
    # using hist_price_url on initialization
    def hist_prices_query(self):
        with urlreq.urlopen(self.hist_price_url) as url:
            data = json.loads(url.read().decode())
            self.hist_prices = pd.DataFrame(data['chart']['result'][0]['indicators']['quote'][0],
                                            index = [dt.datetime.utcfromtimestamp(int(x)).date() for x in 
                                                     data['chart']['result'][0]['timestamp']])
            self.hist_prices.index = pd.to_datetime(self.hist_prices.index)
            self.hist_prices.columns = ["{0}_{1}".format(self.ticker, x) for x in self.hist_prices.columns]
            
    # Class method for querying yahoo earnings data
    # using earnings_management_url on initialization
    def earnings_query(self):
        with urlreq.urlopen(self.earnings_management_url) as url:
            data = json.loads(url.read().decode())
            earnings_history = pd.concat([pd.DataFrame(quarter_earnings).loc['raw'] for 
                                          quarter_earnings in 
                                          data['quoteSummary']['result'][0]['earningsHistory']['history']],
                                         axis = 1).T
            earnings_history.index = pd.to_datetime([dt.datetime.utcfromtimestamp(int(x)).date() for 
                                                     x in earnings_history['quarter'].tolist()])
            self.earnings_history = earnings_history.drop(['period','maxAge','quarter'], axis = 1)
            
            # Additional data figure assignments from same api call
            self.profile = pd.DataFrame(dict((k, data['quoteSummary']['result'][0]['assetProfile'][k]) for 
                                             k in ('industry', 'sector', 'fullTimeEmployees', 'auditRisk', 
                                                   'boardRisk', 'compensationRisk', 'shareHolderRightsRisk', 
                                                   'overallRisk')), index = [self.ticker])
            
            executives = pd.concat([pd.DataFrame(executive).loc['raw'] for 
                                    executive in data['quoteSummary']['result'][0]['assetProfile']['companyOfficers']],
                                   axis = 1).T
            executives.index = executives.title
            self.executives = executives.drop(['title','maxAge','yearBorn'], axis = 1)
            
        
    # Class method for querying most near-term options chain
    # using  options_url on initialization
    def latest_options_query(self):
        with urlreq.urlopen(self.options_url) as url:
            data = json.loads(url.read().decode())
            options = data['optionChain']['result'][0]['options'][0]
            options = pd.merge(json_normalize(options['calls']), json_normalize(options['puts']), how='inner', on = 'strike',
                               suffixes=('_calls', '_puts'))
            options['expiry'] = dt.datetime.utcfromtimestamp(options['expiration_calls'][0]).date()

            self.options = options.drop(['expiration_calls','expiration_puts','contractSize_calls',
                                         'currency_calls','contractSize_puts','currency_puts',
                                         'lastTradeDate_calls', 'lastTradeDate_puts', 'percentChange_calls',
                                         'percentChange_puts'], axis = 1)
            self.options.index = self.options.strike
            
    # Class method for querying quick quote summary using
    # quick_summary_url on initialzation
    def quick_quote_query(self):
        with urlreq.urlopen(self.quick_summary_url) as url:
            data = json.loads(url.read().decode())
            self.quick_quote = pd.DataFrame(data['quoteResponse']['result'][0], index = [self.ticker])
            for col in ['dividendDate','earningsTimestamp',
                        'earningsTimestampEnd', 'earningsTimestampStart']:
                self.quick_quote.loc[self.ticker,col] = dt.datetime.utcfromtimestamp(int(self.quick_quote.loc[self.ticker,col])).date()
    
    # Class method for querying financials quote summary using
    # fin_statements_url on initialization
    def financials_query(self):
        with urlreq.urlopen(self.fin_statements_url) as url:
            data = json.loads(url.read().decode())
            self.financials = pd.DataFrame(data['quoteResponse']['result'][0], index = [self.ticker])