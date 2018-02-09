import os
import time

import csv
import pandas as pd
import numpy as np

import crypto

# Return dictionary with pairs as index (ie ETH-BTC) and value.
# Pairs are in global format.
def get_market_prices(client) :
	market_prices = {}
	# market_prices['time'] = crypto.utils.dateparse(crypto.utils.current_milli_time())
	# print(market_prices['time'])

	if type(client) is crypto.binanceClient :
		prices = client.get_all_tickers()
		for price in prices :
			if price['symbol'] == '123456' : continue
			p,u = crypto.utils.chop(price['symbol'])
			market_prices[p+'-'+u] = float(price['price'])
			# print('[{0}] {1}'.format(price['symbol'],price['price']))

	elif type(client) is crypto.kucoinClient :
		prices = client.get_tick()
		for price in prices :
			# print(price)
			if 'lastDealPrice' in price :
				market_prices[price['coinType']+'-'+price['coinTypePair']] = float(price['lastDealPrice'])

	elif type(client) is crypto.poloClient :
		prices = client.returnTicker()
		for price in prices :
			p = price.split('_')
			# print(p)
			market_prices[p[1]+'-'+p[0]] = float(prices[price]['last'])

	elif type(client) is crypto.gdaxClient :
		# to implement
		client = crypto.gdaxPClient()
		prices = client.get_products()
		for price in prices :
			pair = price['id']
			market_prices[pair] = float(client.get_product_ticker(pair)['price'])

	market_prices['ETH-ETH'] = 1
	market_prices['BTC-BTC'] = 1
	if 'ETH-BTC' in market_prices :
		market_prices['BTC-ETH'] = 1 / market_prices['ETH-BTC']
	elif 'BTC-ETH' in market_prices :
		market_prices['ETH-BTC'] = 1 / market_prices['BTC-ETH']

	if 'ETH-USD' in market_prices :
		market_prices['USD-ETH'] = 1 / market_prices['ETH-USD']
	if 'BTC-USD' in market_prices :
		market_prices['USD-BTC'] = 1 / market_prices['BTC-USD']
	if 'BTC-EUR' in market_prices :
		market_prices['EUR-BTC'] = 1 / market_prices['BTC-EUR']
	# if 'ETH-USD' in market_prices :
	# 	market_prices['ETH-USD'] = market_prices['ETH-USD']

	return market_prices

def load_market_history() :
	file = 'market_'+time.strftime("%Y%m%d")+".csv"
	return pd.read_csv(file, parse_dates=True, date_parser=dateparse, index_col=[0])

def update_market_file(dir,market) :
	file = dir+'/market_'+time.strftime("%Y%m%d")+".csv"

	file_exists = os.path.exists(file)

	with open(file,'a') as f:
		w = csv.DictWriter(f, market.keys())
		if not file_exists :
			w.writeheader()
		w.writerow(market)

def get_all_market_prices(clients) :
	df = None
	list_clients = []
	for client in clients :
		name = crypto.utils.get_client_name(client)
		list_clients.append(crypto.utils.get_client_name(client))
		market_prices = crypto.market.get_market_prices(client)
		t = pd.DataFrame(list(market_prices.items()), columns=['pair', name])
		t[name] = t[name].apply(pd.to_numeric)

		if df is None :
			df = t
		else :
			df = pd.merge(df, t, on='pair', how='outer')
	# print(df.head(10))

	# Find maximum deltas between two platforms
	df['delta'] = ((df.max(axis=1) - df.min(axis=1)) / df.min(axis=1)) * 100
	df['deltaP'] = pd.Series(["{0:.0f}%".format(val) for val in df['delta']], index = df.index)

	df['From'] = df[list_clients].idxmin(axis=1)
	df['To'] = df[list_clients].idxmax(axis=1)

	df.index =  df['pair']
	df = df.drop('pair', 1)

	return df
