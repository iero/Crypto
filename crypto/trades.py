import pandas as pd
import numpy as np

import crypto

def get_active_trades(client,market_prices) :
	if type(client) is crypto.binanceClient :
		trades = client.get_open_orders()
		pairs = crypto.utils.get_all_pairs(client)
	elif type(client) is crypto.kucoinClient :
		# not yet implemented
		trades = []
	elif type(client) is crypto.poloClient :
		# not yet implemented
		trades = []
	elif type(client) is crypto.gdaxClient :
		# not yet implemented
		trades = []
	else :
		trades = []


	if len(trades) == 0 :
		return pd.DataFrame()

	df = pd.DataFrame(trades)
	df = df.drop('clientOrderId', 1)
	df = df.drop('executedQty', 1)
	df = df.drop('icebergQty', 1)
	df = df.drop('isWorking', 1)
	df = df.drop('orderId', 1)
	df = df.drop('status', 1)
	df = df.drop('timeInForce', 1)
	df.index =  df['symbol']
	df = df.drop('symbol', 1)

	df.rename(columns={'origQty':'quantity'}, inplace=True)
	df.rename(columns={'price':'target'}, inplace=True)

	df['quantity'] = df['quantity'].apply(pd.to_numeric)
	df['target'] = df['target'].apply(pd.to_numeric)
	df['stopPrice'] = df['stopPrice'].apply(pd.to_numeric)

	df['time'] = pd.to_datetime(df['time'], unit='ms')

	actual_price = []
	for s in df.index.values :
		for x, y in pairs.items():
			if y == s:
				actual_price.append(market_prices[x])
	df['price'] = actual_price
	df['distance'] = df['target'] - df['price']
	return df

def add_active_trades_to_portfolio(portfolio, trades) :

	if trades.empty :
		return portfolio

	trades['clean'] = trades.index.map(lambda x: crypto.utils.lchop(x))
	trades['unit'] = trades.index.map(lambda x: crypto.utils.rchop(x))

	# If we buy, we still have needed btc/eth/usdt
	# If we sell, we still have the alt
	trades['portfolio'] = np.where(trades['side']=='BUY', trades['unit'], trades['clean'])
	trades['amount'] = np.where(trades['side']=='BUY', trades['quantity']*trades['target'], trades['quantity'])

	df = trades[['portfolio','amount']]
	df.index = trades['portfolio']
	df = df.drop('portfolio', 1)

	df.rename(columns={'amount':'quantity'}, inplace=True)
	df['quantity'] = df['quantity'].apply(pd.to_numeric)
	portfolio['quantity'] = portfolio['quantity'].apply(pd.to_numeric)

	res = pd.concat([portfolio, df])
	res = res.groupby(res.index).sum()

	return res

def get_trades(client,s,source) :
	try :
		mytrades = client.get_my_trades(symbol=s+source)
		t = pd.DataFrame(mytrades)
		t['source'] = source
		t['symbol'] = s
		t.index = t['symbol']
		return t
	except :
		return pd.DataFrame()

def get_all_trades(client,symbol) :
	res = pd.DataFrame()
	for source in ['ETH','BTC','USD'] :
		t = get_trades(client,symbol,source)
		if not t.empty :
			res = pd.concat([res,t])

	return res

def show_trades(trades) :

	if trades.empty :
		# print('\n---------- No Actives Trades ----')
		return

	print('---- [Active Trades] ----')
	trades['quantity'] = trades['quantity'].map(lambda x: '%2.3f' % x)
	# portfolio.loc['Total'] = portfolio.sum()

	# add percent to complete
	trades['%'] = (trades['target'] -  trades['price']) / trades['price']
	trades['%'] = pd.Series(["{0:.0f}%".format(val * 100) for val in trades['%']], index = trades.index)

	# remove stopPrice if not set
	if not 0 in trades['stopPrice'].values :
		print(trades[['quantity','target','price','stopPrice','%','side','type']])
		# print(trades[['quantity','target','price','distance','stopPrice','type','side']])
	else :
		# print(trades[['quantity','target','price','distance','type','side']])
		print(trades[['quantity','target','price','%','side','type']])

	# Remove column with only null values
	# trades.loc[:, (trades != 0).any(axis=0)]
	print('\n')

