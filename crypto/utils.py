import os
import time, datetime

import pandas as pd
import numpy as np

# for fees pages
import requests
from bs4 import BeautifulSoup # parse page

import xml.etree.ElementTree as ET

import crypto

# Get all available clients
def get_clients(file) :
	clients = []
	tree = ET.parse(file)
	settings = tree.getroot()

	for service in settings.findall('service') :
		name = service.get("name")
		client = get_client(name=name, file=file)

		try :
			if verify_time(client) :
				clients.append(client)
				print('Connected to {0}'.format(get_client_name(client)))
			else :
				print('Client {} not available'.format(name))

		except :
			print('Client {} not available (exception)'.format(name))

	return clients

# Get one client
# Params : name, file
def get_client(**kwargs) :

	# Service is mandatory
	if kwargs.get('name') :
		service_name = kwargs.get('name')
	else :
		return None

	# Find directly in file
	if kwargs.get('file') :
		tree = ET.parse(kwargs.get('file'))
		settings = tree.getroot()

		try :
			for service in settings.findall('service') :
				s_name = service.get("name")
				if s_name == service_name == "binance" :
					api_key = service.find("api_key")
					api_secret = service.find("api_secret")
					return crypto.binanceClient(api_key.text, api_secret.text)
				elif s_name == service_name == "kucoin" :
					api_key = service.find("api_key")
					api_secret = service.find("api_secret")
					return crypto.kucoinClient(api_key.text, api_secret.text)
				elif s_name == service_name == "poloniex" :
					api_key = service.find("api_key")
					api_secret = service.find("api_secret")
					return crypto.poloClient(api_key.text, api_secret.text)
				elif s_name == service_name == "gdax" :
					api_key = service.find("api_key")
					api_secret = service.find("api_secret")
					api_passphrase = service.find("api_passphrase")
					if api_key and api_secret and api_passphrase :
						return crypto.gdaxClient(api_key.text, api_secret.text, api_passphrase.text)
					else :
						return crypto.gdaxPClient()
				elif s_name == service_name == "bitfinex" :
					# Not enough money to test private API
					return crypto.bitfinexClient()
				elif s_name == service_name == "kraken" :
					api_key = service.find("api_key")
					api_secret = service.find("api_secret")
					return crypto.krakenClient(api_key.text, api_secret.text)
				elif s_name == service_name == "etherscan" :
					api_key = service.find("api_key")
					eth_addresses = []
					for ad in service.findall('address') :
						eth_addresses.append(ad.text)
					# print(eth_addresses)
					return crypto.etherClient(address=eth_addresses, api_key=api_key.text)
		except :
			print('Client {} not available (exception)'.format(name))
			return None

	return None

def get_out_dir(file) :
	tree = ET.parse(file)
	settings = tree.getroot()

	out_dir = settings.find('output').text
	# Create paths
	if not os.path.exists(out_dir): os.makedirs(out_dir)
	rep = ['market','history','history/binance','history/kucoin','history/poloniex','history/gdax','fees']
	for r in rep :
		if not os.path.exists(out_dir+'/'+r): os.makedirs(out_dir+'/'+r)

	return out_dir

def get_fees_url(file, client) :
	tree = ET.parse(file)
	settings = tree.getroot()

	for service in settings.findall('service') :
		name = get_client_name(client)
		if service.get("name") == name :
			if service.find('fees') is not None :
				return service.find('fees').text
	return None

# Get fees for different platforms
def get_fees(file, client) :
	df = pd.DataFrame(columns=['coin', 'minimum', 'fee'])

	fees_url = get_fees_url(file, client)
	if fees_url is not None :
		if type(client) is crypto.binanceClient :
			r = requests.get(fees_url)
			for asset in r.json() :
				asset_code = asset['assetCode']
				asset_name = asset['assetName']
				asset_minimum = float(asset['minProductWithdraw'])
				asset_fee = float(asset['transactionFee'])
				df.loc[len(df.index)] = [asset_code,asset_minimum,asset_fee]
			return df
		elif type(client) is crypto.kucoinClient :
			web_page = requests.get(fees_url)
			soup = BeautifulSoup(web_page.content, "html.parser")
			table = soup.find('table')
			for row in table.find_all('tr'):
				columns = row.find_all('td')
				if len(columns) == 0 : continue
				asset_code = columns[0].get_text().strip()
				if asset_code == 'Assets' :
					continue
				asset_minimum = 0
				asset_fee = columns[1].get_text().strip()
				if asset_fee == 'Free' :
					asset_fee = 0
				else :
					asset_fee = float(asset_fee)
				df.loc[len(df.index)] = [asset_code,asset_minimum,asset_fee]

			return df

	return pd.DataFrame()

# Save fees
def save_fees(dir,name,df) :
	file = dir+'/fees/'+name+".pickle"
	df.to_pickle(file)
	# Load with df = pd.read_pickle(file)

def get_client_name(client) :
	if type(client) is crypto.binanceClient :
		return 'binance'
	elif type(client) is crypto.kucoinClient :
		return 'kucoin'
	elif type(client) is crypto.poloClient :
		return 'poloniex'
	elif type(client) is crypto.gdaxClient or type(client) is crypto.gdaxPClient :
		return 'gdax'
	elif type(client) is crypto.krakenClient :
		return 'kraken'
	elif type(client) is crypto.etherClient :
		return 'etherscan'
	else :
		return None

# Get list of pairs we can trade in universal XXX-YYY format with equivalents in
# binance  : ETHBTC
# kucoin   : ETH-BTC
# poloniex : BTC_ETH

def get_all_pairs(client) :
	list_pairs = {}
	if type(client) is crypto.binanceClient :
		pairs = client.get_all_tickers()
		for pair in pairs :
			if pair['symbol'] == '123456' : continue
			p, u = chop(pair['symbol'])
			list_pairs[p+'-'+u] = pair['symbol']

	elif type(client) is crypto.kucoinClient :
		pairs = client.get_tick()
		for pair in pairs :
			list_pairs[pair['coinType']+'-'+pair['coinTypePair']] = pair['coinType']+'-'+pair['coinTypePair']

	elif type(client) is crypto.poloClient :
		pairs = client.returnTicker()
		for pair in pairs.keys() :
			p = pair.split('_')
			list_pairs[p[1]+'_'+p[0]] = pair

	elif type(client) is crypto.gdaxClient or type(client) is crypto.gdaxPClient:
		pairs = client.get_products()
		for pair in pairs :
			list_pairs[pair['base_currency']+'-'+pair['quote_currency']] = pair['id']

	elif type(client) is crypto.bitfinexClient :
		pairs = client.symbols()
		for pair in pairs :
			p,u = chop(pair)
			list_pairs[p+'-'+u] = pair

	elif type(client) is crypto.krakenClient :
		pairs = client.query_public('AssetPairs')['result']
		for pair in pairs :
			p = pairs[pair]
			list_pairs[p['base']+'-'+p['quote']] = pair

	return list_pairs

def get_ethereum_balances(file) :
	balances = {}
	tree = ET.parse(file)
	settings = tree.getroot()

	for service in settings.findall('service') :
		if service.get("name") == "etherscan" :
			api_key = service.find("api_key").text
			for wallet in service.findall('addresses') :
				print(wallet)
				# ad = account.get('add').text
				# print(ad)

# Time
current_milli_time = lambda: int(round(time.time() * 1000))

def dateparse(time_in_secs):
	return datetime.datetime.fromtimestamp(int(time_in_secs)/1000).strftime('%d/%m/%Y %H:%M:%S')

def convert_to_paris_time(client,row):
	return pd.to_datetime(row.datetime_local).tz_convert('Europe/Paris')

def verify_time(client) :
	if not client :
		return False

	timestamp = None
	if type(client) is crypto.binanceClient :
		timestamp = client.get_server_time()['serverTime']
		time_ser = int(int(timestamp)/1000)
	elif type(client) is crypto.kucoinClient :
		currencies = client.get_currencies()
		timestamp = client.get_last_timestamp()
		time_ser = int(int(timestamp)/1000)
	elif type(client) is crypto.poloClient : # no timestamp
		tickers = client.returnTicker()
		if tickers is not None and len(tickers) > 0 :
			return True
	elif type(client) is crypto.gdaxClient or type(client) is crypto.gdaxPClient :
		timestamp = client.get_time()['epoch']
		time_ser = int(timestamp)
	elif type(client) is crypto.krakenClient :
		timestamp = client.query_public('Time')['result']['unixtime']
		time_ser = int(timestamp)

	elif type(client) is crypto.etherClient :
		return True

	if not timestamp :
		return False

	time_loc = int(time.time())
	dtime_ser = datetime.datetime.fromtimestamp(time_ser).strftime('%Y-%m-%d %H:%M:%S')
	dtime_loc = datetime.datetime.fromtimestamp(time_loc).strftime('%Y-%m-%d %H:%M:%S')
	# print('Server time is {0}ms {1}'.format(time_ser, dtime_ser))
	# print(' Local time is {0}ms {1}'.format(time_loc, dtime_loc))
	# print(' Delta with {0} server is {1}'.format(get_client_name(client),time_loc-time_ser))
	if time_loc - time_ser < 1000 :
		return True

# Misc

def percent_change(old_price, new_price) :
	return (((new_price - old_price) / old_price) * 100)

# Chop XXXYYY to XXX and YYY
def chop(thestring):
	thestring = thestring.upper()
	if thestring.endswith('ETH') :
		return thestring[:-len('ETH')], 'ETH'
	elif thestring.endswith('BTC') :
		return thestring[:-len('BTC')] , 'BTC'
	elif thestring.endswith('BNB') :
		return thestring[:-len('BNB')] , 'BNB'
	elif thestring.endswith('USDT') :
		return thestring[:-len('USDT')] , 'USD'
	elif thestring.endswith('USD') :
		return thestring[:-len('USD')] , 'USD'
	else :
		return thestring , ''

def lchop(x) :
	y,z = chop(x)
	return y

def rchop(x) :
	y,z = chop(x)
	return z
