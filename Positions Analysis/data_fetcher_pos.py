# Import required libraries
import datetime as dt

#import numpy as np
import pandas as pd
#from pandas_datareader.data import Options
import numpy as np
import py_vollib
from py_vollib.black_scholes_merton.implied_volatility import *
from py_vollib.black_scholes_merton.greeks.analytical import *

from pandas.io.json import json_normalize
from pandas_datareader.data import Options 

import urllib.request as req


# Getting Options Data
def all_options(ticker, dte_ub, dte_lb, moneyness = 0.03):
    tape = Options(ticker, 'yahoo')
    data = tape.get_all_data().reset_index()
    
    data['Moneyness'] = np.abs(data['Strike'] - data['Underlying_Price'])/data['Underlying_Price']
    
    data['DTE'] = (data['Expiry'] - dt.datetime.today()).dt.days
    data = data[['Strike', 'DTE', 'Type', 'IV', 'Underlying_Price',
                 'Last','Bid','Ask', 'Moneyness']]
    data['Mid'] = (data['Ask'] - data['Bid'])/2 + data['Bid']
    data = data.dropna()
    data = data[(abs(data['Moneyness']) <= moneyness) &
                (data['DTE'] <= dte_ub) &
                (data['DTE'] >= dte_lb)]
    return data.sort_values(['DTE','Type']).reset_index()[data.columns]


def greek_calc(df, prem_price_use = 'Mid', day_format = 'trading', interest_rate = 0.0193, dividend_rate = 0):
    if prem_price_use != 'Mid':
        price_col = 'Last'
    else:
        price_col = 'Mid'
        
    if day_format != 'trading':
        year = 365
    else:
        year = 252
    
    premiums = df[price_col].values
    strikes = df['Strike'].values
    time_to_expirations = df['DTE'].values
    ivs = df['IV'].values
    underlying = df['Underlying_Price'].values[0]
    types = df['Type'].values

    deltas = []
    gammas = []
    thetas = []
    rhos = []
    vegas = []
    for premium, strike, time_to_expiration, flag, iv in zip(premiums, strikes, time_to_expirations, types, ivs):

        # Constants
        S = underlying
        K = strike
        t = time_to_expiration/float(year)
        r = interest_rate
        q = dividend_rate
        try:
            rho = py_vollib.black_scholes_merton.greeks.analytical.rho(flag[0], S, K, t, r, iv, q)
        except:
            rho = 0.0
        rhos.append(rho)

        try:
            delta = py_vollib.black_scholes_merton.greeks.analytical.delta(flag[0], S, K, t, r, iv, q)
        except:
            delta = 0.0
        deltas.append(delta)

        try:
            gamma = py_vollib.black_scholes_merton.greeks.analytical.gamma(flag[0], S, K, t, r, iv, q)
        except:
            gamma = 0.0
        gammas.append(gamma)

        try:
            theta = py_vollib.black_scholes_merton.greeks.analytical.theta(flag[0], S, K, t, r, iv, q)
        except:
            theta = 0.0
        thetas.append(theta)

        try:
            vega = py_vollib.black_scholes_merton.greeks.analytical.vega(flag[0], S, K, t, r, iv, q)
        except:
            vega = 0.0
        vegas.append(vega)

    df['Delta'] = deltas
    df['Gamma'] = gammas
    df['Theta'] = thetas
    df['Vega'] = vegas
    df['Rho'] = rhos
    # df = df.dropna()
    
    return df


def price_sim(options_df, price_change, vol_change, days_change, output = 'All',
              skew = 'flat', day_format = 'trading', interest_rate = 0.0193, dividend_rate = 0,
              prem_price_use = 'Mid'):
    '''
    output types can be: All, Price, Delta, Gamma, Vega, Theta
    skew types can be: flat, left, right, smile
    '''
    if prem_price_use != 'Mid':
        price_col = 'Last'
    else:
        price_col = 'Mid'
        
    if day_format != 'trading':
        year = 365
    else:
        year = 252
        
    strikes = options_df['Strike'].values
    time_to_expirations = options_df['DTE'].values
    ivs = options_df['IV'].values
    underlying = options_df['Underlying_Price'].values[0]
    types = options_df['Type'].values

    # Tweaking changes
    prices = []
    deltas = []
    gammas = []
    thetas = []
    vegas = []
    rhos = []
    for sigma, strike, time_to_expiration, flag in zip(ivs, strikes, time_to_expirations, types):

        # Constants
        S = underlying*(1 + price_change)
        t = max(time_to_expiration - days_change, 0)/float(year)
        K = strike
        r = interest_rate
        q = dividend_rate
        
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
                except:
                    price = 0.0
                prices.append(price)
                    
        if (output == 'All') or (output == 'Delta'):
            try:
                delta = py_vollib.black_scholes_merton.greeks.analytical.delta(flag[0], S, K, t, r, sigma, q)
            except:
                delta = 0.0
            deltas.append(delta)
        
        if (output == 'All') or (output == 'Gamma'):
            try:
                gamma = py_vollib.black_scholes_merton.greeks.analytical.gamma(flag[0], S, K, t, r, sigma, q)
            except:
                gamma = 0.0
            gammas.append(gamma)
            
        if (output == 'All') or (output == 'Theta'):
            try:
                theta = py_vollib.black_scholes_merton.greeks.analytical.theta(flag[0], S, K, t, r, sigma, q)
            except:
                theta = 0.0
            thetas.append(theta)
        
        if (output == 'All') or (output == 'Vega'):
            try:
                vega = py_vollib.black_scholes_merton.greeks.analytical.vega(flag[0], S, K, t, r, sigma, q)
            except:
                vega = 0.0
            vegas.append(vega)
        if (output == 'All') or (output == 'Rho'):
            try:
                rho = py_vollib.black_scholes_merton.greeks.analytical.rho(flag[0], S, K, t, r, sigma, q)
            except:
                rho = 0.0
            rhos.append(rho)
            
    df = options_df[['Strike','DTE','Type',price_col,'Underlying_Price']]
    df['Simulated Price'] = prices
    df['Price Change'] = df['Simulated Price']/(df[price_col]) - 1
    if (output == 'All') or (output == 'Delta'):
        df['Delta'] = deltas
    if (output == 'All') or (output == 'Gamma'):
        df['Gamma'] = gammas
    if (output == 'All') or (output == 'Theta'):
        df['Theta'] = thetas
    if (output == 'All') or (output == 'Vega'):
        df['Vega'] = vegas
    if (output == 'All') or (output == 'Rho'):
        df['Rho'] = rhos
    df = df.dropna()
    return df

def position_sim(position_df, holdings, shares,
                 price_change, vol_change, dte_change, output = 'All',
                 skew = 'flat', prem_price_use = 'Mid', day_format = 'trading', 
                 interest_rate = 0.0193, dividend_rate = 0):
    
    if prem_price_use != 'Mid':
        price_col = 'Last'
    else:
        price_col = 'Mid'
                
    position = position_df
    position['Pos'] = holdings
    position_dict = {}
    position_dict['Total Cost'] = sum(position[price_col]*position['Pos'])*100 + shares*position['Underlying_Price'].values[0]
    
    simulation = price_sim(position, price_change, vol_change, dte_change, output,
                           skew, day_format, interest_rate, dividend_rate,
                           prem_price_use)
    
    if (output == 'All') or (output == 'PnL') or (output == 'Percent Return'):
        position_dict['Simulated Price'] = sum(simulation['Simulated Price']*position['Pos'])*100 + shares*position['Underlying_Price'].values[0]*(1 + price_change)
        position_dict['PnL'] = position_dict['Simulated Price'] - position_dict['Total Cost']
        if position_dict['Total Cost'] > 0:
            position_dict['Percent Return'] = position_dict['PnL']/position_dict['Total Cost']
        else:
            position_dict['Percent Return'] = -position_dict['PnL']/position_dict['Total Cost']
            
    if (output == 'All') or (output == 'Delta'):
        position_dict['Simulated Delta'] = sum(simulation['Delta']*position['Pos']) + shares/100
        
    if (output == 'All') or (output == 'Gamma'):
        position_dict['Simulated Gamma'] = sum(simulation['Gamma']*position['Pos'])
        
    if (output == 'All') or (output == 'Theta'):
        position_dict['Simulated Theta'] = sum(simulation['Theta']*position['Pos'])
        
    if (output == 'All') or (output == 'Vega'):
        position_dict['Simulated Vega'] = sum(simulation['Vega']*position['Pos'])
        
    if (output == 'All') or (output == 'Rho'):
        position_dict['Simulated Rho'] = sum(simulation['Rho']*position['Pos'])
    
    outframe = pd.DataFrame(position_dict, index = [vol_change])
    return outframe