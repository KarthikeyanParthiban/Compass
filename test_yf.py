import yfinance as yf
import pandas as pd

symbols = ['RELIANCE.NS', 'SBIN.NS']
df = yf.download(symbols, period='5d')
print("Columns structure:")
print(df.columns)
print("\nFirst few rows:")
print(df.head())
