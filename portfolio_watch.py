import sys

import argparse

import pandas as pd
import numpy as np

import crypto

def get_options() :
	parser = argparse.ArgumentParser()
	parser.add_argument("--params", type=str, help="file.xml", required=True)
	parser.add_argument("--save", type=bool, help="Save portfolio", default=False)
	parser.add_argument("--dust", help="Show dust", action='store_true')
	parser.add_argument("--exchange", type=str, help="platform (binance or kucoin)", required=False)
	return parser.parse_args()

if __name__ == "__main__":

	option = get_options()
	clients = crypto.utils.get_clients(option.params)
	out_dir = crypto.utils.get_out_dir(option.params)

	main_market_price = None
	for client in clients :
		if option.exchange is not None and option.exchange != crypto.utils.get_client_name(client) :
			continue

		print('[{0}]'.format(crypto.utils.get_client_name(client)))
		# crypto.utils.verify_time(client)
		# Get prices
		market_prices = crypto.market.get_market_prices(client)

		# Get portfolio and add equivalent values
		portfolio = crypto.portfolio.get_portfolio(client)
		# crypto.portfolio.show_portfolio(portfolio,0)

		# Get active trading position
		trades = crypto.trades.get_active_trades(client,market_prices)

		# add active trades to portfolio
		portfolio = crypto.trades.add_active_trades_to_portfolio(portfolio, trades)

		# add current prices (eth, btc, usd)
		portfolio = crypto.portfolio.add_market_prices_to_portfolio(portfolio,market_prices)

		if option.dust :
			dust_limit = 0
		else :
			dust_limit = 5

		crypto.portfolio.show_portfolio(portfolio,dust_limit)
		crypto.trades.show_trades(trades)

		# In beta (too long to execute) :
		#crypto.portfolio.add_original_buy_transactions(client, portfolio, market_prices)



