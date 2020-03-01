import re

from django.core.exceptions import ValidationError


# Validators

def validate_bd_phone_number(phone_number):
	"""Validates a Bangladeshi phone number."""
	phone_number = re.sub(r'\D', '', phone_number)
	search = re.search(
		r'^(008801|8801|01)(?P<local_number>[1|5-9]{1}(\d){8})$',
		phone_number
	)
	if not search:
		raise ValidationError(
			'Must be a valid Bangaldeshi phone number.'
		)
	else:
		phone_number = '+8801' + search.group('local_number')
	return phone_number


def validate_us_phone_number(phone_number):
	return phone_number


# Maps

PHONE_NUMBER_VALIDATOR_COUNTRY_MAP = {
	'BD': validate_bd_phone_number,
	'US': validate_us_phone_number
}

