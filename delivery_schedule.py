#!/usr/bin/python3
import MySQLdb
import config
import requests
import datetime
from datetime import datetime
import email_helper


def get_packages_for_user(user_id):
	# Setup MySQL Connection
	db = MySQLdb.connect(host="localhost", user="root", passwd=config.db_password, db="wheresmystuff")
	cursor = db.cursor(MySQLdb.cursors.DictCursor)

	get_pkgs_query = """SELECT * FROM packages WHERE user_id = %s"""
	get_pkgs_parameters = [user_id]

	user_packages = []
	cursor.execute(get_pkgs_query, get_pkgs_parameters)
	packages = cursor.fetchall()
	for package in packages:

		package_id = package["id"]
		get_trackers_query = """SELECT * FROM trackers WHERE package_id = %s"""
		get_trackers_parameters = [package_id]

		cursor.execute(get_trackers_query, get_trackers_parameters)
		tracker = cursor.fetchone()
		if tracker["status"] != "delivered": # Skip packages that have already been delivered
			
			if tracker["status"] in ("unknown","pre_transit","in_transit","out_for_delivery","available_for_pickup"):
				index = get_index_of_date(user_packages, tracker["est_delivery_date"])

				if index == -1:
					user_packages.append([tracker["est_delivery_date"], package])
				else:
					user_packages[index].append(package)
			else: # return_to_sender, failure, cancelled, error
				fake_date = datetime.strptime("January 31, 2100", "%B %d, %Y")
				index = get_index_of_date(user_packages, fake_date)

				if index == -1:
					user_packages.append([fake_date, package])
				else:
					user_packages[index].append(package)

	return(user_packages)


def get_index_of_date(array_to_search, date_to_find):
	dates_only = []
	for duple in array_to_search:

		dates_only.append(duple[0].strftime("%A %B %d, %Y"))

	try:
		index = dates_only.index(date_to_find.strftime("%A %B %d, %Y"))
	except:
		index = -1

	return(index)


def generate_delivery_schedule_for_user(user, user_packages):
	user_packages.sort()
	email_body = ""

	try:
		for user_package in user_packages:
			
			fake_date = datetime.strptime("January 31, 2100", "%B %d, %Y")
			if user_package[0] < fake_date:
				delivery_date = user_package[0].strftime("%A %B %d, %Y")
				email_body = email_body + "Arriving on " + delivery_date + ": " + "\n"
			else:
				email_body = email_body + "Delivery unknown for: " + "\n"


			for i in range(1, len(user_package)):

				description = str(user_package[i]["description"])
				carrier = str(user_package[i]["carrier"])
				tracking_code = str(user_package[i]["tracking_code"])
				current_status = get_current_status(user_package[i])
				current_location = get_current_location(user_package[i])

				email_body = email_body + description + " (currently " + current_status + " at " + current_location + ")\n"
			else:
				email_body = email_body + "\n"
	except:
		print("Exception in generate_delivery_schedule_for_user()")

	send_email(user, email_body)


def send_email(user, email_json):
	from_addr = "Support at WheresMyStuff<support@sandbox6441ed402cbe4179802eb8bf0af5d96d.mailgun.org>"
	to_addr = str(user["email"])
	bcc_addr = "ethanteng@gmail.com"
	subject = "Your upcoming deliveries"
	email_helper.send_schedule_via_mailgun(from_addr, to_addr, bcc_addr, subject, email_json)


def get_current_status(package):
	# Setup MySQL Connection
	db = MySQLdb.connect(host="localhost", user="root", passwd=config.db_password, db="wheresmystuff")
	cursor = db.cursor(MySQLdb.cursors.DictCursor)

	query = """SELECT * FROM trackers WHERE package_id = %s"""
	parameters = [package["id"]]
	cursor.execute(query, parameters)
	tracker = cursor.fetchone()

	return(str(tracker["status"]))


def get_current_location(package):
	# Setup MySQL Connection
	db = MySQLdb.connect(host="localhost", user="root", passwd=config.db_password, db="wheresmystuff")
	cursor = db.cursor(MySQLdb.cursors.DictCursor)

	query = """SELECT * FROM trackers WHERE package_id = %s"""
	parameters = [package["id"]]
	cursor.execute(query, parameters)
	tracker = cursor.fetchone()

	location = str(tracker["current_city"]) + " " + str(tracker["current_state"])
	return(location)


# Setup MySQL Connection
db = MySQLdb.connect(host="localhost", user="root", passwd=config.db_password, db="wheresmystuff")
cursor = db.cursor(MySQLdb.cursors.DictCursor)

cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
for user in users:
	
	user_packages = get_packages_for_user(user["id"])
	if (len(user_packages) >= 1):
		generate_delivery_schedule_for_user(user, user_packages)