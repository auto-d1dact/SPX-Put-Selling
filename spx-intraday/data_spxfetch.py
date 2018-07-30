# Import required libraries
import datetime as dt

import numpy as np
import pandas as pd
import os
from pytz import timezone
tz = timezone('US/Eastern')

os.chdir('D:\Options Data\SPX Intraday')

def get_intraday_data():
    
    current_time = dt.datetime.now(tz).strftime('%Y-%m-%d')
    spx_filename = 'spx_' + current_time +'.csv'
    
    intraday_df = pd.read_csv(spx_filename,index_col = 0)
    
    rolling_window = 20
    
    intraday_vol = intraday_df[['Last']]
    intraday_vol['Log Return'] = np.log(intraday_vol['Last']/intraday_vol['Last'].shift(1))
    intraday_vol['Return Std'] = intraday_vol['Log Return'].rolling(window=rolling_window,center=False).std()
    intraday_vol['Dollar Std'] = intraday_vol['Return Std']*intraday_vol['Last']
    intraday_vol['Dollar Std Move'] = (intraday_vol['Last'] - intraday_vol['Last'].shift(1))/intraday_vol['Dollar Std'].shift(1)
    intraday_df['Dollar Std Move'] = intraday_vol['Dollar Std Move']
    
    return intraday_df.dropna()
