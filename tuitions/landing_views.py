import json
import uuid
from django.http import HttpResponse
from django.shortcuts import render, redirect

from .models import *


# Views

def index(request):
	#if not request.user.is_authenticated:
	#	return HttpResponse("Yoda is under maintenance. We will be back very soon.")
	subject_filter = {}
	class_filter = {}
	area_filter = {}

	for subject in OfflineSubject.objects.filter(country='BD').order_by('name'):
		# Set subjects
		subject_filter.setdefault(subject.name, {
			'ids': [],
			'classes': []
		})
		subject_filter[subject.name]['ids'].append(subject.id)
		subject_filter[subject.name]['classes'].append(subject.sub_category)

		# Set classes
		class_filter.setdefault(subject.sub_category, [])
		class_filter[subject.sub_category].append(subject.id)

	for area in Area.objects.filter(country='BD'):
		# Set areas
		area_filter[area.name] = area.id

	return render(request, 'landing/index.html', {
		'subject_filter': subject_filter,
		'class_filter': class_filter,
		'area_filter': area_filter
	})


def tutor_list(request):
	return redirect('https://app.yodabd.com/tutor-list')


def tutor_details_slug(request, tutor_slug):
	if Tutor.objects.filter(old_slug=tutor_slug).exists():
		tutor = Tutor.objects.values(
			'full_name', 'about', 'display_picture', 'uuid'
		).filter(old_slug=tutor_slug)[0]
	else:
		return HttpResponse('Not found.', status=404)

	return render(request, 'landing/tutor_details.html', {
		'tutor_uuid': str(tutor['uuid']),
		'tutor': tutor,
	})


def tutor_details_uuid(request, tutor_uuid):
	try:
		tutor_uuid = uuid.UUID(tutor_uuid)
	except Exception as e:
		return HttpResponse('Invalid tutor UUID.', status=400)

	if Tutor.objects.filter(uuid=tutor_uuid).exists():
		tutor = Tutor.objects.values(
			'full_name', 'about', 'display_picture', 'uuid'
		).filter(uuid=tutor_uuid)[0]
	else:
		return HttpResponse('Not found.', status=404)

	return render(request, 'landing/tutor_details.html', {
		'tutor_uuid': str(tutor['uuid']),
		'tutor': tutor,
	})

