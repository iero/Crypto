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
	print(df.tail(5))

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

	out_dir = crypto.utils.get_out_dir(option.params)
	client = crypto.utils.get_client(name=option.exchange,file=option.params)

	# Only with binance now
	if not client or option.exchange != 'binance' :
		print('Client {0} unknown'.format(option.exchange))
		sys.exit(1)

	#TODO Verify that bag is available for trade
	# portfolio = crypto.portfolio.get_portfolio(client)

	# First call
	df = crypto.klines.get_last_klines(client,option.pair,1)
	df = add_inf(df,option.buy)
	show_df(df)

	#Verify if support & buy values are not strange
	last_close = float(df.tail(1).iloc[0]['Close'])
	if not crypto.calls.verify_call_buy(last_close,option.support,option.buy) :
		sys.exit(1)

	#TODO : Synchronise

	# We are before buy zone
	step_in_buy_zone = False
	got_a_bag = False

	# Loop every minute :
	timer = 1
	while True :
		df = crypto.klines.get_last_klines(client,option.pair,timer)
		last_open = float(df.tail(1).iloc[0]['Open'])
		last_close = float(df.tail(1).iloc[0]['Close'])

		# Enter in buyzone for first time
		if not step_in_buy_zone and option.support < last_open < option.buy and option.support < last_close < option.buy :
			print ('Reached buy zone !')
			step_in_buy_zone = True

		# Support broken and close 5% below, but nothing bought
		if last_open < option.support and last_close < option.support and lastclose < 0.95 * option.support :
			# If bought : sell, if not, exit
			if got_a_bag :
				print ('Support broken ! Sell bag')
			else :
				print ('Support broken !')
			sys.exit(1)

		# Go out above buy zone
		if step_in_buy_zone and option.buy < last_open and option.buy < last_close :
			print ('Signal to buy !')
			got_a_bag = True

		time.sleep(timer*60)




