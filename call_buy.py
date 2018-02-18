import sys, os
import time
import argparse

import csv
import pandas as pd
import numpy as np

import crypto

def add_inf(df,buy) :
	df['change'] = (df['Close'] -  df['Open']) / df['Open']
	df['change'] = pd.Series(["{0:.2f}%".format(val * 100) for val in df['change']], index = df.index)

	df['to_target'] = (buy -  df['Close']) / df['Close']
	df['to_target'] = pd.Series(["{0:.0f}%".format(val * 100) for val in df['to_target']], index = df.index)

	return df

def show_df(df) :
	pd.set_option('expand_frame_repr', False)
	df.index = df.index.strftime('%H:%M')
	print(df.tail(15))

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--params", type=str, help="file.xml", required=True)

	# Asset
	parser.add_argument("--exchange", type=str, help="platform (ie : binance)", required=True)
	parser.add_argument("--pair", type=str, help="Pair to trade (ie: ETH-BTC)", required=True)
	# parser.add_argument("--bag", type=float, help="Bag to trade", required=True)

	# Buy Parameters
	parser.add_argument("--support", type=float, help="Support", required=True)
	parser.add_argument("--buy", type=float, help="Min value to buy", required=True)
	# parser.add_argument("--stoploss", type=str, help="Stoploss (ie: 5% or absolute value)", required=True)
	option = parser.parse_args()

	clients = crypto.utils.get_clients(option.params)
	out_dir = crypto.utils.get_out_dir(option.params)

	# Only with binance now
	client = crypto.utils.get_client(name=option.exchange,file=option.params)
	if not client or option.exchange != 'binance' :
		print('Client {0} unknown'.format(option.exchange))
		sys.exit(1)

	df = crypto.klines.get_last_klines(client,option.pair,1)
	df = add_inf(df,option.buy)
	show_df(df)

	# Synchronise


	# Loop every minute :
	timer = 1
	while True :
		df = crypto.klines.get_last_klines(client,option.pair,timer)
		df = add_inf(df,option.buy)
		show_df(df)
		time.sleep(timer*60)




