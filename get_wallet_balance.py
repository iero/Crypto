import sys, os
import time
import argparse

import csv
import pandas as pd
import numpy as np

import crypto

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--params", type=str, help="file.xml", required=True)
	option = parser.parse_args()

	clients = crypto.utils.get_clients(option.params)
	out_dir = crypto.utils.get_out_dir(option.params)

	for client in clients :
		if type(client) is crypto.etherClient :
			balance = crypto.portfolio.get_balance(client)
			for key,val in balance.items():
				print('[{0}] {1} eth'.format(key,val))
