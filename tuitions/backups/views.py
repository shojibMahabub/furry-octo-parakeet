import arrow
import jwt
import uuid

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django_countries.fields import Country
from django.db import transaction
from django.shortcuts import render
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from six import string_types

from .env_variables_manager import get_auth_jwt_secret
from .helpers import *
from .models import *
from .permissions import *
from .serializers import *


# Methods

def generate_ops_note(user, message):
	return {
		'user':	UserSerializer(user).data,
		'message': message,
		'added_at': str(arrow.utcnow().datetime)
	}


# Views

class Index(APIView):
	"""Index of the Yoda API."""
	permission_classes = (CorrectAPIKeyPermission,)

	def get(self, request, format=None):
		return Response({
			'detail': 'Welcome to the Yoda API!'
		})


# Sign up views

class UserSignUp(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, format=None):
		# Check if country is given
		if not 'country' in request.data:
			return Response({
				'country': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if service available for the given country
		if not request.data['country'] in PHONE_NUMBER_VALIDATOR_COUNTRY_MAP:
			return Response({
				'country': 
				['Our service is not yet available in this country.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if phone number is given
		if not 'phone_number' in request.data:
			return Response({
				'phone_number': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Validate the phone number
		try:
			request.data['phone_number'] = PHONE_NUMBER_VALIDATOR_COUNTRY_MAP[
				request.data['country']
			](request.data['phone_number'])
		except Exception as e:
			return Response(
				{'phone_number': e},
				status=status.HTTP_400_BAD_REQUEST
			)

		# Make sure no other verified user with the same phone number exists
		if self.get_model_class().objects.filter(
			phone_number=request.data['phone_number']).exists():
			obj = self.get_model_class().objects.get(
				phone_number=request.data['phone_number']
			)
			if obj.is_phone_number_verified:
				return Response({
					'phone_number':
					['Another user with this phone number already exists.']
				}, status=status.HTTP_400_BAD_REQUEST)
			else:
				obj.full_name = request.data['full_name']
				obj.set_otp()
				obj.save()
				return Response({
					'detail': 'Confirm sign up by signing in using the OTP.',
					'phone_number': request.data['phone_number']
				}, status=status.HTTP_200_OK)

		# Handle the serializer
		serializer = self.get_serializer_class()(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response({
				'detail': 'Confirm sign up by signing in using the OTP.',
				'phone_number': request.data['phone_number']
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParentSignUp(UserSignUp):
	def get_model_class(self):
		return Parent

	def get_serializer_class(self):
		return ParentSignUpSerializer


class StudentSignUp(UserSignUp):
	def get_model_class(self):
		return Student

	def get_serializer_class(self):
		return StudentSignUpSerializer


# Login set OTP views

class UserLoginSetOTP(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, format=None):
		# Check if country is given
		if not 'country' in request.data:
			return Response({
				'country': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if service available for the given country
		if not request.data['country'] in PHONE_NUMBER_VALIDATOR_COUNTRY_MAP:
			return Response({
				'country': 
				['Our service is not yet available in this country.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if phone number is given
		if not 'phone_number' in request.data:
			return Response({
				'phone_number': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Validate the phone number
		try:
			request.data['phone_number'] = PHONE_NUMBER_VALIDATOR_COUNTRY_MAP[
				request.data['country']
			](request.data['phone_number'])
		except Exception as e:
			return Response(
				{'phone_number': e},
				status=status.HTTP_400_BAD_REQUEST
			)

		# Check if the user exists or not
		if self.get_model_class().objects.filter(
			phone_number=request.data['phone_number']).exists():
			# User exists, so set OTP and send success response
			obj = self.get_model_class().objects.get(
				phone_number=request.data['phone_number']
			)
			obj.set_otp()
			obj.save()
			return Response({
				'detail': 
				'Success! Sign in using the OTP sent to your number.',
				'phone_number': request.data['phone_number']
			}, status=status.HTTP_200_OK)
		else:
			# User does not exist, so send 404
			return Response({
				'phone_number': 
				['No user found with this phone number. Please sign up first.'] 
			}, status=status.HTTP_404_NOT_FOUND)


class ParentLoginSetOTP(UserLoginSetOTP):
	def get_model_class(self):
		return Parent


class StudentLoginSetOTP(UserLoginSetOTP):
	def get_model_class(self):
		return Student


class TutorLoginSetOTP(UserLoginSetOTP):
	def get_model_class(self):
		return Tutor


# Login confirm OTP views

class UserLoginConfirmOTP(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_obj(self, phone_number):
		return self.get_model_class().objects.get(
			phone_number=phone_number
		)

	def get_user_details_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, format=None):
		# Check if country is given
		if not 'country' in request.data:
			return Response({
				'country': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if service available for the given country
		if not request.data['country'] in PHONE_NUMBER_VALIDATOR_COUNTRY_MAP:
			return Response({
				'country': 
				['Our service is not yet available in this country.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if phone number is given
		if not 'phone_number' in request.data:
			return Response({
				'phone_number': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Validate the phone number
		try:
			request.data['phone_number'] = PHONE_NUMBER_VALIDATOR_COUNTRY_MAP[
				request.data['country']
			](request.data['phone_number'])
		except Exception as e:
			return Response(
				{'phone_number': e},
				status=status.HTTP_400_BAD_REQUEST
			)

		# Check if the user exists or not
		if self.get_model_class().objects.filter(
			phone_number=request.data['phone_number']).exists():
			# User exists, so check OTP
			obj = self.get_obj(request.data['phone_number'])
			if obj.otp == request.data['otp']:
				# OTP matched, check if it has expired or not
				if obj.otp_expiry_timestamp < arrow.utcnow().timestamp:
					return Response({
						'otp': ['The OTP has expired. Please login again.']
					}, status=status.HTTP_400_BAD_REQUEST)

				# Not expired, so verify phone number if needed
				if not obj.is_phone_number_verified:
					obj.is_phone_number_verified = True
					obj.save()

				# Send the response
				return Response({
					'detail': 'Successful login.',
					'auth_obj': {
						'user_type': obj.__class__.__name__.lower(),
						'auth_jwt': obj.get_auth_jwt()
					},
					'user_obj': self.get_user_details_serializer_class()(
						obj
					).data
				})
			else:
				# OTP does not match
				return Response({
					'otp': ['Incorrect OTP. Please try again.']
				}, status=status.HTTP_400_BAD_REQUEST)
		else:
			# User does not exist, so send 404
			return Response({
				'phone_number': 
				['No user found with this phone number. Please sign up first.'] 
			}, status=status.HTTP_404_NOT_FOUND)


class ParentLoginConfirmOTP(UserLoginConfirmOTP):
	def get_model_class(self):
		return Parent

	def get_user_details_serializer_class(self):
		return ParentDetailsSerializer


class StudentLoginConfirmOTP(UserLoginConfirmOTP):
	def get_model_class(self):
		return Student

	def get_user_details_serializer_class(self):
		return StudentDetailsSerializer


class TutorLoginConfirmOTP(UserLoginConfirmOTP):
	def get_model_class(self):
		return Tutor

	def get_user_details_serializer_class(self):
		return TutorDetailsSerializer


# User details views

class UserDetails(APIView):
	permission_classes = (UserPermissionTutorSelectRelated,)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def apply_daily_activity_reward_if_eligible(self, obj):
		# Check if the user is eligible for daily activity reward
		self.is_eligible_for_daily_reward = False
		if not field_is_not_null(obj.last_active_at):
			self.is_eligible_for_daily_reward = True
			obj.active_daily() # Also saves
		else:
			if not obj.last_active_at == arrow.utcnow().date():
				self.is_eligible_for_daily_reward = True
				obj.active_daily() # Also saves

	def get(self, request, format=None):
		obj = self.user
		self.apply_daily_activity_reward_if_eligible(obj)
		serializer = self.get_serializer_class()(obj)
		return Response({
			'user_obj': serializer.data,
			'is_eligible_for_daily_reward': self.is_eligible_for_daily_reward
		})

	def post(self, request, format=None):
		obj = self.user
		serializer = self.get_serializer_class()(obj, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response({
				'user_obj': serializer.data
			}, status=status.HTTP_200_OK)

		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParentDetails(UserDetails):
	def get_serializer_class(self):
		return ParentDetailsSerializer


class StudentDetails(UserDetails):
	def get_serializer_class(self):
		return StudentDetailsSerializer


class TutorDetails(UserDetails):
	def get_serializer_class(self):
		return TutorDetailsSerializer

	def post(self, request, format=None):
		return Response({
			'detail': 'Method not allowed.'
		}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# Tutor profile views

class TutorProfile(APIView):
	permission_classes = (UserPermissionTutorSelectRelated,)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_response_key(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def update_extra(self, request, tutor):
		pass

	def get(self, request, format=None):
		tutor = self.user
		serializer = self.get_serializer_class()(tutor)
		return Response({
			self.get_response_key(): serializer.data
		})

	def post(self, request, format=None):
		tutor = self.user
		serializer = self.get_serializer_class()(tutor, data=request.data)
		if serializer.is_valid():
			# Extra update before saving
			self.update_extra(request, tutor)
			serializer.save()
			return Response({
				'user_obj': TutorDetailsSerializer(tutor).data,
				self.get_response_key(): serializer.data
			}, status=status.HTTP_200_OK)

		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TutorPersonalInformation(TutorProfile):
	def get_serializer_class(self):
		return TutorPersonalInformationSerializer

	def get_response_key(self):
		return 'personal_information'


class TutorTeachingPreferences(TutorProfile):
	def get_serializer_class(self):
		return TutorTeachingPreferencesSerializer

	def get_response_key(self):
		return 'teaching_preferences'

	def update_extra(self, request, tutor):
		# Adding offline preferred teaching areas to the M2M serialized data
		if 'offline_preferred_teaching_areas' in request.data:
			tutor.m2m_fields_serialized[
				'offline_preferred_teaching_areas'
			] = AreaSerializer(
				Area.objects.filter(
					id__in=request.data['offline_preferred_teaching_areas']
				),
				many=True
			).data

		# Adding offline preferred teaching subjects to the M2M serialized data
		if 'offline_preferred_teaching_subjects' in request.data:
			tutor.m2m_fields_serialized[
				'offline_preferred_teaching_subjects'
			] = OfflineSubjectSerializer(
				OfflineSubject.objects.filter(
					id__in=request.data['offline_preferred_teaching_subjects']
				),
				many=True
			).data


class TutorAcademicBackground(APIView):
	permission_classes = (UserPermissionTutorSelectRelated,)

	def get(self, request, format=None):
		tutor = self.user
		return Response({
			'undergraduate_university_academic_bg': 
			TutorUndergraduateUniversityABSerializer(
				tutor.undergraduate_university_academic_bg).data,
			'school_academic_bg': 
			TutorAcademicBackgroundSerializer(tutor.school_academic_bg).data,
			'college_academic_bg': 
			TutorAcademicBackgroundSerializer(tutor.college_academic_bg).data

		})

	def post(self, request, format=None):
		tutor = self.user
		if (request.data['academic_background_type'] == 
			'undergraduate_university_academic_bg'):
			serializer = TutorUndergraduateUniversityABSerializer(
				tutor.undergraduate_university_academic_bg, data=request.data
			)
		elif request.data['academic_background_type'] == 'school_academic_bg':
			serializer = TutorAcademicBackgroundSerializer(
				tutor.school_academic_bg, data=request.data
			)
		elif request.data['academic_background_type'] == 'college_academic_bg':
			serializer = TutorAcademicBackgroundSerializer(
				tutor.college_academic_bg, data=request.data
			)
		else:
			return Response({
				'detail': 'Incorrect academic background type.'
			}, status=status.HTTP_400_BAD_REQUEST)

		if serializer.is_valid():
			serializer.save()
			return Response({
				'user_obj': TutorDetailsSerializer(tutor).data,
				request.data['academic_background_type']: serializer.data
			}, status=status.HTTP_200_OK)

		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Area, subject, school, and university field of study list views

class AreaList(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get(self, request, country, format=None):
		return Response({
			'areas': AreaSerializer(
				Area.objects.filter(country=Country(country)), many=True
			).data
		})


class OfflineSubjectList(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get(self, request, country, subject_type=None, format=None):
		if subject_type:
			offline_subjects = OfflineSubject.objects.filter(
				country=Country(country),
				subject_type=str(subject_type)
			)
		else:
			offline_subjects = OfflineSubject.objects.filter(
				country=Country(country)
			)
		return Response({
			'offline_subjects': OfflineSubjectSerializer(
				offline_subjects, many=True).data
		})


class SchoolList(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get(self, request, country, format=None):
		return Response({
			'schools': SchoolSerializer(
				School.objects.filter(country=Country(country)), many=True
			).data
		})


class UniversityFieldOfStudyList(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get(self, request, format=None):
		return Response({
			'university_fields_of_study': UniversityFieldOfStudySerializer(
				UniversityFieldOfStudy.objects.all(), many=True
			).data
		})


class UniversityDegreeList(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get(self, request, format=None):
		return Response({
			'university_degrees': UniversityDegreeSerializer(
				UniversityDegree.objects.all(), many=True
			).data
		})


# Tutor filter view

class TutorFilter(APIView, PageNumberPagination):
	page_size = 30
	max_page_size = 30
	permission_classes = (CorrectAPIKeyPermission,)

	def post(self, request, country, format=None):
		# Init serializer
		filter_serializer = TutorFilterSerializer(data=request.data)

		if filter_serializer.is_valid():
			filters = models.Q()

			# Add the country filter (required from URL) and checks
			filters &= models.Q(
				country=Country(country),
				is_suspended_by_ops=False,
				is_deleted=False,
				is_verified_by_ops=True
			)

			# Adding the extra filters
			if request.data.get('gender', ''):
				filters &= models.Q(gender=request.data['gender'],)

			if request.data.get('academic_medium', ''):
				filters &= models.Q(
					academic_medium=request.data['academic_medium'],
				)

			if 'undergraduate_university' in request.data:
				if isinstance(request.data['undergraduate_university'], int):
					filters &= models.Q(
						undergraduate_university=
						request.data['undergraduate_university'],
					)

			if request.data.get('salary_range_start', ''):
				filters &= models.Q(
					salary_range_start__gte=request.data['salary_range_start'],
				)

			if request.data.get('salary_range_end', ''):
				filters &= models.Q(
					salary_range_end__lte=request.data['salary_range_end'],
				)

			if request.data.get('offline_preferred_teaching_areas', []):
				filters &= models.Q(
					offline_preferred_teaching_areas__in=
					request.data['offline_preferred_teaching_areas'],
				)
					
			if request.data.get('offline_preferred_teaching_subjects', []):
				filters &= models.Q(
					offline_preferred_teaching_subjects__in=
					request.data['offline_preferred_teaching_subjects'],
				)

			# Getting the queryset
			tutors = Tutor.objects.select_related(
				'undergraduate_university_academic_bg', 'school_academic_bg',
				'college_academic_bg'
			).filter(filters).distinct()

			# Init paginated serializer and return
			paginated_serializer = TutorPublicSerializer(
				self.paginate_queryset(tutors, self.request), many=True
			)
			return self.get_paginated_response(paginated_serializer.data)

		return Response(
			filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST
		)


# Tutor public views

class TutorPublicDetails(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def get(self, request, tutor_uuid, format=None):
		# Only return if the tutor is verified, not suspended, and has not 
		# deleted their profile.
		if Tutor.objects.filter(
				uuid=uuid.UUID(tutor_uuid),
				is_verified_by_ops=True,
				is_suspended_by_ops=False,
				is_deleted=False
			).exists():
			tutor = Tutor.objects.select_related(
				'undergraduate_university_academic_bg', 'school_academic_bg',
				'college_academic_bg'
			).get(
				uuid=uuid.UUID(tutor_uuid),
				is_verified_by_ops=True,
				is_suspended_by_ops=False,
				is_deleted=False
			)
		else:
			return Response({
				'detail': 'Tutor not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		serializer = TutorPublicSerializer(tutor)

		return Response({
			'tutor': serializer.data
		})


# Jobs views

class RequestForTutorCreate(APIView):
	permission_classes = (UserPermission,)

	def post(self, request, format=None):
		request.data['parent'] = self.user.id
		serializer = RequestForTutorCreateSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response({
				'detail': 'The RFT has been created.',
				'rft': serializer.data
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestForTutorList(APIView, PageNumberPagination):
	page_size = 10
	max_page_size = 10
	permission_classes = (UserPermission,)

	def get(self, request, format=None):
		parent = self.user

		# Getting the RFTs
		request_for_tutors = RequestForTutor.objects.select_related(
			'tuition_area'
		).filter(
			parent=parent, is_rejected_by_ops=False
		)

		# Creating and returning the paginated serializer data
		paginated_serializer = RequestForTutorSerializer(
			self.paginate_queryset(request_for_tutors, self.request), many=True
		)
		return self.get_paginated_response(paginated_serializer.data)


class RequestForTutorDetails(APIView):
	permission_classes = (UserPermission,)

	def get(self, request, rft_uuid, format=None):
		parent = self.user

		# Getting the RFT
		if RequestForTutor.objects.filter(
			uuid=uuid.UUID(rft_uuid), parent=parent, is_rejected_by_ops=False
		).exists():
			request_for_tutor = RequestForTutor.objects.select_related(
				'tuition_area'
			).get(
				uuid=uuid.UUID(rft_uuid),
				parent=parent,
				is_rejected_by_ops=False
			)
		else:
			return Response({
				'detail': 'RFT not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Creating and returning the serializer data
		serializer = RequestForTutorSerializer(request_for_tutor)
		return Response({
			'rft': serializer.data
		})


class DirectRequestCreate(APIView):
	permission_classes = (UserPermission,)

	def post(self, request, tutor_uuid, format=None):
		# Setting the parent
		parent = self.user
		request.data['parent'] = parent.id

		# Checking if tutor exists
		if Tutor.objects.filter(uuid=uuid.UUID(tutor_uuid)).exists():
			tutor = Tutor.objects.get(uuid=uuid.UUID(tutor_uuid))
			request.data['tutor'] = tutor.id
		else:
			return Response({
				'detail': 'Tutor not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Setting the status of the tuition request manually
		request.data['status'] = 'direct-request'

		serializer = DirectRequestCreateSerializer(data=request.data)
		if serializer.is_valid():
			if parent.is_verified_by_ops:
				# Creating the notification only if the parent is verified
				with transaction.atomic():
					serializer.validated_data['notification_created'] = True
					serializer.save()
					job_uuid = serializer.data['uuid']
					Notification.objects.create(
						notification_type='direct-request-create',
						tutor=tutor,
						created_for='tutor',
						title='New direct request',
						body=str(
							'A parent has directly requested you to be the '
							'potential tutor for their children!'
						),
						url=str(
							f'https://app.yoda.com/job-details/{job_uuid}/'
						),
						create_extra_notifications=True
					)
			else:
				# Simply saving the serializer otherwise
				serializer.validated_data['notification_created'] = False
				serializer.save()

			return Response({
				'detail': 'The direct request has been created.',
				'tuition_request': request.data
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TuitionRequestList(APIView, PageNumberPagination):
	page_size = 10
	max_page_size = 10
	permission_classes = (UserPermission,)

	def get_tuition_requests(self, status):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get(self, request, status, format=None):
		# Formatting the status for query
		if status == 'in-process':
			status = ['in-process', 'waiting-for-parent', 'waiting-for-tutor']
		else:
			status = [status]

		# Getting the tuition requests
		tuition_requests = self.get_tuition_requests(status)

		# Creating and returning the paginated serializer data
		paginated_serializer = TuitionRequestSerializer(
			self.paginate_queryset(tuition_requests, self.request), many=True
		)
		return self.get_paginated_response(paginated_serializer.data)


class ParentTuitionRequestList(TuitionRequestList):
	def get_tuition_requests(self, status):
		return TuitionRequest.objects.select_related(
			'parent', 'tutor', 'tuition_area'
		).filter(
			status__in=status, parent=self.user, is_rejected_by_ops=False
		)


class TutorTuitionRequestList(TuitionRequestList):
	def get_tuition_requests(self, status):
		return TuitionRequest.objects.select_related(
			'parent', 'tutor', 'tuition_area'
		).filter(
			status__in=status, tutor=self.user, is_rejected_by_tutor=False,
			is_rejected_by_ops=False, parent__is_verified_by_ops=True, 
			parent__is_suspended_by_ops=False, parent__is_deleted=False,
		)


class TuitionRequestDetails(APIView):
	permission_classes = (UserPermission,)

	def check_if_tuition_request_exists(self, tuition_request_uuid):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_tuition_request(self, tuition_request_uuid):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get(self, request, tuition_request_uuid, format=None):
		# Getting the tuition request
		if self.check_if_tuition_request_exists(tuition_request_uuid):
			tuition_request = self.get_tuition_request(tuition_request_uuid)
		else:
			return Response({
				'detail': 'Tuition request not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Creating and returning the serializer data
		serializer = TuitionRequestSerializer(tuition_request)
		return Response({
			'tuition_request': serializer.data
		})


class ParentTuitionRequestDetails(TuitionRequestDetails):
	def check_if_tuition_request_exists(self, tuition_request_uuid):
		if TuitionRequest.objects.filter(
			uuid=uuid.UUID(tuition_request_uuid), parent=self.user, 
			is_rejected_by_ops=False
		).exists():
			return True
		else:
			return False

	def get_tuition_request(self, tuition_request_uuid):
		return TuitionRequest.objects.select_related(
			'parent', 'tutor', 'tuition_area'
		).get(
			uuid=uuid.UUID(tuition_request_uuid), parent=self.user, 
			is_rejected_by_ops=False
		)


class TutorTuitionRequestDetails(TuitionRequestDetails):
	def check_if_tuition_request_exists(self, tuition_request_uuid):
		if TuitionRequest.objects.filter(
			uuid=uuid.UUID(tuition_request_uuid), tutor=self.user, 
			is_rejected_by_tutor=False, is_rejected_by_ops=False, 
			parent__is_verified_by_ops=True, 
			parent__is_suspended_by_ops=False, parent__is_deleted=False
		).exists():
			return True
		else:
			return False

	def get_tuition_request(self, tuition_request_uuid):
		return TuitionRequest.objects.select_related(
			'parent', 'tutor', 'tuition_area'
		).get(
			uuid=uuid.UUID(tuition_request_uuid), tutor=self.user, 
			is_rejected_by_ops=False
		)


class AcceptDirectRequest(APIView):
	permission_classes = (UserPermissionTutorSelectRelated,)

	def post(self, request, tuition_request_uuid, format=None):
		tutor = self.user

		# Getting the tuition request if it exists, 404 otherwise
		if TuitionRequest.objects.filter(
			uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
			is_rejected_by_ops=False, status='direct-request',
			parent__is_verified_by_ops=True, 
			parent__is_suspended_by_ops=False, parent__is_deleted=False
		).exists():
			tuition_request = TuitionRequest.objects.select_related(
				'parent', 'tutor', 'tuition_area'
			).get(
				uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
				is_rejected_by_ops=False, status='direct-request'
			)
		else:
			return Response({
				'detail': 'Tuition request not found, or not verified.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Checking if the tutor has jobs left, and updating the counts
		jobs_left = tutor.get_jobs_left()
		current_date = jobs_left['current_date']
		current_month = jobs_left['current_month']

		if jobs_left['daily_direct_requests_left'] < 1:
			return Response({
				'detail': 'Daily direct requests limit reached.'
			}, status=status.HTTP_402_PAYMENT_REQUIRED)

		if jobs_left['monthly_direct_requests_left'] < 1:
			return Response({
				'detail': 'Monthly direct requests limit reached.'
			}, status=status.HTTP_402_PAYMENT_REQUIRED)
		
		if current_date in tutor.daily_direct_requests_accepted:
			tutor.daily_direct_requests_accepted[current_date] += 1
		else:
			tutor.daily_direct_requests_accepted[current_date] = 1

		if current_month in tutor.monthly_direct_requests_accepted:
			tutor.monthly_direct_requests_accepted[current_month] += 1
		else:
			tutor.monthly_direct_requests_accepted[current_month] = 1


		# Updating the status of the tuition request
		tuition_request.status = 'in-process'

		# Creating the notifications and saving the objects using a transaction
		with transaction.atomic():
			tutor.save()
			tuition_request.save()

			# Notification for parent
			Notification.objects.create(
				notification_type='direct-request-accept',
				parent=tuition_request.parent,
				created_for='parent',
				title='Direct request accepted by tutor',
				body=str(
					'A tutor you directly requested has accepted the job '
					'offer. Please expect a call from them before finalizing '
					'the details and confirming the job.'
				),
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=True
			)

			# Notification for tutor
			Notification.objects.create(
				notification_type='direct-request-accept',
				tutor=tuition_request.tutor,
				created_for='tutor',
				title='Direct request accepted',
				body=str(
					'You have accepted the direct request. Please call the '
					'parent to finalize and confirm the job.'
				),
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=False
			)

			return Response({
				'detail': 'Direct request accepted.',
				'user_obj': TutorDetailsSerializer(tutor).data,
				'tuition_request': 
				TuitionRequestSerializer(tuition_request).data
			})


class ApplyToHotJob(APIView):
	permission_classes = (UserPermissionTutorSelectRelated,)

	def post(self, request, tuition_request_uuid, format=None):
		tutor = self.user

		# Getting the tuition request if it exists, 404 otherwise
		if TuitionRequest.objects.filter(
			uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
			is_rejected_by_ops=False, status='hot-job',
			parent__is_verified_by_ops=True, 
			parent__is_suspended_by_ops=False, parent__is_deleted=False
		).exists():
			tuition_request = TuitionRequest.objects.select_related(
				'parent', 'tutor', 'tuition_area'
			).get(
				uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
				is_rejected_by_ops=False, status='hot-job'
			)
		else:
			return Response({
				'detail': 'Tuition request not found, or not verified.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Checking if the tutor has jobs left, and updating the counts
		jobs_left = tutor.get_jobs_left()
		current_date = jobs_left['current_date']
		current_month = jobs_left['current_month']

		if jobs_left['daily_hot_jobs_left'] < 1:
			return Response({
				'detail': 'Daily hot jobs limit reached.'
			}, status=status.HTTP_402_PAYMENT_REQUIRED)

		if jobs_left['monthly_hot_jobs_left'] < 1:
			return Response({
				'detail': 'Monthly hot jobs limit reached.'
			}, status=status.HTTP_402_PAYMENT_REQUIRED)
		
		if current_date in tutor.daily_hot_jobs_applied:
			tutor.daily_hot_jobs_applied[current_date] += 1
		else:
			tutor.daily_hot_jobs_applied[current_date] = 1

		if current_month in tutor.monthly_hot_jobs_applied:
			tutor.monthly_hot_jobs_applied[current_month] += 1
		else:
			tutor.monthly_hot_jobs_applied[current_month] = 1


		# Updating the status of the tuition request
		tuition_request.status = 'in-process'

		# Creating the notifications and saving the objects using a transaction
		with transaction.atomic():
			tutor.save()
			tuition_request.save()

			# Notification for parent
			Notification.objects.create(
				notification_type='hot-job-apply',
				parent=tuition_request.parent,
				created_for='parent',
				title='A tutor applied to your job post',
				body=str(
					'A tutor has applied to a job post you made. Please '
					'expect a call from them before finalizing the details '
					'and confirming the job.'
				),
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=True
			)

			# Notification for tutor
			Notification.objects.create(
				notification_type='hot-job-apply',
				tutor=tuition_request.tutor,
				created_for='tutor',
				title='Successfully applied to hot job',
				body=str(
					'You have applied to the hot job. Please call the parent '
					'to finalize and confirm the job.'
				),
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=False
			)

			return Response({
				'detail': 'Successfully applied to the hot job.',
				'user_obj': TutorDetailsSerializer(tutor).data,
				'tuition_request': 
				TuitionRequestSerializer(tuition_request).data
			})


class TutorRejectTuitionRequest(APIView):
	permission_classes = (UserPermission,)

	def post(self, request, tuition_request_uuid, format=None):
		tutor = self.user

		# Getting the tuition request if it exists, 404 otherwise
		if TuitionRequest.objects.filter(
			uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
			is_rejected_by_tutor=False, is_rejected_by_ops=False,
			parent__is_verified_by_ops=True, 
			parent__is_suspended_by_ops=False, parent__is_deleted=False
		).exists():
			tuition_request = TuitionRequest.objects.get(
				uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
				is_rejected_by_tutor=False, is_rejected_by_ops=False
			)
		else:
			return Response({
				'detail': 'Tuition request not found, or not verified.'
			}, status=status.HTTP_404_NOT_FOUND)

		tuition_request.is_rejected_by_tutor = True
		tuition_request.save()

		return Response({
			'detail': 'The tuition request has been rejected.'
		})


class TutorConfirmTuitionRequest(APIView):
	permission_classes = (UserPermission,)

	def post(self, request, tuition_request_uuid, format=None):
		tutor = self.user

		# Getting the tuition request if it exists, 404 otherwise
		if TuitionRequest.objects.filter(
			uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
			is_rejected_by_tutor=False, is_rejected_by_ops=False,
			parent__is_verified_by_ops=True, 
			parent__is_suspended_by_ops=False, parent__is_deleted=False,
			status__in=['in-process', 'waiting-for-tutor']
		).exists():
			tuition_request = TuitionRequest.objects.get(
				uuid=uuid.UUID(tuition_request_uuid), tutor=tutor, 
				is_rejected_by_tutor=False, is_rejected_by_ops=False,
				status__in=['in-process', 'waiting-for-tutor']
			)
		else:
			return Response({
				'detail': 'Tuition request not found, or not verified.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Parent RFT save check
		save_parent_rft = False

		# Generating the status specific data
		if tuition_request.status == 'in-process':
			tuition_request.status = 'waiting-for-parent'

			# Parent notification
			parent_notification_title = str(
				'A tutor is waiting for you to confirm a job'
			)
			parent_notification_body = str(
				'A tutor is waiting for you to confirm a job you posted. '
				'Please confirm if you have talked over the phone and '
				'finalized everything.'
			)

			# Tutor notification
			tutor_notification_title = 'Waiting for parent'
			tutor_notification_body = str(
				'You have confirmed the job from your side. Please wait for '
				'the parent to confirm the job from their side.'
			)

		elif tuition_request.status == 'waiting-for-tutor':
			tuition_request.status = 'confirmed'
			tuition_request.confirmation_date = arrow.utcnow().datetime

			# Parent notification
			parent_notification_title = 'Job confirmed'
			parent_notification_body = 'Job has been confirmed successfully.'

			# Tutor notification
			tutor_notification_title = parent_notification_title
			tutor_notification_body = parent_notification_body

			# Update the parent RFT save check
			if tuition_request.parent_rft:
				if not tuition_request.parent_rft.is_confirmed:
					tuition_request.parent_rft.is_confirmed = True
					tuition_request.parent_rft.confirmation_date = arrow.utcnow().datetime
					save_parent_rft = True

		# Creating the notifications and saving the object using a transaction
		with transaction.atomic():
			tuition_request.save()

			# Notification for parent
			Notification.objects.create(
				notification_type=tuition_request.status,
				parent=tuition_request.parent,
				created_for='parent',
				title=parent_notification_title,
				body=parent_notification_body,
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=True
			)

			# Notification for tutor
			Notification.objects.create(
				notification_type=tuition_request.status,
				tutor=tuition_request.tutor,
				created_for='tutor',
				title=tutor_notification_title,
				body=tutor_notification_body,
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=False
			)

			# Update the parent RFT, depending on save check
			if save_parent_rft:
				tuition_request.parent_rft.save()

			# Returning the response
			return Response({
				'detail': 'Success',
				'tuition_request': 
				TuitionRequestSerializer(tuition_request).data
			})


class ParentConfirmTuitionRequest(APIView):
	permission_classes = (UserPermission,)

	def is_ops_view(self):
		return False

	def get_serializer_class(self):
		return TuitionRequestSerializer

	def post(self, request, tuition_request_uuid, format=None):
		# Get the parent depending on type of view
		if not self.is_ops_view():
			parent = self.user
		else:
			# Get the parent uuid
			if not 'parent_uuid' in request.data:
				return Response({
					'parent_uuid': ['This field is required']
				}, status=status.HTTP_400_BAD_REQUEST)
			else:
				parent_uuid = request.data['parent_uuid']

			# Get parent
			if Parent.objects.filter(
					uuid=uuid.UUID(parent_uuid),
					is_phone_number_verified=True,
					is_verified_by_ops=True,
					is_suspended_by_ops=False,
					is_deleted=False
				).exists():
				parent = Parent.objects.get(
					uuid=uuid.UUID(parent_uuid),
					is_phone_number_verified=True,
					is_verified_by_ops=True,
					is_suspended_by_ops=False,
					is_deleted=False
				)
			else:
				return Response({
					'detail': str(
						'Parent not found, or one of following: phone number '
						'not verified, parent not verified by ops, parent '
						'suspended by ops, and/or parent deleted.'
					)
				}, status=status.HTTP_404_NOT_FOUND)

		# Getting the tuition request if it exists, 404 otherwise
		if TuitionRequest.objects.filter(
			uuid=uuid.UUID(tuition_request_uuid), parent=parent, 
			is_rejected_by_tutor=False, is_rejected_by_ops=False,
			parent__is_verified_by_ops=True, 
			parent__is_suspended_by_ops=False, parent__is_deleted=False,
			status__in=['in-process', 'waiting-for-parent']
		).exists():
			tuition_request = TuitionRequest.objects.get(
				uuid=uuid.UUID(tuition_request_uuid), parent=parent, 
				is_rejected_by_tutor=False, is_rejected_by_ops=False,
				status__in=['in-process', 'waiting-for-parent']
			)
		else:
			return Response({
				'detail': 'Tuition request not found, or not verified.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Parent RFT save check
		save_parent_rft = False

		# Generating the status specific data
		if tuition_request.status == 'in-process':
			tuition_request.status = 'waiting-for-tutor'

			# Parent notification
			parent_notification_title = str(
				'Waiting for tutor'
			)
			parent_notification_body = str(
				'You have confirmed the job from your side. Please wait for '
				'the tutor to confirm the job from their side.'
			)

			# Tutor notification
			tutor_notification_title = str(
				'A parent is waiting for you to confirm a job'
			)
			tutor_notification_body = str(
				'A parent is waiting for you to confirm a job you accepted or '
				'applied to. Please confirm if you have talked over the phone '
				'and finalized everything.'
			)

		elif tuition_request.status == 'waiting-for-parent':
			tuition_request.status = 'confirmed'
			tuition_request.confirmation_date = arrow.utcnow().datetime

			# Parent notification
			parent_notification_title = 'Job confirmed'
			parent_notification_body = 'Job has been confirmed successfully.'

			# Tutor notification
			tutor_notification_title = parent_notification_title
			tutor_notification_body = parent_notification_body

			# Update the parent RFT save check
			if tuition_request.parent_rft:
				if not tuition_request.parent_rft.is_confirmed:
					tuition_request.parent_rft.is_confirmed = True
					tuition_request.parent_rft.confirmation_date = arrow.utcnow().datetime
					save_parent_rft = True

		# Creating the notifications and saving the object using a transaction
		with transaction.atomic():
			# Update the ops note for ops view
			if self.is_ops_view():
				tuition_request.ops_notes['notes'].append(
					generate_ops_note(
						self.account.user,
						str(f'Status changed to {tuition_request.status} by '
							f'ops user.')
					)
				)
			tuition_request.save()

			# Notification for parent
			Notification.objects.create(
				notification_type=tuition_request.status,
				parent=tuition_request.parent,
				created_for='parent',
				title=parent_notification_title,
				body=parent_notification_body,
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=False
			)

			# Notification for tutor
			Notification.objects.create(
				notification_type=tuition_request.status,
				tutor=tuition_request.tutor,
				created_for='tutor',
				title=tutor_notification_title,
				body=tutor_notification_body,
				url=str(
					f'https://app.yoda.com/job-details/{tuition_request.uuid}/'
				),
				create_extra_notifications=True
			)

			# Update the parent RFT, depending on save check
			if save_parent_rft:
				tuition_request.parent_rft.save()

			# Returning the response
			return Response({
				'detail': 'Success',
				'tuition_request': 
				self.get_serializer_class()(tuition_request).data
			})


# Notification views

class NotificationList(APIView, PageNumberPagination):
	page_size = 20
	max_page_size = 20
	permission_classes = (UserPermission,)

	def get_notifications(self, obj):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get(self, request, format=None):
		obj = self.user

		# Getting notifications 
		notifications = self.get_notifications(obj)

		# Creating and returning the paginated serializer data
		paginated_serializer = NotificationSerializer(
			self.paginate_queryset(notifications, self.request), many=True
		)
		return self.get_paginated_response(paginated_serializer.data)


class ParentNotificationList(NotificationList):
	def get_notifications(self, obj):
		return Notification.objects.filter(parent=obj)


class StudentNotificationList(NotificationList):
	def get_notifications(self, obj):
		return Notification.objects.filter(student=obj)


class TutorNotificationList(NotificationList):
	def get_notifications(self, obj):
		return Notification.objects.filter(tutor=obj)


# Transaction views

class TransactionList(APIView, PageNumberPagination):
	page_size = 20
	max_page_size = 20
	permission_classes = (UserPermission,)

	def get_transactions(self, obj):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get(self, request, format=None):
		obj = self.user

		# Getting transactions
		transactions = self.get_transactions(obj)

		# Creating and returning the paginated serializer data
		paginated_serializer = TransactionSerializer(
			self.paginate_queryset(transactions, self.request), many=True
		)
		return self.get_paginated_response(paginated_serializer.data)


class ParentTransactionList(TransactionList):
	def get_transactions(self, obj):
		return Transaction.objects.filter(parent=obj)


class StudentTransactionList(TransactionList):
	def get_transactions(self, obj):
		return Transaction.objects.filter(student=obj)


class TutorTransactionList(TransactionList):
	def get_transactions(self, obj):
		return Transaction.objects.filter(tutor=obj)


# Ops related views

class OpsLogin(APIView):
	permission_classes = (CorrectAPIKeyPermission,)

	def post(self, request, format=None):
		# Username not given
		if not 'username' in request.data:
			return Response({
				'username': ['This field is required.']
			}, status=status.HTTP_400_BAD_REQUEST)

		# Password not given
		if not 'password' in request.data:
			return Response({
				'password': ['This field is required.']
			}, status=status.HTTP_400_BAD_REQUEST)

		# Find the user, and 404 otherwise
		if User.objects.filter(username=request.data['username']).exists():
			user = User.objects.get(username=request.data['username'])
		else:
			return Response({
				'detail': 'User not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Check the password and return result if match
		if not check_password(request.data['password'], user.password):
			return Response({
				'password': ['Incorrect password.']
			}, status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({
				'detail': 'Successful login.',
				'auth_obj': {
					'user_type': user.account.account_type,
					'auth_jwt': user.account.get_auth_jwt()
				},
				'user_obj': UserSerializer(user).data
			})


# Sign up views

class OpsUserSignUp(APIView):
	permission_classes = (OpsPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_user_type(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def update_extra(self, request):
		pass

	def post(self, request, format=None):
		# Check if country is given
		if not 'country' in request.data:
			return Response({
				'country': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if service available for the given country
		if not request.data['country'] in PHONE_NUMBER_VALIDATOR_COUNTRY_MAP:
			return Response({
				'country': 
				['Our service is not yet available in this country.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if phone number is given
		if not 'phone_number' in request.data:
			return Response({
				'phone_number': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Validate the phone number
		try:
			request.data['phone_number'] = PHONE_NUMBER_VALIDATOR_COUNTRY_MAP[
				request.data['country']
			](request.data['phone_number'])
		except Exception as e:
			return Response(
				{'phone_number': e},
				status=status.HTTP_400_BAD_REQUEST
			)

		# Make sure no other user with the same phone number exists
		if self.get_model_class().objects.filter(
			phone_number=request.data['phone_number']).exists():
			return Response({
				'phone_number': [str(
					'Another user with this phone number already exists. '
					'Please update the existing user.'
				)]
			}, status=status.HTTP_400_BAD_REQUEST)

		# Handle the serializer
		serializer = self.get_serializer_class()(data=request.data)
		self.update_extra(request)
		if serializer.is_valid():
			# Add the signed up by account
			serializer.validated_data['signed_up_by'] = self.account
			# Add the signed up by account as a note
			serializer.validated_data['ops_notes'] = get_default_ops_notes()
			serializer.validated_data['ops_notes']['notes'].append(
				generate_ops_note(self.account.user, 'Sign up by ops user.')
			)
			# Save the serializer and return the data
			serializer.save()
			return Response({
				'detail': 'Sign up successful.',
				'user_uuid': serializer.data['uuid'],
				'user_type': self.get_user_type()
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OpsParentSignUp(OpsUserSignUp):
	def get_model_class(self):
		return Parent

	def get_serializer_class(self):
		return OpsParentSignUpSerializer

	def get_user_type(self):
		return 'parent'


class OpsStudentSignUp(OpsUserSignUp):
	def get_model_class(self):
		return Student

	def get_serializer_class(self):
		return OpsStudentSignUpSerializer

	def get_user_type(self):
		return 'student'


class ActivationTutorSignUp(OpsUserSignUp):
	permission_classes = (ActivationManagerPermission,)

	def get_model_class(self):
		return Tutor

	def get_serializer_class(self):
		return OpsTutorSignUpSerializer

	def get_user_type(self):
		return 'tutor'

	def update_extra(self, request):
		request.data['sign_up_channel'] = 'activation'


class CampusAmbassadorTutorSignUp(OpsUserSignUp):
	permission_classes = (CampusAmbassadorPermission,)

	def get_model_class(self):
		return Tutor

	def get_serializer_class(self):
		return OpsTutorSignUpSerializer

	def get_user_type(self):
		return 'tutor'

	def update_extra(self, request):
		request.data['sign_up_channel'] = 'campus-ambassador'
		request.data['undergraduate_university'] = self.account.university.id


# List views

class OpsUserList(APIView, PageNumberPagination):
	page_size = 30
	max_page_size = 30
	permission_classes = (OpsPermission,)

	def get_users(self, country):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get(self, request, country, format=None):
		# Getting users
		users = self.get_users(country)

		# Creating and returning the paginated serializer data
		paginated_serializer = self.get_serializer_class()(
			self.paginate_queryset(users, self.request), many=True
		)
		return self.get_paginated_response(paginated_serializer.data)


class OpsParentList(OpsUserList):
	def get_users(self, country):
		return Parent.objects.filter(country=Country(country))

	def get_serializer_class(self):
		return OpsParentSerializer


class OpsStudentList(OpsUserList):
	def get_users(self, country):
		return Student.objects.filter(country=Country(country))

	def get_serializer_class(self):
		return OpsStudentSerializer


class OpsTutorList(OpsUserList):
	def get_users(self, country):
		return Tutor.objects.select_related(
			'undergraduate_university_academic_bg', 'school_academic_bg',
			'college_academic_bg'
		).filter(country=Country(country))

	def get_serializer_class(self):
		return OpsTutorListSerializer


# Details views

class OpsUserDetails(APIView):
	permission_classes = (OpsPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_user(self, user_uuid):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class_for_get(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class_for_post(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get(self, request, user_uuid, format=None):
		# Check if the user exists and get it
		if self.get_model_class().objects.filter(uuid=uuid.UUID(user_uuid)):
			user = self.get_user(user_uuid)
		else:
			return Response({
				'detail': 'User not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Handle the serializer
		serializer = self.get_serializer_class_for_get()(user)
		return Response({
			'user_obj': serializer.data,
			'user_type': user.__class__.__name__.lower(),
		})

	def post(self, request, user_uuid, format=None):
		# Check if the user exists and get it
		if self.get_model_class().objects.filter(uuid=uuid.UUID(user_uuid)):
			user = self.get_user(user_uuid)
		else:
			return Response({
				'detail': 'User not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Check if country is given
		if not 'country' in request.data:
			return Response({
				'country': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if service available for the given country
		if not request.data['country'] in PHONE_NUMBER_VALIDATOR_COUNTRY_MAP:
			return Response({
				'country': 
				['Our service is not yet available in this country.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if phone number is given
		if not 'phone_number' in request.data:
			return Response({
				'phone_number': ['This field is required.'] 
			}, status=status.HTTP_400_BAD_REQUEST)

		# Validate the phone number
		try:
			request.data['phone_number'] = PHONE_NUMBER_VALIDATOR_COUNTRY_MAP[
				request.data['country']
			](request.data['phone_number'])
		except Exception as e:
			return Response(
				{'phone_number': e},
				status=status.HTTP_400_BAD_REQUEST
			)

		# Make sure no other user with the same phone number exists
		if self.get_model_class().objects.filter(
				phone_number=request.data['phone_number']
			).exclude(uuid=uuid.UUID(user_uuid)).exists():
			return Response({
				'phone_number': [str(
					'Another user with this phone number already exists. '
					'Please update the existing user.'
				)]
			}, status=status.HTTP_400_BAD_REQUEST)

		# Handle the serializer
		serializer = self.get_serializer_class_for_post()(
			user, data=request.data, partial=True
		)
		if serializer.is_valid():
			serializer.save()
			return Response({
				'detail': 'User updated successfully.',
				'user_obj': self.get_serializer_class_for_get()(user).data,
				'user_type': user.__class__.__name__.lower(),
			})
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OpsParentDetails(OpsUserDetails):
	def get_model_class(self):
		return Parent

	def get_user(self, user_uuid):
		return Parent.objects.get(uuid=uuid.UUID(user_uuid))

	def get_serializer_class_for_get(self):
		return OpsParentSerializer

	def get_serializer_class_for_post(self):
		return OpsParentSerializer


class OpsStudentDetails(OpsUserDetails):
	def get_model_class(self):
		return Student

	def get_user(self, user_uuid):
		return Student.objects.get(uuid=uuid.UUID(user_uuid))

	def get_serializer_class_for_get(self):
		return OpsStudentSerializer

	def get_serializer_class_for_post(self):
		return OpsStudentSerializer


class OpsTutorDetails(OpsUserDetails):
	def get_model_class(self):
		return Tutor

	def get_user(self, user_uuid):
		return Tutor.objects.select_related(
			'undergraduate_university_academic_bg', 'school_academic_bg',
			'college_academic_bg'
		).get(uuid=uuid.UUID(user_uuid))

	def get_serializer_class_for_get(self):
		return OpsTutorDetailsGetSerializer

	def get_serializer_class_for_post(self):
		return OpsTutorDetailsPostSerializer


# Filter views

class OpsUserFilter(APIView, PageNumberPagination):
	page_size = 30
	max_page_size = 30
	permission_classes = (OpsPermission,)

	def get_users(self, filters):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class_for_filter(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class_for_get(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_user_type(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, country, get_all=None, format=None):
		# Init serializer
		filter_serializer = self.get_serializer_class_for_filter()(
			data=request.data, partial=True
		)

		if filter_serializer.is_valid():
			filters = models.Q()

			# Add the country filter (required from URL)
			filters &= models.Q(
				country=Country(country),
			)

			# Add the other filters
			if request.data.get('full_name', ''):
				filters &= models.Q(
					full_name__contains=request.data['full_name'],
				)

			if request.data.get('phone_number', ''):
				filters &= models.Q(
					phone_number=request.data['phone_number'],
				)

			if 'is_phone_number_verified' in request.data:
				filters &= models.Q(
					is_phone_number_verified=
					request.data['is_phone_number_verified'],
				)

			if request.data.get('gender', ''):
				filters &= models.Q(
					gender=request.data['gender'],
				)

			if 'is_social_media_connected' in request.data:
				filters &= models.Q(
					is_social_media_connected=
					request.data['is_social_media_connected'],
				)

			if 'is_verified_by_ops' in request.data:
				filters &= models.Q(
					is_verified_by_ops=request.data['is_verified_by_ops'],
				)

			if 'is_suspended_by_ops' in request.data:
				filters &= models.Q(
					is_suspended_by_ops=request.data['is_suspended_by_ops'],
				)

			if 'is_deleted' in request.data:
				filters &= models.Q(
					is_deleted=request.data['is_deleted'],
				)

			if request.data.get('sign_up_date', None):
				filters &= models.Q(
					sign_up_date__gte=request.data['sign_up_date'],
				)

			if request.data.get('last_active_at', None):
				filters &= models.Q(
					last_active_at__gte=request.data['last_active_at'],
				)

			if self.get_user_type() == 'tutor':
				# Add extra filters for tutor
				if request.data.get('academic_medium', ''):
					filters &= models.Q(
						academic_medium=request.data['academic_medium'],
					)

				if 'undergraduate_university' in request.data:
					if isinstance(
						request.data['undergraduate_university'], int):
						filters &= models.Q(
							undergraduate_university=
							request.data['undergraduate_university'],
						)

				if request.data.get('salary_range_start', ''):
					filters &= models.Q(
						salary_range_start__gte=
						request.data['salary_range_start'],
					)

				if request.data.get('salary_range_end', ''):
					filters &= models.Q(
						salary_range_end__lte=request.data['salary_range_end'],
					)

				if request.data.get('offline_preferred_teaching_areas', []):
					filters &= models.Q(
						offline_preferred_teaching_areas__in=
						request.data['offline_preferred_teaching_areas'],
					)
					
				if request.data.get('offline_preferred_teaching_subjects', []):
					filters &= models.Q(
						offline_preferred_teaching_subjects__in=
						request.data['offline_preferred_teaching_subjects'],
					)

				if 'is_personal_information_complete' in request.data:
					filters &= models.Q(
						is_personal_information_complete=
						request.data['is_personal_information_complete'],
					)

				if 'is_teaching_preferences_complete' in request.data:
					filters &= models.Q(
						is_teaching_preferences_complete=
						request.data['is_teaching_preferences_complete'],
					)

				if request.data.get('account_type', ''):
					filters &= models.Q(
						account_type=request.data['account_type'],
					)

				if request.data.get('date_till_premium_account_valid', None):
					filters &= models.Q(
						date_till_premium_account_valid__gte=
						request.data['date_till_premium_account_valid'],
					)

				if request.data.get('is_academic_background_complete', None):
					filters &= models.Q(
						undergraduate_university_academic_bg__is_complete=
						True,
						school_academic_bg__is_complete=True,
						college_academic_bg__is_complete=True,
					)

			# Getting the users
			users = self.get_users(filters)

			if not get_all:
				# Init paginated serializer and return
				paginated_serializer = self.get_serializer_class_for_get()(
					self.paginate_queryset(users, self.request), many=True
				)
				return self.get_paginated_response(paginated_serializer.data)
			else:
				# Get all
				return Response({
					'count': len(users),
    				'next': None,
   			 		'previous': None,
					'results': self.get_serializer_class_for_get()(
						users, many=True
					).data
				})

		return Response(
			filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST
		)


class OpsParentFilter(OpsUserFilter):
	def get_users(self, filters):
		return Parent.objects.filter(filters).distinct()

	def get_serializer_class_for_filter(self):
		return OpsParentFilterSerializer

	def get_serializer_class_for_get(self):
		return OpsParentSerializer

	def get_user_type(self):
		return 'parent'


class OpsStudentFilter(OpsUserFilter):
	def get_users(self, filters):
		return Student.objects.filter(filters).distinct()

	def get_serializer_class_for_filter(self):
		return OpsStudentFilterSerializer

	def get_serializer_class_for_get(self):
		return OpsStudentSerializer

	def get_user_type(self):
		return 'student'


class OpsTutorFilter(OpsUserFilter):
	def get_users(self, filters):
		return Tutor.objects.select_related(
			'undergraduate_university_academic_bg', 'school_academic_bg',
			'college_academic_bg'
		).filter(filters).distinct()

	def get_serializer_class_for_filter(self):
		return OpsTutorFilterSerializer

	def get_serializer_class_for_get(self):
		return OpsTutorListSerializer

	def get_user_type(self):
		return 'tutor'


# Verification views

class OpsChangeUserVerification(APIView):
	permission_classes = (OpsPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_user(self, user_uuid):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def save_user(self, user):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, user_uuid, new_ops_verification_status, 
		format=None):
		# Check and get if the user exists
		if self.get_model_class().objects.filter(
			uuid=uuid.UUID(user_uuid)).exists():
			user = self.get_user(user_uuid)
		else:
			return Response({
				'detail': 'User not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Check if redundant
		if user.is_verified_by_ops and new_ops_verification_status == 'verify':
			return Response({
				'detail': 'Already up-to date.'
			}, status=status.HTTP_400_BAD_REQUEST)

		elif (not user.is_verified_by_ops and 
			new_ops_verification_status == 'unverify'):
			return Response({
				'detail': 'Already up-to date.'
			}, status=status.HTTP_400_BAD_REQUEST)

		# Update the verification status
		if new_ops_verification_status == 'verify':
			user.is_verified_by_ops = True
		elif new_ops_verification_status == 'unverify':
			user.is_verified_by_ops = False

		# Update the ops notes
		if user.is_verified_by_ops:
			user.ops_notes['notes'].append(
				generate_ops_note(self.account.user, 'Verified by ops user.')
			)
		else:
			user.ops_notes['notes'].append(
				generate_ops_note(self.account.user, 'Unverified by ops user.')
			)

		# Save the object by calling the class method
		self.save_user(user)

		return Response({
			'detail': 'Successfully updated verification status.',
			'user_obj': self.get_serializer_class()(user).data
		})


class OpsChangeParentVerification(OpsChangeUserVerification):
	def get_model_class(self):
		return Parent

	def get_user(self, user_uuid):
		return Parent.objects.get(uuid=uuid.UUID(user_uuid))

	def save_user(self, user):
		if user.is_verified_by_ops:
			with transaction.atomic():
				# Get the direct requests where notifications were not created
				tuition_requests = TuitionRequest.objects.select_related(
					'tutor'
				).filter(
					parent=user,
					status='direct-request',
					notification_created=False
				)

				# Update the tuition requests and create notifications
				for tuition_request in tuition_requests:
					Notification.objects.create(
						notification_type='direct-request-create',
						tutor=tuition_request.tutor,
						created_for='tutor',
						title='New direct request',
						body=str(
							'A parent has directly requested you to be the '
							'potential tutor for their children!'
						),
						url=str(
							f'https://app.yoda.com/job-details'
							f'/{tuition_request.uuid}/'
						),
						create_extra_notifications=True
					)
					tuition_request.notification_created = True
					tuition_request.save()

				# Save the object
				user.save()
		else:
			user.save()

	def get_serializer_class(self):
		return OpsParentSerializer


class OpsChangeStudentVerification(OpsChangeUserVerification):
	def get_model_class(self):
		return Student

	def get_user(self, user_uuid):
		return Student.objects.get(uuid=uuid.UUID(user_uuid))

	def save_user(self, user):
		user.save()

	def get_serializer_class(self):
		return OpsStudentSerializer


class OpsChangeTutorVerification(OpsChangeUserVerification):
	def get_model_class(self):
		return Tutor

	def get_user(self, user_uuid):
		return Tutor.objects.select_related(
			'undergraduate_university_academic_bg', 'school_academic_bg',
			'college_academic_bg'
		).get(uuid=uuid.UUID(user_uuid))

	def save_user(self, user):
		if user.is_verified_by_ops:
			with transaction.atomic():
				# Create the notification
				Notification.objects.create(
					notification_type='ops-verification',
					tutor=user,
					created_for='tutor',
					title='Profile verification successful',
					body=str(
						'Congratulations. Your profile has been successfully ' 
						'verified by Yoda!'
					),
					url=str(f'https://app.yoda.com/tutor-dashboard/'),
					create_extra_notifications=True
				)

				# Save the object
				user.save()
		else:
			user.save()

	def get_serializer_class(self):
		return OpsTutorDetailsGetSerializer


# Job views

class OpsRequestForTutorCreate(APIView):
	permission_classes = (OpsPermission,)

	def post(self, request, format=None):
		# Check if the parent's phone number is provided
		if not 'parent_phone_number' in request.data:
			return Response({
				'detail': 'The parent\'s phone number must be provided.'
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if the parent exists and meets all the checks
		if Parent.objects.filter(
				phone_number=request.data['parent_phone_number'],
				is_phone_number_verified=True,
				is_verified_by_ops=True,
				is_suspended_by_ops=False,
				is_deleted=False
			).exists():
			parent = Parent.objects.get(
				phone_number=request.data['parent_phone_number'],
				is_phone_number_verified=True,
				is_verified_by_ops=True,
				is_suspended_by_ops=False,
				is_deleted=False
			)
			request.data['parent'] = parent.id
		else:
			return Response({
				'detail': str(
					'Parent not found, or one of following: phone number not '
					'verified, parent not verified by ops, parent suspended '
					'by ops, and/or parent deleted.'
				)
			}, status=status.HTTP_404_NOT_FOUND)

		# Handle the serializer
		serializer = RequestForTutorCreateSerializer(data=request.data)
		if serializer.is_valid():
			# Add the ops notes
			serializer.validated_data['ops_notes'] = get_default_ops_notes()
			serializer.validated_data['ops_notes']['notes'].append(
				generate_ops_note(self.account.user, 'Created by ops user.')
			)
			# Save the serializer and return the data
			serializer.save()
			return Response({
				'detail': 'The RFT has been created.',
				'rft': serializer.data
			}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OpsJobDetails(APIView):
	permission_classes = (OpsPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_job(self, job_uuid):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_job_type(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get(self, request, job_uuid, format=None):
		# Check if the job exists and get it
		if self.get_model_class().objects.filter(uuid=uuid.UUID(job_uuid)):
			job = self.get_job(job_uuid)
		else:
			return Response({
				'detail': 'Not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Handle the serializer
		serializer = self.get_serializer_class()(job)
		return Response({
			self.get_job_type(): serializer.data
		})


class OpsRequestForTutorDetails(OpsJobDetails):
	def get_model_class(self):
		return RequestForTutor

	def get_job(self, job_uuid):
		return RequestForTutor.objects.select_related(
			'parent', 'tuition_area'
		).get(uuid=uuid.UUID(job_uuid))

	def get_serializer_class(self):
		return OpsRequestForTutorSerializer

	def get_job_type(self):
		return 'rft'


class OpsTuitionRequestDetails(OpsJobDetails):
	def get_model_class(self):
		return TuitionRequest

	def get_job(self, job_uuid):
		return TuitionRequest.objects.select_related(
			'parent', 'tuition_area', 'tutor'
		).get(uuid=uuid.UUID(job_uuid))

	def get_serializer_class(self):
		return OpsTuitionRequestSerializer

	def get_job_type(self):
		return 'tuition_request'


class OpsChangeJobRejection(APIView):
	permission_classes = (OpsPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_job(self, job_uuid):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_job_type(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, job_uuid, new_ops_rejection_status, format=None):
		# Check and get if the job exists
		if self.get_model_class().objects.filter(
			uuid=uuid.UUID(job_uuid)).exists():
			job = self.get_job(job_uuid)
		else:
			return Response({
				'detail': 'Not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Check if redundant
		if job.is_rejected_by_ops and new_ops_rejection_status == 'reject':
			return Response({
				'detail': 'Already up-to date.'
			}, status=status.HTTP_400_BAD_REQUEST)

		elif (not job.is_rejected_by_ops and 
			new_ops_rejection_status == 'unreject'):
			return Response({
				'detail': 'Already up-to date.'
			}, status=status.HTTP_400_BAD_REQUEST)

		# Update the rejection status
		if new_ops_rejection_status == 'reject':
			job.is_rejected_by_ops = True
		elif new_ops_rejection_status == 'unreject':
			job.is_rejected_by_ops = False

		# Update the ops notes
		if job.is_rejected_by_ops:
			job.ops_notes['notes'].append(
				generate_ops_note(self.account.user, 'Rejected by ops user.')
			)
		else:
			job.ops_notes['notes'].append(
				generate_ops_note(self.account.user, 'Unrejected by ops user.')
			)

		job.save()
		return Response({
			'detail': 'Successfully updated rejection status.',
			self.get_job_type(): self.get_serializer_class()(job).data
		})


class OpsChangeRequestForTutorRejection(OpsChangeJobRejection):
	def get_model_class(self):
		return RequestForTutor

	def get_job(self, job_uuid):
		return RequestForTutor.objects.select_related(
			'parent', 'tuition_area'
		).get(uuid=uuid.UUID(job_uuid))

	def get_serializer_class(self):
		return OpsRequestForTutorSerializer

	def get_job_type(self):
		return 'rft'


class OpsChangeTuitionRequestRejection(OpsChangeJobRejection):
	def get_model_class(self):
		return TuitionRequest

	def get_job(self, job_uuid):
		return TuitionRequest.objects.select_related(
			'parent', 'tuition_area', 'tutor'
		).get(uuid=uuid.UUID(job_uuid))

	def get_serializer_class(self):
		return OpsTuitionRequestSerializer

	def get_job_type(self):
		return 'tuition_request'


class OpsJobFilter(APIView, PageNumberPagination):
	page_size = 30
	max_page_size = 30
	permission_classes = (OpsPermission,)

	def get_jobs(self, filters):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class_for_filter(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class_for_get(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_job_type(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, country, get_all=None, format=None):
		# Init serializer
		filter_serializer = self.get_serializer_class_for_filter()(
			data=request.data, partial=True
		)

		if filter_serializer.is_valid():
			filters = models.Q()

			# Add the country filter (required from URL)
			filters &= models.Q(
				country=Country(country),
			)

			# Add the other filters
			if request.data.get('uuid', ''):
				filters &= models.Q(
					uuid=uuid.UUID(request.data['uuid']),
				)

			if request.data.get('created_at', None):
				filters &= models.Q(
					created_at__gte=request.data['created_at'],
				)

			if 'is_rejected_by_ops' in request.data:
				filters &= models.Q(
					is_rejected_by_ops=request.data['is_rejected_by_ops'],
				)

			if request.data.get('confirmation_date', None):
				filters &= models.Q(
					confirmation_date__gte=request.data['confirmation_date'],
				)

			if request.data.get('parent_phone_number', ''):
				filters &= models.Q(
					parent__phone_number=
					request.data['parent_phone_number'],
				)

			if 'parent_is_verified_by_ops' in request.data:
				filters &= models.Q(
					parent__is_verified_by_ops=
					request.data['parent_is_verified_by_ops'],
				)

			if self.get_job_type() == 'rft':
				# Add extra filters for RFT
				if 'is_confirmed' in request.data:
					filters &= models.Q(
						is_confirmed=request.data['is_confirmed'],
					)

			if self.get_job_type() == 'tuition_request':
				# Add extra filters for tuition requests
				if request.data.get('status', ''):
					filters &= models.Q(
						status=request.data['status'],
					)

				if 'is_rejected_by_tutor' in request.data:
					filters &= models.Q(
						is_rejected_by_tutor=
						request.data['is_rejected_by_tutor'],
					)

				if request.data.get('tutor_phone_number', ''):
					filters &= models.Q(
						tutor__phone_number=
						request.data['tutor_phone_number'],
					)

			# Getting the jobs
			jobs = self.get_jobs(filters)

			if not get_all:
				# Init paginated serializer and return
				paginated_serializer = self.get_serializer_class_for_get()(
					self.paginate_queryset(jobs, self.request), many=True
				)
				return self.get_paginated_response(paginated_serializer.data)
			else:
				# Get all
				return Response({
					'count': len(jobs),
    				'next': None,
   			 		'previous': None,
					'results': self.get_serializer_class_for_get()(
						jobs, many=True
					).data
				})

		return Response(
			filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST
		)


class OpsRequestForTutorFilter(OpsJobFilter):
	def get_jobs(self, filters):
		return RequestForTutor.objects.select_related(
			'parent', 'tuition_area'
		).filter(filters).distinct()

	def get_serializer_class_for_filter(self):
		return OpsRequestForTutorFilterSerializer

	def get_serializer_class_for_get(self):
		return OpsRequestForTutorSerializer

	def get_job_type(self):
		return 'rft'


class OpsTuitionRequestFilter(OpsJobFilter):
	def get_jobs(self, filters):
		return TuitionRequest.objects.select_related(
			'parent', 'tuition_area', 'tutor'
		).filter(filters).distinct()

	def get_serializer_class_for_filter(self):
		return OpsTuitionRequestFilterSerializer

	def get_serializer_class_for_get(self):
		return OpsTuitionRequestSerializer

	def get_job_type(self):
		return 'tuition_request'


class OpsRftToHotJob(APIView):
	permission_classes = (OpsPermission,)

	def post(self, request, rft_uuid, format=None):
		# Get RFT
		if RequestForTutor.objects.filter(
				uuid=uuid.UUID(rft_uuid),
				is_rejected_by_ops=False
			).exists():
			rft = RequestForTutor.objects.get(
				uuid=uuid.UUID(rft_uuid),
				is_rejected_by_ops=False
			)
		else:
			return Response({
				'detail': 'RFT not found, or is rejected by ops.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Get tutor uuid
		if not 'tutor_uuid' in request.data:
			return Response({
				'tutor_uuid': ['This field is required']
			}, status=status.HTTP_400_BAD_REQUEST)
		else:
			tutor_uuid = request.data['tutor_uuid']

		# Get tutor
		if Tutor.objects.filter(
				uuid=uuid.UUID(tutor_uuid),
				is_phone_number_verified=True,
				is_verified_by_ops=True,
				is_suspended_by_ops=False,
				is_deleted=False
			).exists():
			tutor = Tutor.objects.get(
				uuid=uuid.UUID(tutor_uuid),
				is_phone_number_verified=True,
				is_verified_by_ops=True,
				is_suspended_by_ops=False,
				is_deleted=False
			)
		else:
			return Response({
				'detail': str(
					'Tutor not found, or one of following: phone number not '
					'verified, tutor not verified by ops, tutor suspended '
					'by ops, and/or tutor deleted.'
				)
			}, status=status.HTTP_404_NOT_FOUND)

		# Check if the tutor has received the same RFT as a hot job before
		if TuitionRequest.objects.filter(tutor=tutor, parent_rft=rft).exists():
			return Response({
				'detail': str(
					'This tutor has already received this RFT as a hot job.'
				)
			}, status=status.HTTP_400_BAD_REQUEST)

		# Update the tutor
		tutor.last_hot_job_received_at = arrow.utcnow().datetime

		# Save the tutor, and create the job and notification
		with transaction.atomic():
			# Save the tutor
			tutor.save()

			# Create the job
			hot_job = TuitionRequest(
				status='hot-job',
				parent=rft.parent,
				tutor=tutor,
				note_by_parent=rft.note_by_parent,
				student_gender=rft.student_gender,
				student_school=rft.student_school,
				student_class=rft.student_class,
				student_medium=rft.student_medium,
				student_bangla_medium_version=
				rft.student_bangla_medium_version,
				student_english_medium_curriculum=
				rft.student_english_medium_curriculum,
				tuition_area=rft.tuition_area,
				teaching_place_preference=rft.teaching_place_preference,
				number_of_days_per_week=rft.number_of_days_per_week,
				salary=rft.salary,
				is_salary_negotiable=rft.is_salary_negotiable,
				parent_rft=rft,
				notification_created=True
			)
			hot_job.ops_notes['notes'].append(
				generate_ops_note(self.account.user, 'Created by ops user.')
			)
			hot_job.save()
			for subject in rft.subjects.all():
				hot_job.subjects.add(subject)

			# Create the notification
			Notification.objects.create(
				notification_type='new-hot-job',
				tutor=tutor,
				created_for='tutor',
				title='New hot job',
				body='You have a new job you can apply to.',
				url=str(
					f'https://app.yoda.com/job-details/{hot_job.uuid}/'
				),
				create_extra_notifications=True
			)

			return Response({
				'detail': 'Hot job created.',
				'tuition_request': OpsTuitionRequestSerializer(hot_job).data
			}, status=status.HTTP_201_CREATED)


class OpsParentConfirmTuitionRequest(ParentConfirmTuitionRequest):
	permission_classes = (OpsPermission,)

	def is_ops_view(self):
		return True

	def get_serializer_class(self):
		return OpsTuitionRequestSerializer


# Add ops note view

class AddOpsNote(APIView):
	permission_classes = (OpsPermission,)

	def get_model_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_obj(self, obj_uuid):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_serializer_class(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def get_response_key(self):
		raise NotImplementedError(
			'Please implement this method in the sub-class.'
		)

	def post(self, request, obj_uuid, format=None):
		# Get object or 404
		if self.get_model_class().objects.filter(
			uuid=uuid.UUID(obj_uuid)).exists():
			obj = self.get_obj(obj_uuid)
		else:
			return Response({
				'detail': 'Object not found.'
			}, status=status.HTTP_404_NOT_FOUND)

		# Check if note exists
		if not 'note' in request.data:
			return Response({
				'note': ['This field is required.']
			}, status=status.HTTP_400_BAD_REQUEST)

		# Check if note is a string
		if not isinstance(request.data['note'], string_types):
			return Response({
				'note': ['This field must be a string.']
			}, status=status.HTTP_400_BAD_REQUEST)

		# Add the ops note and save
		obj.ops_notes['notes'].append(
			generate_ops_note(self.account.user, request.data['note'])
		)
		obj.save()

		# Return the response
		return Response({
			'detail': 'Ops note added successfully.',
			self.get_response_key(): self.get_serializer_class()(obj).data
		})


class ParentAddOpsNote(AddOpsNote):
	def get_model_class(self):
		return Parent

	def get_obj(self, obj_uuid):
		return Parent.objects.get(uuid=uuid.UUID(obj_uuid))

	def get_serializer_class(self):
		return OpsParentSerializer

	def get_response_key(self):
		return 'parent'


class StudentAddOpsNote(AddOpsNote):
	def get_model_class(self):
		return Student

	def get_obj(self, obj_uuid):
		return Student.objects.get(uuid=uuid.UUID(obj_uuid))

	def get_serializer_class(self):
		return OpsStudentSerializer

	def get_response_key(self):
		return 'student'


class TutorAddOpsNote(AddOpsNote):
	def get_model_class(self):
		return Tutor

	def get_obj(self, obj_uuid):
		return Tutor.objects.select_related(
			'undergraduate_university_academic_bg', 'school_academic_bg',
			'college_academic_bg'
		).get(uuid=uuid.UUID(obj_uuid))

	def get_serializer_class(self):
		return OpsTutorDetailsGetSerializer

	def get_response_key(self):
		return 'tutor'


class RequestForTutorAddOpsNote(AddOpsNote):
	def get_model_class(self):
		return RequestForTutor

	def get_obj(self, obj_uuid):
		return RequestForTutor.objects.select_related(
			'parent', 'tuition_area'
		).get(uuid=uuid.UUID(obj_uuid))

	def get_serializer_class(self):
		return OpsRequestForTutorSerializer

	def get_response_key(self):
		return 'rft'


class TuitionRequestAddOpsNote(AddOpsNote):
	def get_model_class(self):
		return TuitionRequest

	def get_obj(self, obj_uuid):
		return TuitionRequest.objects.select_related(
			'parent', 'tuition_area', 'tutor'
		).get(uuid=uuid.UUID(obj_uuid))

	def get_serializer_class(self):
		return OpsTuitionRequestSerializer

	def get_response_key(self):
		return 'tuition_request'

