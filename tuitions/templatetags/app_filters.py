from django import template

register = template.Library()

@register.filter(name='get_app_url')
def get_app_url(path):
	#return 'https://app.yodabd.com/' + path
	return 'https://app-yoda.web.app/' + path