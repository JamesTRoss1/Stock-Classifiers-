# Python script to test a trading strategy using the backtesting library 
from backtesting import Backtest, Strategy
import yfinance as yf 
import pandas as pd
from backtesting.lib import TrailingStrategy, SignalStrategy, crossover
from backtesting.test import SMA
import numpy as np
import os

def vwap(df):
    q = df["Volume"]
    p = df["Close"]
    VWAP = pd.Series((p * q).cumsum() / q.cumsum())
    return VWAP

class SmaCross1(SignalStrategy,
               TrailingStrategy):
    n1 = 5
    n2 = 10 
    def init(self):
        # In init() and in next() it is important to call the
        # super method to properly initialize the parent classes
        super().init()
        
        # Precompute the two moving averages
        sma1 = self.I(SMA, self.data.Close, self.n1)
        sma2 = self.I(SMA, self.data.Close, self.n2)
        # Where sma1 crosses sma2 upwards. Diff gives us [-1,0, *1*]
        signal = ((pd.Series(sma1) > sma2)).astype(int).diff().fillna(0)
        signal = signal.replace(-1, 0)  # Upwards/long only
        
        # Use 95% of available liquidity (at the time) on each order.
        # (Leaving a value of 1. would instead buy a single share.)
        entry_size = signal * .95
                
        # Set order entry sizes using the method provided by 
        # `SignalStrategy`. See the docs.
        self.set_signal(entry_size=entry_size)
        
        # Set trailing stop-loss to 2x ATR using
        # the method provided by `TrailingStrategy`
        self.set_trailing_sl(2)

class SmaCross(SignalStrategy,
               TrailingStrategy):
    n1 = 5
    n2 = 10 
    def init(self):
        # In init() and in next() it is important to call the
        # super method to properly initialize the parent classes
        super().init()
        # Precompute the two moving averages
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
        #self.VWAP = self.I(vwap, self.data)
        self.set_trailing_sl(5)
    def next(self): 
        #if crossover(self.sma1, self.sma2) or crossover(self.VWAP, self.data.Close):
        if crossover(self.sma1, self.sma2):
            self.position.close()
            self.buy()
        #elif crossover(self.sma2, self.sma1) or crossover(self.data.Close, self.VWAP):
        elif crossover(self.sma2, self.sma1):
            self.position.close()
            self.sell()
ticker = str(input("Ticker: "))
tick = yf.Ticker(str(ticker))
short1 = tick.history(period="1d", interval="1m", prepost=True)
short2 = tick.history(period="5d", interval="15m", prepost=True)
medium1 = tick.history(period="30d", interval="1h", prepost=True)
long1 = tick.history(period="365d", interval="1d", prepost=True)
durations = [short1, short2, medium1, long1]
Periods = {}
Periods1 = {}
for dur in durations:
    try:
        dur = dur.dropna()
        tester = Backtest(data=dur, strategy=SmaCross1, commission=.002)
        run = tester.optimize(n1=[2, 3, 5, 7, 10, 12, 13, 14, 15], n2=[15, 20, 25, 30, 35, 40, 45, 50, 55],
                    constraint=lambda p: p.n1 < p.n2)
        if(run.get("Return [%]") > run.get("Buy & Hold Return [%]")):
            Periods.update({str(run.get("Duration")) : run.get("Return [%]")})
        else: 
            Periods1.update({str(run.get("Duration")) : run.get("Buy & Hold Return [%]")})
    except Exception:
        continue

    
if len(Periods) > 0: 
    dic2=dict(sorted(Periods.items(),key= lambda x:x[1]))
    print()
    print("Results: Use Strategy")
    print("Chosen Duration: ", list(dic2.keys())[-1])
    print("Projected Return: ", list(dic2.values())[-1])
    print()
if len(Periods1) > 0:
    dic2=dict(sorted(Periods1.items(),key= lambda x:x[1]))
    print()
    print("Results: Use Buy And Hold Strategy")
    print("Chosen Duration: ", list(dic2.keys())[-1])
    print("Projected Return: ", list(dic2.values())[-1])
    print()
