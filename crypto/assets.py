import crypto

def get_deposit_address(client,coin) :
	if type(client) is crypto.binanceClient :
		ad = client.get_deposit_address(asset=coin)
		if 'address' in ad :
			return ad['address']
	elif type(client) is crypto.kucoinClient :
		try :
			return client.get_deposit_address(coin)['address']
		except :
			return None
	# Library for poloniex is not complete
	# elif type(client) is crypto.poloClient :
	# 	print(client.returnDepositAddresses)
	return None

def get_withdrawal_fees(client,url) :
	return None

# infouser = client.get_user()
# Test if can withdraw
# print(infouser['credentialStatus'])
