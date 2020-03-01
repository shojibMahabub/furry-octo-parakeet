import arrow
import json

from decimal import Decimal
from django.db import transaction

from .serializers import *
from .models import *
from django.core.validators import validate_email
from django.core.validators import URLValidator


'''
HOW TO RUN THIS FILE
	THE GREAT WAY IS TO UNCOMMENT SERIALLY ORGANIZED FUNCTION CALLS
	AND IMPORT * FROM SHELL_FUNCTIONS IN MANAGE.PY SHELL

	ANOTHER WAY IS TO CALL EACH FUNCTION SERIALLY ACCORDING TO
	DEFINITION ORDER IN MANAGE.PY SHELL
'''

def add_offline_subjects():
	'''
	SELECT * FROM yoda_main.subjects;
	'''
	# QUREY RETURNS 253 OFFLINE SUBJECTS. ALL UPFOR DATABASE

	input_file = 'tuitions/model_data/offline_subjects.json'

	with open(input_file, 'r') as f_in:
		response_data = json.load(f_in)

	for subject in response_data:
		sub = OfflineSubject(
			id=subject['id'],
			category=subject['category'],
			sub_category=subject['sub_category'],
			name=subject['name'],
			country=subject['country'],
			subject_type=subject['type']
		)
		sub.full_clean()
		sub.save()

def add_universities():
	'''
	SELECT * FROM yoda_main.institutions;
	'''
	# QUERY RETURNS 130 UNIVERSITIES. ALL UP FOR DATABASE

	input_file = 'tuitions/model_data/university.json'

	with open(input_file, 'r') as f_in:
		response_data = json.load(f_in)

	for university in response_data:
		if University.objects.filter(id=university['id']).exists():
			pass
		else:
			uni = University(
				id=university['id'],
				name=university['name'],
				grade=university['grade'],
				country=university['country']
			)
			
			uni.full_clean()
			uni.save()

def add_areas():
	'''
	SELECT * FROM yoda_main.locations;
	'''
	# QUERY RETURNS 86 AREAS. SOME ADDED LATER MANUALLY ON JSON FILE
	# IN TOTOAL 116 AREAS UP FOR DATABASE

	input_file = 'tuitions/model_data/116_area.json'

	with open(input_file, 'r') as f_in:
		response_data = json.load(f_in)

	for area in response_data:
		a = Area(
			id=area['id'],
			name=area['name'],
			city='Dhaka',
			zip_code=area['zip_code'],
			state='Dhaka',
			district='Dhaka',
			division='Dhaka',
			country='BD'
		)
		a.full_clean()
		a.save()

def add_university_fields_of_study():
	'''
	SELECT * FROM yoda_main.departments;
	'''
	# QUERY RETURNS 129 FIELD OF STUDIES.
	# ALL UP FOR DATABASE

	input_file = 'tuitions/model_data/unifofs.json'

	with open(input_file, 'r') as f_in:
		response_data = json.load(f_in)

	for each in response_data:
		major = UniversityFieldOfStudy(
			id=each['id'],
			name=each['name']
		)
		major.full_clean()
		major.save()

def add_schools():
	'''
	SELECT * FROM yoda_main.higher_institutes;
	'''
	# QUERY RETURNS 34979 HIGHER INSTITUTIONS
	# DUE TO REDUNDENCY AND QUERY OPTIMIZATION
	# DATA SHAPED TO 1620 SCHOOLS

	input_file = 'tuitions/model_data/school.json'

	with open(input_file, 'r') as f_in:
		response_data = json.load(f_in)

	for each in response_data:
		schl = School(
			id=each['id'],
			name=each['name'],
			country='BD'
		)

		schl.full_clean()
		schl.save()


def add_tutor():
	'''
	SELECT * FROM yoda_main.tutors;
	'''
	# QUERY RETRUNS 4353 TUTORS. ALL UP FOR DATABASE

	inputFile = "./tuitions/model_data/tutor.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()

	for each in data:
		try:
			u = University.objects.get(pk=each['undergraduate_university_fk'])
			if each['home_area']:
				h = Area.objects.get(pk=each['home_area'])
			t = Tutor(
				id = each['id'],
				sign_up_channel= "activation",
				full_name=each['name'],
				phone_number=each['phone'],
				undergraduate_university=u,
				is_verified_by_ops=each['is_verified'],
				old_slug = each['old_slug'],
				schedule=each['schedule'],
				home_area= h,
				number_of_public_profile_views = each['profile_view'],
			)
			if 'login_count' in each:
				if each['login_count'] > 0:
					t.is_phone_number_verified = True
			else:
				t.is_phone_number_verified = False
			t.save()

			if each['undergraduate_university_academic_bg']['identification_document_picture']:
				t.undergraduate_university_identification_document_picture = each['undergraduate_university_academic_bg']['identification_document_picture']
				t.save()

			if each['last_active_at']:
				t.last_active_at = arrow.get(each['last_active_at']).datetime
				t.save()

			if each['date_till_premium_account_is_valid']:
				t.date_till_premium_account_valid=arrow.get(each['date_till_premium_account_is_valid']).datetime
				t.save()

			if each['date_of_birth']:
				t.date_of_birth=arrow.get(each['date_of_birth']).datetime
				t.save()

			if each['gender']:
				t.gender=each['gender'].lower()
				t.save()
			
			if each['email']:
				try:
					t.email = each['email']
					validate_email(t.email)
				except Exception:
					t.email = 'placeholder@gmail.com'
					t.save()

			if each['about_me']:
				t.about = each['about_me']
				if len(t.about) < 150:
					difference = 150 - len(t.about)
					t.about = t.about + (' '*difference)
					t.save()

			if each['undergraduate_university_id_no']:
				t.undergraduate_university_id_number = each['undergraduate_university_id_no']
				t.save()

			if each['government_id_type']:
				t.government_id_type = each['government_id_type']
				t.save()

			if each['government_id_picture']:
				t.government_id_picture = each['government_id_picture']
				t.save()

			if each['government_id_number']:
				t.government_id_number = each['government_id_number']
				t.save()

			if each['created_at']:
				t.sign_up_date = arrow.get(each['created_at']).datetime
				t.save()

			if 'academic-medium' in each:
				if each['academic-medium']:
					t.academic_medium=each['academic-medium']
					t.save()

			if each['display_picture']:
				t.display_picture=each['display_picture']
				t.save()

			if each['salary_range_start']:
				t.salary_range_start=Decimal(each['salary_range_start'])
				t.save()

			if each['salary_range_end']:
				t.salary_range_end=Decimal(each['salary_range_end'])
				t.save()

			if each['is_flexible']:
				t.schedule_is_flexible=each['is_flexible']
				t.save()
			print('STEP 2 DONE FOR {}'.format(t.id))


			# UNIVERSITY
			if each['undergraduate_university_academic_bg']['name_of_institution']:
				t.undergraduate_university_academic_bg.name_of_institution=str(each['undergraduate_university_academic_bg']['name_of_institution'])

			if each['undergraduate_university_academic_bg']['name_of_degree']:
				t.undergraduate_university_academic_bg.name_of_degree=str(each['undergraduate_university_academic_bg']['name_of_degree'])

			if each['undergraduate_university_academic_bg']['identification_document_picture']:
				t.undergraduate_university_academic_bg.identification_document_picture=each['undergraduate_university_academic_bg']['identification_document_picture']

			if each['undergraduate_university_academic_bg']['start_year']:
				t.undergraduate_university_academic_bg.start_year=each['undergraduate_university_academic_bg']['start_year']

			if each['undergraduate_university_academic_bg']['end_year']:
				t.undergraduate_university_academic_bg.end_year=each['undergraduate_university_academic_bg']['end_year']

			t.undergraduate_university_academic_bg.save()

			# SCHOOL
			if each['school_academic_bg']['name_of_institution']:
				t.school_academic_bg.name_of_institution=str(each['school_academic_bg']['name_of_institution'])

			if each['school_academic_bg']['name_of_degree']:
				t.school_academic_bg.name_of_degree=str(each['school_academic_bg']['name_of_degree'])

			if each['school_academic_bg']['identification_document_picture']:
				t.school_academic_bg.identification_document_picture=each['school_academic_bg']['identification_document_picture']

			if each['school_academic_bg']['end_year']:
				t.school_academic_bg.end_year=each['school_academic_bg']['end_year']

			if each['school_academic_bg']['medium']:
				t.school_academic_bg.medium=each['school_academic_bg']['medium']

			t.school_academic_bg.save()

			# COLLEGE
			if each['college_academic_bg']['name_of_institution']:
				t.college_academic_bg.name_of_institution=str(each['college_academic_bg']['name_of_institution'])

			if each['college_academic_bg']['name_of_degree']:
				t.college_academic_bg.name_of_degree=str(each['college_academic_bg']['name_of_degree'])

			if each['college_academic_bg']['medium']:
				t.college_academic_bg.medium=each['college_academic_bg']['medium']

			if each['college_academic_bg']['identification_document_picture']:
				t.college_academic_bg.identification_document_picture=each['college_academic_bg']['identification_document_picture']

			if each['college_academic_bg']['end_year']:
				t.college_academic_bg.end_year=each['college_academic_bg']['end_year']

			t.college_academic_bg.save()
			print('STEP 3 DONE FOR {}'.format(t.id))


			# M2M fields
			if each['offline_preferred_teaching_areas']:
				for area in each['offline_preferred_teaching_areas']:
					try:
						t.offline_preferred_teaching_areas.add(area)
					except:
						pass
			if each['offline_preferred_teaching_subjects']:
				for sub in each['offline_preferred_teaching_subjects']:
					try:
						t.offline_preferred_teaching_subjects.add(sub)
					except:
						pass

			# M2M serialization
			t.m2m_fields_serialized['offline_preferred_teaching_areas'] = AreaSerializer(t.offline_preferred_teaching_areas.all(), many=True).data
			t.m2m_fields_serialized['offline_preferred_teaching_subjects'] = OfflineSubjectSerializer(t.offline_preferred_teaching_subjects.all(), many=True).data
			t.save()
			print('STEP 4 DONE FOR {}'.format(t.id))

			print(t.id, t.old_slug, sep="\t")
		except Exception as e:
			print(e)

		t.full_clean()
		t.save()


def add_parents():

	'''
	SELECT
		p.id, p.name, p.phone, p.email, p.gender,
		p.is_suspended, p.created_at, p.profile_img, u.mobile_confirmed,
        p.provider, p.user_id, u.last_login_at, u.login_count, 
        u.status, u.user_type
	FROM
		yoda_main.student_parents AS p, yoda_main.users AS u
	WHERE
		p.user_id=u.id
		and p.created_at >= '2020-02-01';
	'''
	# THIS QUERY RETURNS 1054 PARENTS WITH 1 DUPLICATE
	# 1053 UP FOR DATABASE

	inputFile = "./tuitions/model_data/parents.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()

	for each in data:
		p = Parent(
			id = each['id'],
			phone_number = '+880{}'.format(each['phone']),
			full_name=each['name'],
			is_phone_number_verified = each['is_phone_number_verified'],
			sign_up_date = arrow.get(each['created_at']).datetime,
			is_verified_by_ops = each['is_verified_by_ops'],
		)
		if not p.full_name:
			p.full_name = "Anonymous Parent"

		# if p.display_picture:
		try:
			v = URLValidator()
			v(each['profile_img'])
			p.display_picture = each['profile_img']
		except Exception:
			p.display_picture = ''

		if each['provider']:
			p.is_social_media_connected = True
		else:
			p.is_social_media_connected = False

		if each['email']:
			try:
				p.email=each['email']
				validate_email(p.email)
			except Exception:
				p.email = 'placeholder@gmail.com'

		if each['gender']:
			p.gender = each['gender'].lower()
			if p.gender == "1":
				p.gender = "female"

		if each['last_login_at']:
			p.last_active_at = arrow.get(each['last_login_at']).datetime

		print(p.id)
		print(p.display_picture)
		p.full_clean()

		p.save()
		print('{} saved'.format(p.full_name))


def add_request_for_tutors():
	'''
	SELECT 	*
	FROM
		yoda_main.tutor_jobs AS tj, yoda_main.student_parents as sp
	WHERE
		is_preference = 0
	AND
		tj.student_parent_id=sp.id;
	'''

	# FROM 661 TOTAL RFTs,
	# THIS QUERY RETURNS 653 RFTs BY APPLYING FILTER
	# IF PARENT EXISTS FOR THAT RFT

	# 610 UP FOR DATABASE


	inputFile = "./tuitions/model_data/610_jobs_confirmed.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if each['institution_preference']:
				for u in each['institution_preference']:
					## "institution_preferece": [4,5,6]
					uni = University.objects.get(pk=u)
					print(uni)
			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])

			rft = RequestForTutor(
				id = each['id'],
				tutor_gender = each['gender_preference'].lower(),
				tutor_undergraduate_university = uni,
				tutor_academic_medium = each['medium_preference'],
				is_confirmed = each['is_confirmed'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'].lower(),
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max'])
			)
			rft.save()

			if rft.student_medium == "1":
				rft.student_medium = "bangla-medium"
			
			if rft.student_medium == "2":
				rft.student_medium = "english-medium"

			if each['student_school']:
				rft.student_school = each['student_school']
			rft.save()

			if each['subjects']:
				for sub in each['subjects']:
					rft.subjects.add(sub)
			rft.save()

			print(rft.parent)
			print(rft.id)
	except Exception as e:
		print(e)
		pass


"""
HOT JOB
"""


def add_tuition_request_hot_job():
	"""
	SELECT 
		tr.id as tuition_request_id,
		tr.created_at,
		tr.updated_at,
		tr.student_parent_id as parent_id,
		tj.student_gender,
		tj.class as student_class,
		tj.medium as student_medium,
		tj.student_school,
		tj.subjects,
		tj.location_id as tuition_area,
		tj.teaching_preference as teaching_place_preference,
		tj.no_of_days as number_of_days_per_week,
		tj.salary_max as salary,
		tr.id as parent_rft,
		tr.tutor_id as tutor
		
	FROM 
		yoda_main.tutor_requests as tr,
		yoda_main.tutor_jobs as tj
	WHERE
		tr.tutor_job_id=tj.id
		and tr.status = 1
		and tr.request_status = 0
		and tr.request_type = 2
		and tr.created_at >= '2020-02-01'

	"""
	# QUERY RETURNS 6780 JOBS 6674 UP FOR DATABASE
	inputFile = "./tuitions/model_data/6674_raw_tuition_request.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if RequestForTutor.objects.filter(pk=each['tutor_job_id']).exists():
				rft = RequestForTutor.objects.get(pk=each['tutor_job_id'])
				print(rft)

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				parent_rft = rft,
				status = 'hot-job',
				job_origin = 'hot-job',
				tutor = t
			)
			tr.save()
			print(tr.id)
			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()

			print(tr)
	except Exception as e:
		print(e)
		pass


def add_tuition_request_in_process():
	"""
		where
			tr.status = 1
			tr.request_status = 1, 5

			tr.request_type = 2
	"""
	# QUERY RETURNS 1031 REQUESTS IN PROCESS
	# 1007 UP FOR DATABASE

	inputFile = "./tuitions/model_data/1007_raw_tuition_request_in_process.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if RequestForTutor.objects.filter(pk=each['tutor_job_id']).exists():
				rft = RequestForTutor.objects.get(pk=each['tutor_job_id'])
				print(rft)

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				parent_rft = rft,
				status = 'in-process',
				job_origin = 'hot-job',
				tutor = t
			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()
			print(tr.id)
			print(tr)
	except Exception as e:
		print(tr.id)
		print(e)
		pass

def add_tuition_request_confirmed():
	"""
		where
			tr.status = 1
			tr.request_status = 3
			tr.request_type = 2
	"""
	# QUERY RETURNS 45 CONFIRMED REQUEST
	# ALL UP FOR DATABASE
	inputFile = "./tuitions/model_data/47_raw_tuition_request_confirmed.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if RequestForTutor.objects.filter(pk=each['tutor_job_id']).exists():
				rft = RequestForTutor.objects.get(pk=each['tutor_job_id'])
				print(rft)

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				parent_rft = rft,
				status = 'confirmed',
				job_origin = 'hot-job',
				tutor = t
			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"


			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()
			print(tr.id)
			print(tr)
	except Exception as e:
		print(tr.id)
		print(e)
		pass


def add_tuition_request_rejected_by_tutor_0():
	"""
		where
			tr.status = 1
			tr.request_status = 4
			tr.request_type = 2
	"""
	# QUERY RETURNS 842 REQUEST
	# 772 UP FOR DATABASE
	inputFile = "./tuitions/model_data/772_raw_tuition_request_rejected_by_tutor.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if RequestForTutor.objects.filter(pk=each['tutor_job_id']).exists():
				rft = RequestForTutor.objects.get(pk=each['tutor_job_id'])
				print(rft)

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				is_rejected_by_tutor = True,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				parent_rft = rft,
				status = 'hot-job',
				job_origin = 'hot-job',
				tutor = t
			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()
			print(tr.id)
			print(tr)
	except Exception as e:
		print(tr.id)
		print(e)
		pass


def add_tuition_request_rejected_by_tutor_1():
	"""
		where
			tr.status = 1
			tr.request_status = 2
			tr.request_type = 2
	"""
	# QUERY RETURNS 1587 JOBS
	# 1570 UP FOR DATABASE
	inputFile = "./tuitions/model_data/1570_raw_tuition_request_rejected_by_tutor.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if RequestForTutor.objects.filter(pk=each['tutor_job_id']).exists():
				rft = RequestForTutor.objects.get(pk=each['tutor_job_id'])
				print(rft)

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				parent_rft = rft,
				is_rejected_by_tutor = True,
				job_origin = 'hot-job',
				tutor = t
			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['tutor_confirmed'] == 1:
				tr.status = 'in-process'
				tr.save()
				print(tr.status)

			elif each['tutor_confirmed'] == 0:
				tr.status = 'hot-job'
				tr.save()
				print(tr.status)

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()
			print(tr.id)
			print(tr)
	except Exception as e:
		print(tr.id)
		print(e)
		pass


def add_tuition_request_wfp():
	"""
		where
			tr.status = 1
			tr.request_status = 1
			tutor confirmed = 1
			tr.request_type = 2
	"""
	# QUERY RETURNS 318 JOBS
	# 316 UP FOR DATABASE
	inputFile = "./tuitions/model_data/316_raw_tuition_request_waiting_for_parent.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if RequestForTutor.objects.filter(pk=each['tutor_job_id']).exists():
				rft = RequestForTutor.objects.get(pk=each['tutor_job_id'])
				print(rft)

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				parent_rft = rft,
				status = 'waiting-for-parent',
				job_origin = 'hot-job',
				tutor = t
			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()

			print(tr)
	except Exception as e:
		print(e)
		pass


def add_tuition_request_wft():
	"""
		where
			tr.status = 1
			tr.request_status = 1
			tutor_confirmed = 0
			parent_confirmed = 1
			tr.request_type = 2
	"""
	# QUERY RETURNS 2 JOBS ALL UP FOR DATABASE

	inputFile = "./tuitions/model_data/2_raw_tuition_request_waiting_for_tutor.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			if RequestForTutor.objects.filter(pk=each['tutor_job_id']).exists():
				rft = RequestForTutor.objects.get(pk=each['tutor_job_id'])
				print(rft)

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				parent_rft = rft,
				status = 'waiting-for-tutor',
				job_origin = 'hot-job',
				tutor = t
			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()

			print(tr)
	except Exception as e:
		print(e)
		pass




"""
DIRECT REQUEST
"""
def add_tuition_request_direct_request():
	"""
		where
			tr.status = 0, 1
			tr.request_status = 0
			tr.request_type = 1 DIRECT REQUEST
	"""
	# QUERY RETURNS 375 JOBS 372 UP FOR DATABASE

	inputFile = "./tuitions/model_data/372_raw_tuition_request_dr.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				status = 'direct-request',
				job_origin = 'direct-request',
				tutor = t,
				note_by_parent = each['message']
			)
			tr.save()
			print(tr.id)
			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['status'] == 0:
				tr.is_rejected_by_ops = True
				tr.save()
			elif each['status'] == 1:
				tr.is_rejected_by_ops = False
				tr.save()

			if each['student_school']:
				tr.student_school = each['student_school']
				tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()

			print(tr)
	except Exception as e:
		print(e)
		pass


def add_tuition_request_direct_request_confirmed():
	"""
		where
			tr.status = 0, 1
			tr.request_status = 3
			tr.request_type = 1 DIRECT REQUEST
	"""
	# QUERY RETURNS 11 JOBS 10 UP FOR DATABASE
	inputFile = "./tuitions/model_data/10_raw_tuition_request_dr_confirmed.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				status = 'confirmed',
				job_origin = 'direct-request',
				tutor = t,
				note_by_parent = each['message']
			)
			tr.save()
			print(tr.id)
			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['status'] == 0:
				tr.is_rejected_by_ops = True
				tr.save()
			elif each['status'] == 1:
				tr.is_rejected_by_ops = False
				tr.save()

			if each['student_school']:
				tr.student_school = each['student_school']
				tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()

			print(tr)
	except Exception as e:
		print(e)
		pass



def add_tuition_request_direct_request_in_process():
	"""
		where
			tr.status = 0, 1
			tr.request_status = 1, 5
			tr.request_type = 1
	"""
	# QUERY RETURNS 86 JOBS
	# 85 UP FOR DATABASE
	inputFile = "./tuitions/model_data/85_raw_dr_in_process.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:
			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				status = 'in-process',
				job_origin = 'direct-request',
				tutor = t,
				note_by_parent = each['message']

			)
			tr.save()
			print(tr.id)
			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['status'] == 0:
				tr.is_rejected_by_ops = True
				tr.save()
			elif each['status'] == 1:
				tr.is_rejected_by_ops = False
				tr.save()

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()
			print(tr.id)
			print(tr)
	except Exception as e:
		print(tr.id)
		print(e)
		pass



def add_tuition_request_direct_request_wfp():
	"""
		where
			tr.status = 1, 0
			tr.request_status = 1
			tutor confirmed = 1
			tr.request_type = 1
	"""
	# QUERY RETURNS 26 JOBS 25 UP FOR DATABASE
	inputFile = "./tuitions/model_data/25_dr_wfp.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				status = 'waiting-for-parent',
				job_origin = 'direct-request',
				tutor = t,
				note_by_parent = each['message']

			)
			tr.save()
			print(tr.id)
			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['status'] == 0:
				tr.is_rejected_by_ops = True
				tr.save()
			elif each['status'] == 1:
				tr.is_rejected_by_ops = False
				tr.save()

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()

			print(tr)
	except Exception as e:
		print(e)
		pass


def add_tuition_request_direct_request_wft_in_process():
	"""
		where
			tr.status = 1, 0
			tr.request_status = 1
			tutor confirmed = 0
			parent_confirmed = 0
			tr.request_type = 1
	"""
	# QUERY RETURNS 54 JOBS
	# ALL UP FOR DATABASE
	inputFile = "./tuitions/model_data/54_dr_wft_in_process.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				# parent_rft = rft,
				status = 'in-process',
				job_origin = 'direct-request',
				tutor = t,
				note_by_parent = each['message']
			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['status'] == 0:
				tr.is_rejected_by_ops = True
				tr.save()
			elif each['status'] == 1:
				tr.is_rejected_by_ops = False
				tr.save()

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()

			print(tr)
	except Exception as e:
		print(e)
		pass




def add_tuition_request_rejected_by_tutor():
	"""
		where
			tr.status = 1
			tr.request_status = 2, 4
			tr.request_type = 1
	"""
	# QUERY RETURNS 209 ALL UP FOR DATABASE
	inputFile = "./tuitions/model_data/209_dr_rbt.json"

	with open(inputFile, 'r') as jsonfile:
		data = json.load(jsonfile)
		jsonfile.close()
	try:
		for each in data:

			parent_fk = Parent.objects.get(pk=each['student_parent_id'])
			area_fk = Area.objects.get(pk=each['location_id'])
			t = Tutor.objects.get(pk=each['tutor_id'])

			tr = TuitionRequest(
				id = each['tutor_req_id'],
				parent = parent_fk,
				created_at = arrow.get(each['created_at']).datetime,
				updated_at = arrow.get(each['updated_at']).datetime,
				student_gender = each['student_gender'],
				student_class = each['class'],
				student_medium = each["medium"],
				tuition_area = area_fk,
				teaching_place_preference = each['teaching_preference'],
				number_of_days_per_week = each['no_of_days'],
				salary = Decimal(each['salary_max']),
				# parent_rft = rft,
				is_rejected_by_tutor = True,
				job_origin = 'direct-request',
				tutor = t,
				note_by_parent = each['message']

			)
			tr.save()
			print(tr.id)

			if tr.student_medium == "0":
				tr.student_medium = "english-medium"

			if each['tutor_confirmed'] == 1:
				tr.status = 'in-process'
				tr.save()
				print(tr.status)

			elif each['tutor_confirmed'] == 0:
				tr.status = 'direct-request'
				tr.save()
				print(tr.status)

			if each['student_school']:
				tr.student_school = each['student_school']
			tr.save()

			if each['subjects']:
				for sub in each['subjects']:
					tr.subjects.add(sub)
			tr.save()
			print(tr.id)
			print(tr)
	except Exception as e:
		print(tr.id)
		print(e)
		pass


def premium():
    '''
    SELECT t.id, t.created_at, t.updated_at, tu.id as tutor_id
    FROM
        yoda_main.transactions as t,
	    yoda_main.users as u,
        yoda_main.tutors as tu
    WHERE
        t.user_id=u.id
        and t.user_id=tu.user_id;
    '''
    # QUERY RETURNS 50 PREMIUM USER WITH TUTOR ID
    inputFile = "./tuitions/model_data/46_premium.json"
    with open(inputFile, 'r') as jsonfile:
    	data = json.load(jsonfile)
    	jsonfile.close()
    try:
    	for each in data:
    		tutor = Tutor.objects.get(pk=each['tutor_id'])
    		created_at = arrow.get(each['created_at'])
    		tutor.date_till_premium_account_valid = created_at.shift(days=90).datetime
    		tutor.premium_type = 'paid'
    		print(each['tutor_id'])
    		tutor.save()
    except:
    	pass


def init_array_search_fields():
	for tutor in Tutor.objects.all():
		# Add subjects
		for subject in tutor.offline_preferred_teaching_subjects.all():
			tutor.offline_preferred_teaching_subjects_arr.append(subject.id)

		# Add areas
		for area in tutor.offline_preferred_teaching_areas.all():
			tutor.offline_preferred_teaching_areas_arr.append(area.id)

		tutor.save()
		print(tutor.id)

def confirm_rft():
  for tr in TuitionRequest.objects.all():
    if tr.parent_rft:
      if tr.status == 'confirmed':
        if not tr.parent_rft.is_confirmed:
          tr.parent_rft.is_confirmed = True
          tr.parent_rft.save()


def run_all():
	add_offline_subjects()
	add_areas()
	add_universities()
	add_university_fields_of_study()
	add_schools()

	add_tutor()
	add_parents()
	add_request_for_tutors()

	add_tuition_request_hot_job()
	add_tuition_request_in_process()
	add_tuition_request_confirmed()
	add_tuition_request_rejected_by_tutor_0()
	add_tuition_request_rejected_by_tutor_1()
	add_tuition_request_wfp()
	add_tuition_request_wft()

	add_tuition_request_direct_request()
	add_tuition_request_direct_request_confirmed()
	add_tuition_request_direct_request_in_process()
	add_tuition_request_direct_request_wfp()
	add_tuition_request_direct_request_wft_in_process()
	add_tuition_request_rejected_by_tutor()

	premium()
	init_array_search_fields()

	confirm_rft()

def validate_rft():
	for each in RequestForTutor.objects.all():
		print(each.id)
		each.full_clean()

def validate_tuition_request():
	for each in TuitionRequest.objects.all():
		print(each.id)
		each.full_clean()

def validate_parent():
	for each in Parent.objects.all():
		print(each.id)
		each.full_clean()

def validate_tutor():
	for each in Tutor.objects.all():
		print(each.id)
		each.full_clean()

def validate_data():
	validate_rft()
	validate_tuition_request()
	# validate_tutor()
	# validate_parent()
