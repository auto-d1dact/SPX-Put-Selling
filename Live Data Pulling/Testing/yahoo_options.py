# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 09:15:12 2018
Scheduled function to pull options data from Yahoo Finance. Function
is scheduled to run every weekday from 9:30 am to 4:00 pm.

@author: Fang
"""

# Importing necessary models
import pandas as pd
import os
import time
from pandas_datareader.data import Options
import glob
import sys

# Main function for pulling data 
# Function is default set to ^GSPC ticker but can pull
# any stocks with options chains on yahoo. Note that
# a hack solution for unstacking the multi-index
# dataframe was created by saving down to csv
# and then reading back into function.
def get_options_data(ticker = '^GSPC'):
    tape = Options(ticker, 'yahoo')
    data = tape.get_all_data()
    data.to_csv('raw.csv')
    data = pd.read_csv('raw.csv')
    del data['JSON']
    return data

# Specifying folder for options data collection
# Primary aggregate file is the optionsdata.csv file
# Redundancy set up so that each individual dataframe 
# of options data is also saved as a separate .csv
# file in case of loss of main data file. Each
# datafile 
root = 'C:\\Users\\Fang\\Desktop\\Python Trading\\SPX Option Backtester\\SPX Put Selling\\Live Data Pulling\\Options Data\\'
i = 0
mainfile = 'optionsdata.csv'

# Checks for the latest data_.csv file to pull its
# file number. If not such file exists, initiate
# the file number to start from 0.
list_of_files = glob.glob(root + '*.csv') # * means all if need specific format then *.csv
if len(list_of_files) == 0:
    i = 0
else:
    # Finds the latest file in folder and pulls its last digits
    latest_file = max(list_of_files, key=os.path.getctime)
    i = int(latest_file.split("\\")[-1].split('.')[0][4:])

#%%
# Specify number of minutes to run
minutes = 15
total_trading_seconds = 6.5*60*60
sleep_seconds = minutes*60

i = total_trading_seconds

# Loop to iterate every 15 minutes once script is executed
# The loop terminates when the countdown, i, goes to zero
# which will be 26 times in a day.
while i != 0:
    i += 1
    df = get_options_data()
    if os.path.isfile(root + mainfile) == True:
        df.to_csv(root + mainfile, mode = 'a', header = False)
    else:
        df.to_csv(root + mainfile)
    df.to_csv(root + 'data' + str(i) + '.csv')    
    time.sleep(sleep_seconds)

# Exit program after loop is completed
sys.exit()