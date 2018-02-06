import os
import time, datetime

import pandas as pd
import numpy as np

# for fees pages
import requests
from bs4 import BeautifulSoup # parse page

import xml.etree.ElementTree as ET

import crypto

def get_clients(file) :
	clients = []
	tree = ET.parse(file)
	settings = tree.getroot()

	for service in settings.findall('service') :
		client = None
		name = service.get("name")

		if service.get("name") == "binance" :
			api_key = service.find("api_key").text
			api_secret = service.find("api_secret").text
			client = crypto.binanceClient(api_key, api_secret)
		elif service.get("name") == "kucoin" :
			api_key = service.find("api_key").text
			api_secret = service.find("api_secret").text
			client = crypto.kucoinClient(api_key, api_secret)
		# elif service.get("name") == "poloniex" :
		# 	api_key = service.find("api_key").text
		# 	api_secret = service.find("api_secret").text
		# 	client = crypto.poloClient(api_key, api_secret)
		elif service.get("name") == "gdax" :
			api_key = service.find("api_key").text
			api_secret = service.find("api_secret").text
			api_passphrase = service.find("api_passphrase").text
			client = crypto.gdaxClient(api_key, api_secret, api_passphrase)
		# elif service.get("name") == "kraken" :
		# 	from pykrakenapi import KrakenAPI

		if verify_time(client) :
			clients.append(client)
			print('Connected to {0}'.format(get_client_name(client)))
		else :
			print('Client {} not available'.format(name))

	return clients


def get_out_dir(file) :
	tree = ET.parse(file)
	settings = tree.getroot()

	out_dir = settings.find('output').text
	# Create paths
	if not os.path.exists(out_dir): os.makedirs(out_dir)
	rep = ['market','history','history/binance','history/kucoin','history/poloniex','fees']
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
	elif type(client) is crypto.gdaxClient :
		return 'gdax'
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
			p = rchop(pair['symbol'])
			u = unit(pair['symbol'])
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

	elif type(client) is crypto.gdaxClient :
		pairs = client.returnTicker()

	# print(list_pairs)
	# return list_pairs.values()
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

	elif type(client) is crypto.kucoinClient :
		currencies = client.get_currencies()
		# if currencies['rates'] :
		# 	return True
		timestamp = client.get_last_timestamp()

	elif type(client) is crypto.poloClient :
		# no timestamp
		tickers = client.returnTicker()
		if tickers is not None and len(tickers) > 0 :
			return True

	elif type(client) is crypto.gdaxClient :
		timestamp_t = client.get_time()
		timestamp = int(timestamp_t['epoch'])
		return True # a adapter ? ex : 1517783784.87

	if not timestamp :
		return False

	time_ser = int(int(timestamp)/1000)
	time_loc = int(time.time())

	# print(time_ser)
	# print(time_loc)

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

def rchop(thestring):
	if thestring.endswith('ETH') :
		return thestring[:-len('ETH')]
	elif thestring.endswith('BTC') :
		return thestring[:-len('BTC')]
	elif thestring.endswith('BNB') :
		return thestring[:-len('BNB')]
	elif thestring.endswith('USDT') :
		return thestring[:-len('USDT')]
	else :
		return thestring

def unit(thestring):
	if thestring.endswith('ETH') :
		return 'ETH'
	elif thestring.endswith('BTC') :
		return 'BTC'
	elif thestring.endswith('BNB') :
		return 'BNB'
	elif thestring.endswith('USDT') :
		return 'USDT'
	else :
		return thestring
