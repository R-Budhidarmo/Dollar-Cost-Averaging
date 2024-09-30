# functions for DCA study

# import relevant libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import yfinance as yf

def data_fetch(tickers,start,end):

    # tickers = [more than 1 tickers in a list]
    data = yf.download(tickers,start,end)

    # plot the Close price to have an idea of the price movement
    # data['Close'].plot()
    # plt.ylabel('Close Price ($)')

    # calculate daily returns
    data[f'Returns'] = data['Close'].pct_change()
    
    # price at the beginning of the period
    print(f"ETF price at the beginning of the period:\t${round(data['Close'][0],2)}")
    
    # price at the end of the period
    print(f"ETF price at the end of the period:\t\t${round(data['Close'][-1],2)}")
    
    # increase in price over the period
    print(f"ETF returns over the period:\t\t\t{round(((data['Close'][-1]/data['Close'][0])-1)*100,2)}%\n")

    return data

def buy_n_hold(data,total_investment):

    df = data.copy()

    buy_n_hold_capital = round((total_investment * df['Close'][-1] / df['Close'][0]),2)
    print(f'Investment value at the end of the period:\t${buy_n_hold_capital}')

    # the overall percentage returns will be the following
    buy_n_hold_gain = round(((buy_n_hold_capital/total_investment)-1)*100,2)
    print(f'Buy-and-hold return at the end of period:\t{buy_n_hold_gain}%\n')

    buy_n_hold_cumul = cumul_ret(df,df['Returns'],total_investment,contribute=False)

    return buy_n_hold_capital,buy_n_hold_gain,buy_n_hold_cumul

def cumul_ret(data,returns,investment,contribute=False):

    df = data.copy()

    # initiate a new column to calculate the investment value over the 5-year period
    df['Investment Value'] = 0

    # set the first value as the initial contribution
    df.iloc[0,-1] = investment

    # a loop to choose whether to contribute a deposit every month or not
    if contribute == True:
        for i in range(1,len(df)):
            df.iloc[i,-1] = (df['Investment Value'][i-1] * (1 + returns[i])) + df['Monthly Investment'][i]
    else:
        for i in range(1,len(df)):
            df.iloc[i,-1] = df['Investment Value'][i-1] * (1 + df['Returns'][i])
    
    return df['Investment Value']

def dca(data,deposit,total_investment):
    
    df2 = data.copy()
    
    # initialise a new column for monthly investment
    df2['Monthly Investment'] = 0

    # set to invest every 20 days
    for i in range(len(df2)):
        if i == 0 or i % 20 == 0:
            df2.iloc[i,-1] = deposit
    
    # sum all monthly investments at the end of the period
    print(f"Total amount invested over the period:\t\t\t${round(df2['Monthly Investment'].sum(),2)}")

    dca_cumul = cumul_ret(df2,df2['Returns'],deposit,contribute=True)
    
    df2['Investment Value'] = dca_cumul
    dca_capital = round(df2['Investment Value'][-1],2)
    print(f"Investment value at the end period (DCA strategy):\t${dca_capital}")

    dca_gain = round(((df2['Investment Value'][-1] - total_investment) / total_investment * 100),2)
    print(f"DCA strategy return at the end of period:\t\t{dca_gain}%")

    return dca_capital,dca_gain,dca_cumul

def dca_ta(data,deposit,total_investment):

    df3 = data.copy()

    # initialise a new column for monthly investment
    df3['Monthly Investment'] = 0

    # set to invest every 20 days
    for i in range(len(df3)):
        if i == 0 or i % 20 == 0:
            df3.iloc[i,-1] = deposit

    # sum all monthly investments at the end of the period
    print(f"Total amount invested over the period:\t\t${round(df3['Monthly Investment'].sum(),2)}")

    # define the entry & exit signals
    df3['SMA1'] = df3['Close'].rolling(100).mean()
    df3['SMA2'] = df3['Close'].rolling(200).mean()

    entry_signal = (df3['SMA1'] > df3['SMA2']) & (df3['Close'] > df3['SMA1'])
    exit_signal = df3['Close'] < df3['SMA1']

    # first, initiate the position tracker
    df3['position_tracker'] = ''
    
    # set position tracker as 1 at entry & set back to 0 upon selling
    df3['position_tracker'] = np.where(exit_signal,0,np.nan)
    df3['position_tracker'] = np.where(entry_signal,1,df3['position_tracker'])
    df3['position_tracker'].ffill(inplace=True)
    df3['position_tracker'].fillna(0,inplace=True)
    
    # shift the position tracker to reflect a more realistic trading situation
    # i.e. buy & sell the next day after the signal appears (beacuse signals are based on close price)
    df3['position_tracker'] = df3['position_tracker'].shift()
    df3['position_tracker'].fillna(0,inplace=True)
    
    # calculate the percent price change when we're in position
    df3['pct_change_long'] = df3['position_tracker'] * df3['Returns']
    df3['pct_change_long'].fillna(0,inplace=True)

    # change the pct_change to reflect price change from that day's open to that day's close,
    # assuming we buy at the Open & also, spread is applied when we buy
    for i in range(len(df3)):
        if (df3['position_tracker'][i-1] == 0) and (df3['position_tracker'][i] == 1):
            df3.iloc[i,-1] = (df3['Close'][i]/df3['Open'][i]) - 1 - 0.005
    
    ta_cumul = (1 + df3['pct_change_long']).cumprod() * total_investment
    dca_ta_cumul = cumul_ret(df3,df3['pct_change_long'],deposit,contribute=True)

    df3['Investment Value - TA'] = ta_cumul
    df3['Investment Value - DCA + TA'] = dca_ta_cumul

    ta_capital = round(df3['Investment Value - TA'][-1],2)
    print(f"Investment value at the end period (TA):\t${ta_capital}")

    ta_gain = round(((df3['Investment Value - TA'][-1] - total_investment) / total_investment * 100),2)
    print(f"TA strategy gain at the end of period:\t\t{ta_gain}%")

    dca_ta_capital = round(df3['Investment Value - DCA + TA'][-1],2)
    print(f"\nInvestment value at the end period (DCA + TA):\t${dca_ta_capital}")

    dca_ta_gain = round(((df3['Investment Value - DCA + TA'][-1] - total_investment) / total_investment * 100),2)
    print(f"DCA + TA strategy gain at the end of period:\t{dca_ta_gain}%")
    
    return df3,ta_capital,ta_gain,ta_cumul,dca_ta_capital,dca_ta_gain,dca_ta_cumul