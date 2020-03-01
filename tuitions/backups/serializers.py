from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *


# Sign up serializers

class ParentSignUpSerializer(serializers.ModelSerializer):
	class Meta:
		model = Parent
		fields = [
			'full_name', 'phone_number', 'country', 'gender'
		]
	
	def create(self, validated_data):
		instance = Parent(**validated_data)
		instance.set_otp()
		instance.save()
		return instance


class StudentSignUpSerializer(serializers.ModelSerializer):
	class Meta:
		model = Student
		fields = [
			'full_name', 'phone_number', 'country', 'gender'
		]
	
	def create(self, validated_data):
		instance = Student(**validated_data)
		instance.set_otp()
		instance.save()
		return instance


# Details serializers

class ParentDetailsSerializer(serializers.ModelSerializer):
	class Meta:
		model = Parent
		fields = [
			'id', 'uuid', 'full_name', 'phone_number', 'country', 'gender', 
			'email', 'is_email_verified', 'points', 'gender', 'date_of_birth', 
			'display_picture', 'is_social_media_connected', 
			'name_in_social_media', 'is_verified_by_ops'
		]
		read_only_fields = [
			'id', 'uuid', 'full_name', 'phone_number', 'country', 'points', 
			'is_verified_by_ops'
		]


class StudentDetailsSerializer(serializers.ModelSerializer):
	class Meta:
		model = Student
		fields = [
			'id', 'uuid', 'full_name', 'phone_number', 'country', 'gender', 
			'email', 'is_email_verified', 'points', 'gender', 'date_of_birth', 
			'display_picture', 'is_social_media_connected', 
			'name_in_social_media', 'is_verified_by_ops'
		]
		read_only_fields = [
			'id', 'uuid', 'full_name', 'phone_number', 'country', 'points', 
			'is_verified_by_ops'
		]


class TutorDetailsSerializer(serializers.ModelSerializer):
	is_academic_background_complete = serializers.SerializerMethodField()
	def get_is_academic_background_complete(self, obj):
		if obj.country.code == 'BD':
			return bool(
				obj.undergraduate_university_academic_bg.is_complete and
				obj.school_academic_bg.is_complete and 
				obj.college_academic_bg.is_complete
			)
		else:
			return bool(
				obj.undergraduate_university_academic_bg.is_complete and
				obj.school_academic_bg.is_complete
			)

	jobs_left = serializers.SerializerMethodField()
	def get_jobs_left(self, obj):
		return obj.get_jobs_left()

	class Meta:
		model = Tutor
		fields = [
			'id', 'uuid', 'full_name', 'phone_number', 'country', 'gender', 
			'email', 'is_email_verified', 'points', 'display_picture',
			'is_verified_by_ops', 'account_type', 'is_social_media_connected', 
			'date_till_premium_account_valid',
			'is_personal_information_complete',
			'is_academic_background_complete', 
			'is_teaching_preferences_complete',
			'jobs_left', 'sign_up_date'
		]


# Tutor profile serializers

class TutorPersonalInformationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tutor
		fields = [
			'academic_medium', 'academic_field_of_study', 'gender',
			'date_of_birth', 'display_picture', 'about', 'home_area',
			'government_id_type', 'government_id_number', 
			'government_id_picture'
		]


class TutorTeachingPreferencesSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tutor
		fields = [
			'wants_to_teach_offline', 'offline_preferred_teaching_areas',
			'wants_to_teach_online', 'offline_preferred_teaching_subjects',
			'online_preferred_teaching_subjects', 'schedule', 
			'schedule_is_flexible', 'salary_range_start', 'salary_range_end'
		]


class TutorAcademicBackgroundSerializer(serializers.ModelSerializer):
	class Meta:
		model = AcademicBackground
		fields = [
			'institution_type', 'country', 'name_of_institution', 
			'name_of_degree', 'field_of_study', 'medium', 
			'bangla_medium_version', 'english_medium_curriculum', 
			'start_year', 'end_year', 'identification_document_picture' 
		]
		read_only_fields = ['institution_type',]


class TutorUndergraduateUniversityABSerializer(serializers.ModelSerializer):
	class Meta:
		model = AcademicBackground
		fields = [
			'institution_type', 'country', 'name_of_institution', 
			'name_of_degree', 'field_of_study', 'medium', 
			'bangla_medium_version', 'english_medium_curriculum', 
			'start_year', 'end_year', 'identification_document_picture' 
		]
		read_only_fields = [
			'institution_type', 'country', 'name_of_institution'
		]


# Area, subject, school, and university field of study list view serializers

class AreaSerializer(serializers.ModelSerializer):
	class Meta:
		model = Area
		fields = [
			'id', 'name', 'city', 'zip_code', 'state', 'district', 'division', 
			'country'
		]


class OfflineSubjectSerializer(serializers.ModelSerializer):
	class Meta:
		model = OfflineSubject
		fields = [
			'id', 'category', 'sub_category', 'name', 
			'english_medium_curriculum', 'country', 'subject_type'
		]


class SchoolSerializer(serializers.ModelSerializer):
	class Meta:
		model = School
		fields = ['id', 'name', 'country']


class UniversityFieldOfStudySerializer(serializers.ModelSerializer):
	class Meta:
		model = UniversityFieldOfStudy
		fields = ['id', 'name']


class UniversityDegreeSerializer(serializers.ModelSerializer):
	class Meta:
		model = UniversityDegree
		fields = ['id', 'name']


# Tutor filter serializers

class TutorFilterSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tutor
		fields = [
			'gender', 'offline_preferred_teaching_areas', 
			'offline_preferred_teaching_subjects', 'academic_medium', 
			'salary_range_start', 'salary_range_end'
			# undergraduate_university in view
		]


# Tutor public view serializer

class TutorPublicSerializer(serializers.ModelSerializer):
	undergraduate_university_academic_bg = serializers.SerializerMethodField()
	def get_undergraduate_university_academic_bg(self, obj):
		return TutorUndergraduateUniversityABSerializer(
			obj.undergraduate_university_academic_bg
		).data

	school_academic_bg = serializers.SerializerMethodField()
	def get_school_academic_bg(self, obj):
		return TutorAcademicBackgroundSerializer(
			obj.school_academic_bg
		).data

	college_academic_bg = serializers.SerializerMethodField()
	def get_college_academic_bg(self, obj):
		return TutorAcademicBackgroundSerializer(
			obj.college_academic_bg
		).data

	class Meta:
		model = Tutor
		fields = [
			'id', 'uuid', 'display_picture', 'full_name', 'gender', 
			'academic_medium', 'salary_range_start', 'salary_range_end', 
			'schedule', 'schedule_is_flexible', 
			'number_of_public_profile_views', 'tutor_behavior', 
			'way_of_teaching', 'communication_skills', 'time_management', 
			'number_of_reviews', 'undergraduate_university_academic_bg', 
			'school_academic_bg', 'college_academic_bg', 
			'm2m_fields_serialized', 'is_verified_by_ops'
		]


# Jobs serializers

class RequestForTutorCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = RequestForTutor
		fields = [
			'id', 'uuid', 'parent', 'created_at', 'note_by_parent', 
			'student_gender', 'student_school', 'student_class', 
			'student_medium', 'student_bangla_medium_version', 
			'student_english_medium_curriculum', 'tuition_area', 
			'teaching_place_preference', 'number_of_days_per_week', 'salary', 
			'is_salary_negotiable', 'subjects', 'tutor_gender', 
			'tutor_undergraduate_university', 'tutor_academic_medium', 
			'tutor_academic_field_of_study', 'is_confirmed',
			'confirmation_date'
		]
		read_only_fields = ['id', 'uuid', 'created_at', 'confirmation_date']



class RequestForTutorSerializer(serializers.ModelSerializer):
	tuition_area = serializers.SerializerMethodField()
	def get_tuition_area(self, obj):
		return AreaSerializer(obj.tuition_area).data

	subjects = serializers.SerializerMethodField()
	def get_subjects(self, obj):
		return OfflineSubjectSerializer(obj.subjects, many=True).data

	class Meta:
		model = RequestForTutor
		fields = [
			'id', 'uuid', 'parent', 'created_at', 'note_by_parent', 
			'student_gender', 'student_school', 'student_class', 
			'student_medium', 'student_bangla_medium_version', 
			'student_english_medium_curriculum', 'tuition_area', 
			'teaching_place_preference', 'number_of_days_per_week', 'salary', 
			'is_salary_negotiable', 'subjects', 'tutor_gender', 
			'tutor_undergraduate_university', 'tutor_academic_medium', 
			'tutor_academic_field_of_study', 'is_confirmed', 
			'confirmation_date'
		]


class DirectRequestCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = TuitionRequest
		fields = [
			'id', 'uuid', 'status', 'parent', 'tutor', 'created_at', 
			'note_by_parent', 'student_gender', 'student_school', 
			'student_class', 'student_medium', 'student_bangla_medium_version', 
			'student_english_medium_curriculum', 'tuition_area', 
			'teaching_place_preference', 'number_of_days_per_week', 'salary', 
			'is_salary_negotiable', 'subjects', 'confirmation_date', 
			'find_similar_tutors_for_parent', 'notification_created'
		]
		read_only_fields = [
			'id', 'uuid', 'created_at', 'confirmation_date'
		]


class TuitionRequestSerializer(serializers.ModelSerializer):
	parent = serializers.SerializerMethodField()
	def get_parent(self, obj):
		return {
			'id': obj.parent.id,
			'uuid': str(obj.parent.uuid),
			'full_name': obj.parent.full_name,
			'phone_number': obj.parent.phone_number,
			'display_picture': obj.parent.display_picture
		}

	tutor = serializers.SerializerMethodField()
	def get_tutor(self, obj):
		return {
			'id': obj.tutor.id,
			'uuid': str(obj.tutor.uuid),
			'full_name': obj.tutor.full_name,
			'phone_number': obj.tutor.phone_number,
			'display_picture': obj.tutor.display_picture
		}

	tuition_area = serializers.SerializerMethodField()
	def get_tuition_area(self, obj):
		return AreaSerializer(obj.tuition_area).data

	subjects = serializers.SerializerMethodField()
	def get_subjects(self, obj):
		return OfflineSubjectSerializer(obj.subjects, many=True).data

	class Meta:
		model = TuitionRequest
		fields = [
			'id', 'uuid', 'status', 'is_rejected_by_tutor', 'parent', 'tutor', 
			'created_at', 'note_by_parent', 'student_gender', 'student_school', 
			'student_class', 'student_medium', 'student_bangla_medium_version', 
			'student_english_medium_curriculum', 'tuition_area', 
			'teaching_place_preference', 'number_of_days_per_week', 'salary', 
			'is_salary_negotiable', 'subjects', 'confirmation_date', 
			'find_similar_tutors_for_parent', 'parent_rft'
		]


# Notification serializer

class NotificationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notification
		fields = ['notification_type', 'created_at', 'title', 'body', 'url']


# Transaction serializer

class TransactionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Transaction
		fields = [
			'uuid', 'created_at', 'total_amount', 'currency', 'trx_id', 
			'title', 'body', 'url', 'vendor_name'
		]


# Ops related serializers

class UserSerializer(serializers.ModelSerializer):
	user_type = serializers.SerializerMethodField()
	def get_user_type(self, obj):
		if obj.account:
			return obj.account.account_type
		return ""

	university = serializers.SerializerMethodField()
	def get_university(self, obj):
		if obj.account:
			if obj.account.university:
				return {
					'id': obj.account.university.id,
					'name': obj.account.university.name
				}
		return None

	country = serializers.SerializerMethodField()
	def get_country(self, obj):
		if obj.account:
			return str(obj.account.country)
		return ""


	class Meta:
		model = User
		fields = [
			'user_type', 'username', 'email', 'first_name', 'last_name', 
			'university', 'country'
		]


# Sign up serializers

class OpsParentSignUpSerializer(serializers.ModelSerializer):
	class Meta:
		model = Parent
		fields = [
			'uuid', 'full_name', 'phone_number', 'is_phone_number_verified', 
			'country', 'gender',
		]
		read_only_fields = ['uuid',]


class OpsStudentSignUpSerializer(serializers.ModelSerializer):
	class Meta:
		model = Student
		fields = [
			'uuid', 'full_name', 'phone_number', 'is_phone_number_verified', 
			'country', 'gender',
		]
		read_only_fields = ['uuid',]


class OpsTutorSignUpSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tutor
		fields = [
			'uuid', 'full_name', 'phone_number', 'country', 'gender', 
			'sign_up_channel', 'undergraduate_university',
			'undergraduate_university_id_number', 
			'undergraduate_university_identification_document_picture',
			'academic_medium', 'academic_field_of_study',
		]
		read_only_fields = ['uuid']


# User list and details serializers

class OpsParentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Parent
		fields = [
			'id', 'uuid', 'full_name', 'phone_number', 
			'is_phone_number_verified', 'country', 'gender', 'email', 
			'is_email_verified', 'points', 'date_of_birth', 'display_picture', 
			'is_social_media_connected', 'name_in_social_media', 
			'is_verified_by_ops', 'is_suspended_by_ops', 'is_deleted', 
			'sign_up_date', 'last_active_at', 'ops_notes'
		]
		read_only_fields = [
			'id', 'uuid', 'points', 'is_verified_by_ops', 'sign_up_date', 
			'last_active_at', 'ops_notes'
		]


class OpsStudentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Student
		fields = [
			'id', 'uuid', 'full_name', 'phone_number', 
			'is_phone_number_verified', 'country', 'gender', 'email', 
			'is_email_verified', 'points', 'date_of_birth', 'display_picture', 
			'is_social_media_connected', 'name_in_social_media', 
			'is_verified_by_ops', 'is_suspended_by_ops', 'is_deleted', 
			'sign_up_date', 'last_active_at', 'ops_notes'
		]
		read_only_fields = [
			'id', 'uuid', 'points', 'is_verified_by_ops', 'sign_up_date', 
			'last_active_at', 'ops_notes'
		]


class OpsTutorListSerializer(serializers.ModelSerializer):
	is_academic_background_complete = serializers.SerializerMethodField()
	def get_is_academic_background_complete(self, obj):
		if obj.country.code == 'BD':
			return bool(
				obj.undergraduate_university_academic_bg.is_complete and
				obj.school_academic_bg.is_complete and 
				obj.college_academic_bg.is_complete
			)
		else:
			return bool(
				obj.undergraduate_university_academic_bg.is_complete and
				obj.school_academic_bg.is_complete
			)

	class Meta:
		model = Tutor
		fields = [
			'id', 'uuid', 'full_name', 'phone_number', 
			'is_phone_number_verified', 'points', 'account_type', 
			'date_till_premium_account_valid', 'country', 'email', 
			'is_email_verified', 'ops_notes',

			# Completion statuses
			'is_personal_information_complete', 
			'is_academic_background_complete', 
			'is_teaching_preferences_complete',

			# Personal information
			'academic_medium', 'academic_field_of_study', 'gender',

			# Teaching preferences
			'm2m_fields_serialized',

			# Dates, checks, and ops related fields
			'is_verified_by_ops','is_suspended_by_ops', 'is_deleted', 
			'sign_up_date', 'last_active_at', 'sign_up_channel'
		]


class OpsTutorDetailsGetSerializer(serializers.ModelSerializer):
	is_academic_background_complete = serializers.SerializerMethodField()
	def get_is_academic_background_complete(self, obj):
		if obj.country.code == 'BD':
			return bool(
				obj.undergraduate_university_academic_bg.is_complete and
				obj.school_academic_bg.is_complete and 
				obj.college_academic_bg.is_complete
			)
		else:
			return bool(
				obj.undergraduate_university_academic_bg.is_complete and
				obj.school_academic_bg.is_complete
			)

	undergraduate_university_academic_bg = serializers.SerializerMethodField()
	def get_undergraduate_university_academic_bg(self, obj):
		return TutorUndergraduateUniversityABSerializer(
			obj.undergraduate_university_academic_bg
		).data

	school_academic_bg = serializers.SerializerMethodField()
	def get_school_academic_bg(self, obj):
		return TutorAcademicBackgroundSerializer(
			obj.school_academic_bg
		).data

	college_academic_bg = serializers.SerializerMethodField()
	def get_college_academic_bg(self, obj):
		return TutorAcademicBackgroundSerializer(
			obj.college_academic_bg
		).data

	class Meta:
		model = Tutor
		fields = [
			'id', 'uuid', 'full_name', 'phone_number', 
			'is_phone_number_verified', 'country', 'email', 
			'is_email_verified', 'points', 'account_type', 
			'date_till_premium_account_valid', 'ops_notes',

			# Completion statuses
			'is_personal_information_complete', 
			'is_academic_background_complete', 
			'is_teaching_preferences_complete',

			# Personal information
			'academic_medium', 'academic_field_of_study', 'gender',
			'date_of_birth', 'display_picture', 'about', 'home_area',
			'government_id_type', 'government_id_number', 
			'government_id_picture',

			# Academic backgrounds
			'undergraduate_university_academic_bg', 'school_academic_bg',
			'college_academic_bg',

			# Teaching preferences
			'wants_to_teach_offline', 'offline_preferred_teaching_areas',
			'wants_to_teach_online', 'offline_preferred_teaching_subjects',
			'online_preferred_teaching_subjects', 'schedule', 
			'schedule_is_flexible', 'salary_range_start', 'salary_range_end',
			'm2m_fields_serialized',

			# Dates, checks, and ops related fields
			'is_verified_by_ops','is_suspended_by_ops', 'is_deleted', 
			'sign_up_date', 'last_active_at', 'sign_up_channel'
		]


class OpsTutorDetailsPostSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tutor
		fields = [
			'full_name', 'phone_number', 'is_phone_number_verified',
			'country', 'email', 'is_email_verified', 'is_suspended_by_ops',
			'is_deleted'
		]


# User filter serializers

class OpsParentFilterSerializer(serializers.ModelSerializer):
	class Meta:
		model = Parent
		fields = [
			'full_name', 'is_phone_number_verified', 'gender',
			'is_social_media_connected', 'is_verified_by_ops', 
			'is_suspended_by_ops', 'is_deleted', 'sign_up_date', 
			'last_active_at'
		]


class OpsStudentFilterSerializer(serializers.ModelSerializer):
	class Meta:
		model = Student
		fields = [
			'full_name', 'is_phone_number_verified', 'gender', 
			'is_social_media_connected', 'is_verified_by_ops', 
			'is_suspended_by_ops', 'is_deleted', 'sign_up_date', 
			'last_active_at'
		]


class OpsTutorFilterSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tutor
		fields = [
			'full_name', 'is_phone_number_verified', 'gender', 
			'offline_preferred_teaching_areas', 
			'offline_preferred_teaching_subjects', 'academic_medium', 
			'salary_range_start', 'salary_range_end', 'is_verified_by_ops', 
			'is_suspended_by_ops', 'is_deleted', 'sign_up_date', 
			'last_active_at', 'is_personal_information_complete', 
			'is_teaching_preferences_complete', 'account_type', 
			'date_till_premium_account_valid', 
			# undergraduate_university, is_academic_background_complete in view
		]


# Job serializers

class OpsRequestForTutorSerializer(serializers.ModelSerializer):
	parent = serializers.SerializerMethodField()
	def get_parent(self, obj):
		return {
			'id': obj.parent.id,
			'uuid': str(obj.parent.uuid),
			'full_name': obj.parent.full_name,
			'phone_number': obj.parent.phone_number,
			'display_picture': obj.parent.display_picture,
			'is_verified_by_ops': obj.parent.is_verified_by_ops,
			'is_suspended_by_ops': obj.parent.is_suspended_by_ops,
			'is_deleted': obj.parent.is_deleted
		}

	tuition_area = serializers.SerializerMethodField()
	def get_tuition_area(self, obj):
		return AreaSerializer(obj.tuition_area).data

	subjects = serializers.SerializerMethodField()
	def get_subjects(self, obj):
		return OfflineSubjectSerializer(obj.subjects, many=True).data

	class Meta:
		model = RequestForTutor
		fields = [
			# Base tuition request
			'id', 'uuid', 'parent', 'created_at', 'note_by_parent', 
			'student_gender', 'student_school', 'student_class', 
			'student_medium', 'student_bangla_medium_version', 
			'student_english_medium_curriculum', 'tuition_area', 
			'teaching_place_preference', 'number_of_days_per_week', 'salary', 
			'is_salary_negotiable', 'subjects', 

			# Ops related fields
			'is_rejected_by_ops', 'confirmation_date', 'ops_notes', 'country', 

			# RFT related fields
			'tutor_gender', 'tutor_undergraduate_university', 
			'tutor_academic_medium', 'tutor_academic_field_of_study', 
			'is_confirmed', 
		]
		read_only_fields = [
			'id', 'uuid', 'created_at', 'is_rejected_by_ops', 
			'confirmation_date', 'ops_notes', 'country', 'is_confirmed',
		]


class OpsRequestForTutorFilterSerializer(serializers.ModelSerializer):
	class Meta:
		model = RequestForTutor
		fields = [
			'created_at', 'is_rejected_by_ops', 'confirmation_date', 
			'is_confirmed',
			# parent.phone_number, and parent.is_verified_by_ops in view
		]


class OpsTuitionRequestSerializer(serializers.ModelSerializer):
	parent = serializers.SerializerMethodField()
	def get_parent(self, obj):
		return {
			'id': obj.parent.id,
			'uuid': str(obj.parent.uuid),
			'full_name': obj.parent.full_name,
			'phone_number': obj.parent.phone_number,
			'display_picture': obj.parent.display_picture,
			'is_verified_by_ops': obj.parent.is_verified_by_ops,
			'is_suspended_by_ops': obj.parent.is_suspended_by_ops,
			'is_deleted': obj.parent.is_deleted
		}

	tuition_area = serializers.SerializerMethodField()
	def get_tuition_area(self, obj):
		return AreaSerializer(obj.tuition_area).data

	subjects = serializers.SerializerMethodField()
	def get_subjects(self, obj):
		return OfflineSubjectSerializer(obj.subjects, many=True).data

	tutor = serializers.SerializerMethodField()
	def get_tutor(self, obj):
		return {
			'id': obj.tutor.id,
			'uuid': str(obj.tutor.uuid),
			'full_name': obj.tutor.full_name,
			'phone_number': obj.tutor.phone_number,
			'display_picture': obj.tutor.display_picture,
			'is_verified_by_ops': obj.tutor.is_verified_by_ops,
			'is_suspended_by_ops': obj.tutor.is_suspended_by_ops,
			'is_deleted': obj.tutor.is_deleted
		}

	class Meta:
		model = TuitionRequest
		fields = [
			# Base tuition request
			'id', 'uuid', 'parent', 'created_at', 'note_by_parent', 
			'student_gender', 'student_school', 'student_class', 
			'student_medium', 'student_bangla_medium_version', 
			'student_english_medium_curriculum', 'tuition_area', 
			'teaching_place_preference', 'number_of_days_per_week', 'salary', 
			'is_salary_negotiable', 'subjects', 

			# Ops related fields
			'is_rejected_by_ops', 'confirmation_date', 'ops_notes', 'country', 

			# Tuition request related fields
			'status', 'is_rejected_by_tutor', 'find_similar_tutors_for_parent', 
			'tutor', 'parent_rft', 'notification_created'
		]


class OpsTuitionRequestFilterSerializer(serializers.ModelSerializer):
	class Meta:
		model = TuitionRequest
		fields = [
			'created_at', 'is_rejected_by_ops', 'confirmation_date', 'status', 
			'is_rejected_by_tutor', 
			# parent.phone_number, tutor.phone_number, and 
			# parent.is_verified_by_ops in view
		]

