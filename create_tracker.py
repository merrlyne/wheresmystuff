#!/usr/bin/python3
import easypost
import config

easypost.api_key = config.easypost_test_api_key
#easypost.api_key = config.easypost_prod_api_key

def create_tracker(tracking_code, carrier):

	try:
		if (carrier is None):
			tracker = easypost.Tracker.create(

				tracking_code=tracking_code
			)
		else:
			tracker = easypost.Tracker.create(

				tracking_code=tracking_code,
				carrier=carrier
			)
	except:
		print("Error while creating EasyPost tracker")