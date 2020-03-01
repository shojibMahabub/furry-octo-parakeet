from django.conf.urls import url
from django.views.generic import TemplateView
from django.urls import path

from . import landing_views


urlpatterns = [
	# Landing
	url(r'^$', landing_views.index, name='index'),

	# Tutor related fields
	path('tutor_list/', landing_views.tutor_list),
	path('tutor/<tutor_slug>/', landing_views.tutor_details_slug),
	path('tutor-details/<tutor_uuid>/', landing_views.tutor_details_uuid),

	# Static pages
	path('about-us/', TemplateView.as_view(template_name='landing/about.html'), name='about'),
	path('how-it-works/', TemplateView.as_view(template_name='landing/how-it-works.html'), name='how-it-works'),
	path('tips/', TemplateView.as_view(template_name='landing/tips.html'), name='tips'),
	path('terms-and-conditions/', TemplateView.as_view(template_name='landing/terms-and-conditions.html'), name='terms-and-conditions'),
	path('privacy-policy/', TemplateView.as_view(template_name='landing/privacy-policy.html'), name='privacy-policy'),
]

