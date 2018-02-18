import time
import calendar
import requests

import pandas as pd
import numpy as np

from datetime import datetime, date, timedelta

import crypto

# Get last klines
def get_last_klines(client, pair, interval) :

	if type(client) is crypto.binanceClient :
		if interval == 1 : interval = crypto.binanceClient.KLINE_INTERVAL_1MINUTE
		elif interval == 5 : interval = crypto.binanceClient.KLINE_INTERVAL_5MINUTE
		else : return None

		klines = client.get_klines(symbol=pair, interval=interval)

	return format_klines(client, pd.DataFrame(klines))

# Get Historical data (for training model use) :
# pair can be 'NEOBTC'
# when should be a date string DD/MM/YYYY
# Warning : We stay in UTC !!

def get_historical_klines(client, pair, dateMin, dateMax) :
	if type(client) is crypto.binanceClient :
		timestamp_min = int(time.mktime(dateMin.timetuple())) * 1000
		klines = client.get_klines(symbol=pair, interval=crypto.binanceClient.KLINE_INTERVAL_5MINUTE, startTime=timestamp_min)
	elif type(client) is crypto.kucoinClient :
		timestamp_min = int(time.mktime(dateMin.timetuple()))
		timestamp_max = int(time.mktime(dateMax.timetuple()))
		klines = client.get_kline_data_tv(pair, crypto.kucoinClient.RESOLUTION_5MINUTES, timestamp_min, timestamp_max)
	elif type(client) is crypto.poloClient :
		timestamp_min = int(time.mktime(dateMin.timetuple()))
		timestamp_max = int(time.mktime(dateMax.timetuple()))
		klines = client.returnChartData(pair, 300, start=timestamp_min, end=timestamp_max)
	elif type(client) is crypto.gdaxClient or type(client) is crypto.gdaxPClient :
		# 350 points max per request : (288/day for 5min step)
		timestamp_min = dateMin.isoformat()
		timestamp_max = (dateMin + timedelta(minutes=1750)).isoformat()
		klines = client.get_product_historic_rates(pair, start=timestamp_min, end=timestamp_max, granularity=300)
	# elif type(client) is crypto.krakenClient :
		# timestamp_min = int(time.mktime(dateMin.timetuple()))
		# data = {'pair': pair,
		# 	'interval': 5,
		# 	'since': 0
		# 	}
		# # klines = requests.get('https://api.kraken.com/0/public/OHLC?pair=BCHEUR&interval=5&since=0').json()
		# klines = client.query_public('OHLC', data=data)
		# last = klines['result']['last']
		# klines = klines['result'][pair]
	return format_klines(client, pd.DataFrame(klines))

# Reformat klines to get ['time','Open', 'High','Low','Close','Volume']
# Return time is in UTC time
def format_klines(client,df) :
	if df.empty : return df

	if type(client) is crypto.binanceClient :
		df.columns = ['Open time','Open', 'High','Low','Close','Volume','Close time','Quote asse volume','Number of trades','Taker base','Taker quote','Ignore']

		# Remove unused columns
		df = df.drop('Close time', 1)
		df = df.drop('Quote asse volume', 1)
		df = df.drop('Number of trades', 1)
		df = df.drop('Taker base', 1)
		df = df.drop('Taker quote', 1)
		df = df.drop('Ignore', 1)

		# Convert unix timestamp (ms) to UTC date
		df['time'] = pd.to_datetime(df['Open time'], unit='ms')
		df = df.drop('Open time', 1)

	elif type(client) is crypto.kucoinClient :
		df.columns = ['Close','High','Low','Open','Status','Open time','Volume']
		df = df.drop('Status', 1)

		# Reorder
		cols = ['Open time','Open', 'High','Low','Close','Volume']
		df = df[cols]

		# Convert unix timestamp (s) to UTC date
		df['time'] = pd.to_datetime(df['Open time'], unit='s')
		df = df.drop('Open time', 1)

	elif type(client) is crypto.poloClient :
		df.columns = ['Close','Open time','High','Low','Open','quoteVolume','Volume','weightedAverage']
		df = df.drop('quoteVolume', 1)
		df = df.drop('weightedAverage', 1)

		# Reorder
		cols = ['Open time','Open','High','Low','Close','Volume']
		df = df[cols]

		# Convert unix timestamp (s) to UTC date
		df['time'] = pd.to_datetime(df['Open time'], unit='s')
		df = df.drop('Open time', 1)

	elif type(client) is crypto.gdaxClient or type(client) is crypto.gdaxPClient :
		df.columns = ['Open time','Low','High','Open','Close','Volume']
		# Reorder
		cols = ['Open time','Open','High','Low','Close','Volume']
		df = df[cols]

		# Convert unix timestamp (s) to UTC date
		df['time'] = pd.to_datetime(df['Open time'], unit='s')
		# for i in df.index:
		# 	df.loc[i,'time']=pd.to_datetime(df.loc[i, 'Open time'], unit='s')
		df = df.drop('Open time', 1)

	elif type(client) is crypto.krakenClient :
		df.columns = ['Open time','Open','High','Low','Close','vwap','Volume','count']
		df = df.drop('vwap', 1)
		df = df.drop('count', 1)

		# Convert unix timestamp (s) to UTC date
		df['time'] = pd.to_datetime(df['Open time'], unit='s')
		df = df.drop('Open time', 1)

	# print(df.head(10))

	# Remove lines without transfer
	df['Volume'] = df['Volume'].apply(pd.to_numeric)
	df = df[(df['Volume'] > 0 )]

	# Sort with last in first and put as index
	df.sort_values(by='time', inplace=True, ascending=True)
	df.index =  df['time']
	df = df.drop('time', 1)

	df['Open'] = df['Open'].apply(pd.to_numeric)
	df['High'] = df['High'].apply(pd.to_numeric)
	df['Low'] = df['Low'].apply(pd.to_numeric)
	df['Close'] = df['Close'].apply(pd.to_numeric)

	return df

def show_klines(df) :
	df = format_klines(df)

	df['time'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert('Europe/Paris').apply(lambda x: x.strftime('%d/%m/%Y %H:%M'))
	# Compute change
	df['Open'] = df['Open'].apply(pd.to_numeric)
	df['Close'] = df['Close'].apply(pd.to_numeric)
	df['change'] = crypto.utils.percent_change(df['Open'],df['Close'])

	return df
