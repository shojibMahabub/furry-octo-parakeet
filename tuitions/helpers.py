import arrow
import json
import requests

from random import randint
from six import string_types

from .env_variables_manager import (
	get_bd_sms_sender_password, get_sendgrid_auth_token
)

# Constants

JOBS_LIMIT = {
	'basic': {
		'daily_direct_requests': 1,
		'daily_hot_jobs': 0,
		'monthly_direct_requests': 5,
		'monthly_hot_jobs': 0
	},
	'premium': {
		'daily_direct_requests': 3,
		'daily_hot_jobs': 5,
		'monthly_direct_requests': 5,
		'monthly_hot_jobs': 10
	}
}


# Helper functions

def get_positive_or_zero(num):
	if num < 0:
		return 0
	else:
		return num

def field_is_not_null(value):
	"""Checks if a given model field's value is null or not."""
	if value == None:
		return False
	elif isinstance(value, string_types):
		return not value == ''
	else:
		return True


def bd_sms_sender(phone_number, message):
	"""Sends an SMS to a Bangladeshi phone number."""
	requests.post(
		'http://sms.sslwireless.com/pushapi/dynamic/server.php',
		data={
			'user': 'Yoda',
			'pass': get_bd_sms_sender_password(),
			'sms[0][0]': phone_number,
			'sms[0][1]': message,
			'sms[0][2]': 54354354354,
			'sid': 'Yoda'
		}
	)


def us_sms_sender(phone_number, message):
	pass


def send_email(to_address, subject, body):
	"""Sends an email to a given address."""
	requests.post('https://api.sendgrid.com/v3/mail/send',
    	data = json.dumps(
    		{
		        "personalizations": [
		            {
		                "to": [
		                    {
		                        "email": to_address
		                    }
		                ],
		                "subject": subject
		            }
		        ],
		        "from": {
		            "email": "noreply@yodabd.com"
		        },
		        "content":[
		            {
		                "type": "text/html",
		                "value": body
		            }
		        ]
		    }
    	),
    	headers={"Authorization": f'Bearer {get_sendgrid_auth_token()}', "Content-Type":"application/json"}
	)


def get_empty_schedule_array():
	"""Generates an empty boolean array with a size of 21."""
	empty_schedule_array = []
	for i in range(21):
		empty_schedule_array.append(False)
	return empty_schedule_array


def get_default_ops_notes():
	"""Generates the default for the ops notes JSONField."""
	return {'notes': []}


def sort_and_stringify(arr):
	"""Sorts the given array, turns it into a string, and removes spaces."""
	result = str(sorted(arr))
	return result.replace(' ', '')


def get_default_date_till_premium_account_valid():
	"""Returns a datetime in the past."""
	return arrow.get('1950-01-01T00:00:00').datetime


def get_random_for_tutor_filter():
	"""Returns a random integer between 0 and 99."""
	return randint(0, 99)


# Maps

SMS_SENDER_COUNTRY_MAP = {
	'BD': bd_sms_sender,
	'US': us_sms_sender,
}