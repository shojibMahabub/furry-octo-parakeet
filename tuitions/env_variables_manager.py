# Environment variables

MAIN_API_KEY = 'LearningMadeSimple123456!'
AUTH_JWT_SECRET = 'Take over the education industry we must!'
BD_SMS_SENDER_PASSWORD = '33f@2B19'
SENDGRID_AUTH_TOKEN = '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'
BKASH_CREDENTIALS = {
	'base_url': 'https://checkout.pay.bka.sh/v1.2.0-beta/checkout',
	'username': 'YODA',
	'password': r'yo@1da9t3ecHLr',
	'app_key': '1908gev93955a7due9g391sevf',
	'app_secret': '16amleu1kqkhj8n1a45lvts788uk5c40qq1ou7n95kqp8db53cbi',
	'x-app-key': '1908gev93955a7due9g391sevf'
}


# Getters

def get_main_api_key():
	return MAIN_API_KEY


def get_auth_jwt_secret():
	return AUTH_JWT_SECRET


def get_bd_sms_sender_password():
	return BD_SMS_SENDER_PASSWORD


def get_sendgrid_auth_token():
	return SENDGRID_AUTH_TOKEN


def get_bkash_credentials():
	return BKASH_CREDENTIALS

