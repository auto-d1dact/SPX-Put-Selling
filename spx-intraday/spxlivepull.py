# -*- coding: utf-8 -*-
"""
Created on Wed Jul 25 13:01:29 2018

@author: Fang
"""

import pandas as pd
import numpy as np
import datetime as dt
import pandas.stats.moments as st
import time
import os
from lxml import html
import requests
import webbrowser
import csv
from bs4 import BeautifulSoup as bs
from pytz import timezone
tz = timezone('US/Eastern')
os.chdir('D:\Options Data\SPX Intraday')

def curr_spx_data():
    yahoo_url = 'https://finance.yahoo.com/quote/%5ESPX/history?p=%5ESPX'

    soup = bs(requests.get(yahoo_url).text, "lxml")

    table = soup.find_all('table')[0]

    i = 0

    for row in table.find_all('tr'):
        if i == 2:
            break
        else:
            individual_row = str(row).split('\n')
            i += 1
            
    curr_spx = [float(x.split('>')[-1].replace(',','')) for x in individual_row[0].split('</span>')[1:-2]]
    if len(curr_spx) == 0:
        curr_spx = float(individual_row[0].split('/td>')[1:-2][1].split('>')[-1].replace('<','').replace(',',''))
        table_dict = {'Last': [curr_spx]}
    else:
        table_dict = {'Open':[curr_spx[0]],
                      'High':[curr_spx[1]],
                      'Low':[curr_spx[2]],
                      'Last':[curr_spx[3]]}

    table = pd.DataFrame(table_dict)
    temp_date = dt.datetime.now(tz).replace(second=0,microsecond=0)
    table['Datetime'] = dt.datetime(temp_date.year,temp_date.month,temp_date.day,temp_date.hour,temp_date.minute)    
    table.index = table['Datetime']
    return table[['Last']]


current_time = dt.datetime.now(tz).strftime('%Y-%m-%d')
spx_filename = 'spx_' + current_time +'.csv'

if os.path.isfile(spx_filename):
    with open(spx_filename, 'a') as f:
        curr_spx_data().to_csv(f, header=False)
else:
    with open(spx_filename, 'a') as f:
        spx_intraday_link = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=SPX&interval=1min&apikey=5HZEUI5AFJB06BUK&datatype=csv'#&outputsize=full'
        spx_intraday = pd.read_csv(spx_intraday_link, index_col = 0)[['close']]
        spx_intraday.columns = ['Last']
        curr_spx_data = curr_spx_data()
        curr_spx_data = pd.concat([spx_intraday,curr_spx_data], axis = 0)
        curr_spx_data.index = pd.to_datetime(curr_spx_data.index)
        curr_spx_data = curr_spx_data.sort_index()
        
        new_index = []
        for i in range(len(curr_spx_data))[::-1]:
            new_index.append(pd.to_datetime(curr_spx_data.index[-1]) - dt.timedelta(minutes = i))
        curr_spx_data.index = new_index
        
        curr_spx_data.to_csv(f)
    
f.close()
