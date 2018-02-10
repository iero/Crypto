import pandas as pd
import numpy as np

import crypto

def get_portfolio(client) :
	if type(client) is crypto.binanceClient :
		info = client.get_account()
		df = pd.DataFrame(info['balances'])
		df['free'] = df['free'].apply(pd.to_numeric)
		df = df.drop('locked', 1)
		df.columns = ['symbol', 'quantity']
	elif type(client) is crypto.kucoinClient :
		# no info here
		info = client.get_all_balances()
		df = pd.DataFrame(info)
		df = df.drop(['freezeBalance','balanceStr', 'freezeBalanceStr'],1)
		df.columns = ['quantity', 'symbol']
	elif type(client) is crypto.gdaxClient :
		info = client.get_accounts()
		df = pd.DataFrame(info)
		df = df.drop(['id','available', 'hold', 'profile_id'],1)
		df.columns = ['quantity', 'symbol']
	elif type(client) is crypto.etherClient :
		df = pd.DataFrame(columns=['symbol','quantity','eth'])
		balance = client.get_balance_multiple()
		line = 0
		for account in balance :
			# balance is in Wei (10^-18) units
			val = int(account['balance']) * 10**-18
			df.loc[line] = [account['account'],val,val]
			line += 1
	else :
		return pd.DataFrame()

	df.index =  df['symbol']
	df = df.drop('symbol', 1)

	return df[(df['quantity'] > 0)]

def add_market_prices_to_portfolio(portfolio, market_prices) :
	if portfolio.empty or len(market_prices) <= 2:
		return portfolio

	portfolio_eth = []
	portfolio_btc = []

	portfolio['quantity'] = portfolio['quantity'].apply(pd.to_numeric)

	for s in portfolio.index.values :
		if s == 'USDT' :
			s = 'USD'

		if s+'-ETH' in market_prices :
			portfolio_eth.append(market_prices[s+'-ETH'])
		else :
			portfolio_eth.append(market_prices[s+'-BTC']/market_prices['ETH-BTC'])
		if s+'-BTC' in market_prices :
			portfolio_btc.append(market_prices[s+'-BTC'])

	portfolio['eth'] = portfolio['quantity'] * portfolio_eth
	portfolio['btc'] = portfolio['quantity'] * portfolio_btc
	portfolio['usd'] = portfolio['eth'] * market_prices['ETH-USD']

	return portfolio

def add_original_buy_transactions(client,portfolio,market) :
	no_symbols = ['Total','USD','BTC','ETH','BNB']

	# For each symbol in portflio, try to get origin
	symbols = portfolio.index.values

	res = pd.DataFrame()

	for s in symbols :
		if s in no_symbols : continue

		# print("Looking for [{}] buy orders".format(s))
		t = crypto.trades.get_all_trades(client,s)
		res = pd.concat([res,t])

	res = res.drop('id', 1)
	res = res.drop('orderId', 1)
	res = res.drop('symbol', 1)

	res['time'] = pd.to_datetime(res['time'], unit='ms')

	res =  res[(res['isBuyer'] == True )]
	res = res.drop('isBuyer', 1)
	res = res.drop('isBestMatch', 1)

	res.rename(columns={'qty':'quantity'}, inplace=True)
	res.rename(columns={'commissionAsset':'comAsset'}, inplace=True)
	res.rename(columns={'commission':'com'}, inplace=True)

	res['quantity'] = res['quantity'].apply(pd.to_numeric)
	res['price'] = res['price'].apply(pd.to_numeric)
	res['com'] = res['com'].apply(pd.to_numeric)

	# print(res)
	# print(res[['source','quantity','price','com','comAsset','time']])

	# We drop 'com','comAsset' but we can use them later
	# We have all transactions, sorted by most recent first
	res = res[['source','quantity','price','time']]
	res.sort_values(by='time', inplace=True, ascending=False)
	#t['time'] = t.to_datetime(t['time'])
	# print(res)

	change_percent = []
	for s in symbols :
		if s in no_symbols :
			change_percent.append(0)
			continue;

		pf = portfolio.loc[portfolio.index == s]
		bag = float(pf.iloc[0]['quantity'])
		# print('Looking for {0} units of {1}'.format(bag,s))

		value = 0
		b_symbol = '-'

		quantity = bag
		r = res.loc[res.index == s]
		# print(r)
		for index, row in r.iterrows():
			# need to keep consistency in source
			if b_symbol != '-' and b_symbol != row['source'] : continue
			b_qty = float(row['quantity'])
			b_price = float(row['price'])
			b_symbol = row['source']
			if quantity > 0 :
				value += b_price * min(b_qty,quantity)
				# print('bought {0} at {1}'.format(min(b_qty,quantity),b_price))
				quantity = quantity - b_qty
		value = value / float(pf.iloc[0]['quantity'])

		if value == 0 :
			change_percent.append(0)
		else :
			actual_price = market[s+b_symbol]
			print('Bought {0} units of {1} at {2} {3} per unit (actual price {4}) '.format(bag, s, value, b_symbol, actual_price))
			change_percent.append("{0:.0f}%".format(crypto.utils.percent_change(value,actual_price)))

	portfolio['change'] = change_percent
	print(portfolio)

def get_balance(client) :
	out = {}
	if type(client) is crypto.etherClient :
		balance = client.get_balance_multiple()
		for account in balance :
			# balance is in Wei (10^-18) units
			val = int(account['balance']) * 10**-18
			out[account['account']] = val

	return out

def show_portfolio(portfolio,dust) :
	if portfolio.empty :
		# print('\n----- empty Portfolio ----')
		return

	print('---- [Portfolio] ----')
	portfolio['%'] = portfolio['eth']/ portfolio['eth'].sum()
	portfolio.loc['Total'] = portfolio.sum()

	portfolio['quantity'] = portfolio['quantity'].map(lambda x: '%2.2f' % x)
	portfolio['eth'] = portfolio['eth'].map(lambda x: '%2.5f' % x)
	if 'btc' in portfolio :
		portfolio['btc'] = portfolio['btc'].map(lambda x: '%2.5f' % x)
	if 'usd' in portfolio :
		portfolio['usd'] = portfolio['usd'].map(lambda x: '%2.2f' % x)
		portfolio['usd'] = portfolio['usd'].apply(pd.to_numeric)

	portfolio['%'] = pd.Series(["{0:.0f}%".format(val * 100) for val in portfolio['%']], index = portfolio.index)

	if 'usd' in portfolio :
		print(portfolio[(portfolio['usd'] > dust)])
	else :
		print(portfolio)

	print('\n')
