import sys, os
import time
import argparse

import pandas as pd
import numpy as np

import crypto

def get_transactions_scenarios(market_prices,clients_fees,clients_dict,cols_list) :
# Get possible transactions with more than x% gain
	mininmum_gain = 5

	# print(market_prices[(market_prices['delta'] > mininmum_gain)][cols_list])

	# Create transactions scenarios
	bag = {}
	bag['BTC'] = 0.05
	bag['ETH'] = 0.5
	bag['USDT'] = 100
	print('Transfers available')
	for index, row in market_prices[(market_prices['delta'] > mininmum_gain)].iterrows():
		# get paramaters
		from_exchange = row['From']
		to_exchange = row['To']
		coin = index.split('-')[0]
		base_coin = index.split('-')[1]
		delta = row['deltaP']
		price_from_exchange = row[from_exchange]
		price_to_exchange = row[to_exchange]

		# extract corresponding fees
		df_fees = clients_fees[client_name]
		df_fees = df_fees.loc[df_fees['coin'] == coin]
		fee = 0
		min_withdraw = 0
		if not df_fees.empty :
			fee  = df_fees['fee'].iloc[0]
			min_withdraw  = df_fees['minimum'].iloc[0]

		# get bag in alt_coin & verify it is more than withdraw
		bag[coin] = (bag[base_coin] / price_from_exchange) + fee
		new_bag = (bag[base_coin] / price_from_exchange) * price_to_exchange

		# get target address
		address = crypto.assets.get_deposit_address(clients_dict[to_exchange],coin)

		# Output
		if address :
			print('Change Bag of {0:04.2f} {1} to {2:06.5f} {3} (fee : {4}) and get {5:05.3f} {1}'.format(bag[base_coin],base_coin,bag[coin],coin,fee,new_bag))
			print('{4:>3} {0:>4} from {1} to {2} \taddress {3}'.format(coin,from_exchange,to_exchange,address,delta))
			if min_withdraw > 0 and bag[coin] > min_withdraw :
				print('Amount too small ({0})'.min_withdraw)
		else :
			# remove entry from table
			market_prices = market_prices.drop(index)

	print(market_prices[(market_prices['delta'] > mininmum_gain)][cols_list])
	return market_prices[(market_prices['delta'] > mininmum_gain)][cols_list]

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--params", type=str, help="file.xml", required=True)
	parser.add_argument("--loop", type=int, help="Loop time in sec (0 one shot)", required= False, default=0)
	option = parser.parse_args()

	clients = crypto.utils.get_clients(option.params)
	out_dir = crypto.utils.get_out_dir(option.params)

	# Get fees for each service
	clients_fees = {}
	clients_dict = {}
	cols_list = ['From','To','deltaP']
	for client in clients :
		client_name = crypto.utils.get_client_name(client)
		clients_dict[client_name] = client
		cols_list.append(client_name)

		clients_fees[client_name] = crypto.utils.get_fees(option.params,client)
		if not clients_fees[client_name].empty and len(clients_fees[client_name]) > 0 :
			crypto.utils.save_fees(out_dir,client_name,clients_fees[client_name])
		print('Got {0} fees for {1}'.format(len(clients_fees[client_name]),client_name))


	# Get market & sort by maximum difference
	if option.loop > 0 :
		while True :
			market_prices = crypto.market.get_all_market_prices(clients)
			market_prices.sort_values(by='delta', inplace=True, ascending=False)
			get_transactions_scenarios(market_prices,clients_fees,clients_dict,cols_list)
			time.sleep(option.loop)
	else :
		market_prices = crypto.market.get_all_market_prices(clients)
		market_prices.sort_values(by='delta', inplace=True, ascending=False)
		get_transactions_scenarios(market_prices,clients_fees,clients_dict,cols_list)

