import os, time, sys
import argparse

from datetime import datetime, date, timedelta

import pandas as pd

import crypto

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--params", type=str, help="file.xml", required=True)
	parser.add_argument("--pair", type=str, help="Pair to trade (ie ETHBTC)", required=False)
	parser.add_argument("--exchange", type=str, help="platform (binance, kucoin, poloniex, gdax..)", required=False)
	#parser.add_argument("--year", type=int, help="Year to check", required=True)
	option = parser.parse_args()

	clients = crypto.utils.get_clients(option.params)
	out_dir = crypto.utils.get_out_dir(option.params)

	date_max = datetime.utcnow()

	for client in clients :
		if option.exchange is not None and option.exchange != crypto.utils.get_client_name(client) :
			continue

		client_name = crypto.utils.get_client_name(client)

		list_pairs = {}
		if option.pair is None :
			list_pairs = crypto.utils.get_all_pairs(client)
		else :
			pairs_available = crypto.utils.get_all_pairs(client)
			if option.pair in pairs_available.keys() :
				list_pairs[option.pair] = pairs_available[option.pair]
			else :
				print('Pair {0} not available on {1}'.format(option.pair,crypto.utils.get_client_name(client)))

		# print(list_pairs)

		# Original = opening date
		if type(client) is crypto.binanceClient :
			# Binance opening : 14/07/2017
			date_original = datetime(2017, 7, 14)
		elif type(client) is crypto.kucoinClient :
			# Kucoin opening : 27/09/2017
			date_original = datetime(2017, 9, 27)
		elif type(client) is crypto.poloClient :
			# Dont know when opening but 01/01/2016 seems good.
			date_original = datetime(2016, 1, 1)
		elif type(client) is crypto.gdaxClient or type(client) is crypto.gdaxPClient :
			date_original = datetime(2015, 1, 15)
		# 	date_max = datetime(2016, 1, 2)
		# 	df = crypto.klines.get_historical_klines(client,'ETH-USD',date_original,date_max)
		# 	print(df)

		# sys.exit(1)
		loop_timer = 0.5
		print ('{0} pairs found on {1}'.format(len(list_pairs),crypto.utils.get_client_name(client)))
		for pair in list_pairs :
			file = out_dir+'/history/'+client_name+'/history_'+pair+".csv"

			# If file exists, complete
			if os.path.exists(file) :
				print('[{}] already found.. load and complete'.format(pair))
				resultat = pd.read_csv(file)
				resultat.index = resultat['time']
				resultat['time'] = resultat['time'].apply(pd.to_datetime)
				resultat = resultat.drop('time', 1)
				date = datetime.strptime(resultat.tail(1).index[0], '%Y-%m-%d %H:%M:%S')
			else :
				resultat = pd.DataFrame()
				date = date_original

			while date_max - date > timedelta(minutes = 5) :

				df = crypto.klines.get_historical_klines(client,list_pairs[pair],date,date_max)

				# too early ?
				if df.empty :
					date = date + timedelta(days = 30)
					print('[{0}] No value for {1}'.format(pair,date))
				else :
					last_date = df.tail(1).index[0]
					print('[{0}] Updated from {1} to {2}'.format(pair,date,last_date))

					# End of list
					if date == last_date :
						break
					else :
						date = last_date
					resultat = pd.concat([resultat, df])

				time.sleep(loop_timer)

			resultat.to_csv(file)
