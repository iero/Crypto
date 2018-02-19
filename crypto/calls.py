import crypto

# Verify if values are not crazy
def verify_call_buy(actual,support,buy) :
	if support > buy :
		print('Error : You cannot buy below support. It is stupid and I will not do that for you')
		return False

	for val in [support,buy] :
		delta_with_last_close = ((val -  actual) / actual)*100

		if val > actual :
			print('Error : {0} target is above actual value ({1})'.format(val,actual))
			print('Error : You don\'t need a script to do that')
			return False
		elif delta_with_last_close < -50 :
			print('Warning : {0} target is {1:.0f}% below actual value '.format(val,delta_with_last_close))

	return True
