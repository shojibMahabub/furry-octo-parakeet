import arrow
import jwt
import random
import threading
import uuid

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import (
	MinValueValidator, MaxValueValidator, MinLengthValidator
)
from django_countries.fields import CountryField
from django.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from .env_variables_manager import get_auth_jwt_secret
from .helpers import (
	JOBS_LIMIT, get_positive_or_zero, field_is_not_null, 
	SMS_SENDER_COUNTRY_MAP, get_empty_schedule_array, get_default_ops_notes
)
from .validators import PHONE_NUMBER_VALIDATOR_COUNTRY_MAP


# Models

class SiteConfig(SingletonModel):
	"""Stores site-wide config."""
	name_of_business = models.CharField(
		_('name of business'),
		max_length=255,
		default='Yoda Technologies Ltd.'
	)

	def __str__(self):
		return 'Site config'

	class Meta:
		verbose_name = 'Site config'


class Account(models.Model):
	"""Stores an account for a user."""
	user = models.OneToOneField(
		User,
		related_name='account',
		on_delete=models.CASCADE,
		verbose_name=_('user')
	)
	account_type = models.CharField(
		_('account type'),
		max_length=120,
		choices=(
			('campus-ambassador', 'Campus Ambassador'),
			('operations', 'Operations'),
			('activation-manager', 'Activation manager'),
			('admin', 'Admin'),
			('other', 'Other')
		),
		default='other'
	)
	university = models.ForeignKey(
		'University',
		related_name='accounts_with_university',
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		verbose_name=_('university'),
		help_text=_(
			'Optional. Must be set for campus ambassadors so that they can '
			'get access to the tutor sign up forms.'
		)
	)
	country = CountryField(_('country'), default='BD')

	def __str__(self):
		return self.user.username

	def get_auth_jwt(self):
		"""Get the authentication JWT for the user account."""
		encoded = jwt.encode({
			'id': self.id,
			'user_type': self.account_type
		}, get_auth_jwt_secret())
		return encoded.decode('utf-8')

def create_account(sender, instance, **kwargs):
	"""Create a user account post-save."""
	if not Account.objects.filter(user=instance).exists():
		Account.objects.create(user=instance)

post_save.connect(create_account, sender=User)


class Area(models.Model):
	"""Stores a  broad area.

	Notes:
		- Some fields are nullable, as not all countries follow the same 
		format for areas.
	"""
	name = models.CharField(
		_('name'), 
		max_length=255,
		help_text=_(
			'Required. Name of the area. Eg: Banani, Kuningan, Kuta, etc.'
		)
	)
	city = models.CharField(
		_('city'),
		max_length=255,
		help_text=_(
			'Required. Name of the city where the area is located. Eg: Dhaka, '
			'Jakarta, Singapore, etc.'
		)
	)
	zip_code = models.CharField(
		_('zip code'),
		max_length=50,
		help_text=_('Required. Zip code of the area.')
	)
	state = models.CharField(
		_('state'),
		max_length=255,
		blank=True,
		help_text=_('Optional. Some countries don\'t have states.')
	)
	district = models.CharField(
		_('district'),
		max_length=255,
		blank=True,
		help_text=_('Optional. Some countries don\'t have districts.')
	)
	division = models.CharField(
		_('division'),
		max_length=255,
		blank=True,
		help_text=_('Optional. Some countries don\'t have divisions.')
	)
	country = CountryField(
		_('country'),
		default='BD',
		help_text=_('Required. Name of the country where the area is located.')
	)
	nearby_areas = models.ManyToManyField(
		'self',
		verbose_name=_('nearby areas'),
		blank=True,
		help_text=_(
			'Optional. Tutors from nearby areas will pop up in the results'
			'if the search filters are too restrictive. Only for internal use.'
		)
	)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ('name',)


class BaseSubject(models.Model):
	"""Base subject, extended by offline and online subjects."""
	name = models.CharField(
		_('name'),
		max_length=255,
		help_text=_(
			'Required. Name of the subject. Eg: Mathematics, Physics, Essay '
			'writing, etc.'
		)
	)
	category = models.CharField(
		_('category or medium'),
		max_length=50,
		help_text=_(
			'Required. Broad category of the subject. Also includes the '
			'academic mediums in applicable countries. Eg: english medium, '
			'bangla medium, test preparation, etc.'
		)
	)
	sub_category = models.CharField(
		_('sub-category or class'),
		max_length=120,
		help_text=_(
			'Required. Specific sub-category of the subject. Includes the '
			'academic classes. Eg: Class 5, Class 8, SSC, HSC, O-levels, '
			'A-levels, etc.'
		)
	)
	english_medium_curriculum = models.CharField(
		_('english medium curriculum'),
		max_length=50,
		blank=True,
		help_text=_(
			'Optional. Only for Bangladesh. Extra filtering option needed for '
			'english medium subjects based on their curriculums.'
		)
	)
	country = CountryField(
		_('country'),
		blank=True,
		null=True,
		default='BD',
		help_text=_(
			'Optional. Can be empty if the subject is general and will be '
			'taught online.'
		)
	)
	subject_type = models.CharField(
		_('subject type'),
		max_length=255,
		blank=True,
		help_text=_('Type used as an extra filtering option for the API.')
	)

	def __str__(self):
		if not self.english_medium_curriculum:
			return f'{self.name} ({self.category}, {self.sub_category})'
		else:
			return str(
				f'{self.name} ({self.category}, {self.sub_category}, '
				f'{self.english_medium_curriculum})'
			)

	class Meta:
		abstract = True


class OfflineSubject(BaseSubject):
	"""Stores an offline subject."""
	country = CountryField(
		_('country'),
		default='BD',
		help_text=_('Required for offline subjects.')
	)


class OnlineSubject(BaseSubject):
	"""Stores an online subject."""
	pass


class University(models.Model):
	"""Stores an university."""
	name = models.CharField(
		_('name'), 
		max_length=255,
		help_text=_(
			'Required. Name of the university. Eg: North South University, '
			'Boston University, National University of Singapore, etc.'
		)
	)
	grade = models.IntegerField(
		_('grade'),
		blank=True,
		null=True,
		choices=(
			(1, 'Top grade'),
			(2, 'Medium grade'),
			(3, 'Bottom grade')
		),
		help_text=_(
			'Optional. Determines the level of university in terms of '
			'education quality and prestige. Only for internal use.'
		)
	)
	areas = models.ManyToManyField(
		Area,
		related_name='universities',
		verbose_name=_('areas'),
		blank=True,
		help_text=_('Areas where branches of the university is located.')
	)
	addresses = models.TextField(
		_('addresses'),
		blank=True,
		help_text=_(
			'Optional. Exact addresses of the universities. For multiple '
			'addresses, please separate them using new lines.'
		)
	)
	similar_universities = models.ManyToManyField(
		'self',
		verbose_name=_('similar universities'),
		blank=True,
		help_text=_(
			'Optional. Tutors from similar universities will pop up in the '
			'results if the search filters are too restrictive. Only for '
			'internal use.'
		)
	)
	country = CountryField(
		_('country'),
		default='BD',
		help_text=_(
			'Required. Name of the country where the university is located.'
		)
	)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ('name',)
		verbose_name_plural = 'universities'


class UniversityFieldOfStudy(models.Model):
	"""Stores a university field of study.

	Notes:
		- This is made into a database table so that the internal operations 
		team can add more fields of study when needed.
	"""
	name = models.CharField(_('name'), max_length=255)

	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = 'university fields of study'


class UniversityDegree(models.Model):
	"""Stores a university degree.

	Notes:
		- This is made into a database table so that the internal operations 
		team can add more fields of study when needed.
	"""
	name = models.CharField(_('name'), max_length=255)

	def __str__(self):
		return self.name


class School(models.Model):
	"""Stores a school.

	Notes:
		- Only the 500 or so most popular schools are stored for every country.
		- For Bangladesh only, this table is also used to store colleges.
	"""
	name = models.CharField(_('name'), max_length=255)
	country = CountryField(
		_('country'),
		default='BD',
		help_text=_(
			'Required. Name of the country where the school is located.'
		)
	)

	def __str__(self):
		return self.name


class MobileDevice(models.Model):
	"""Stores a device where the Yoda app is installed."""
	name = models.CharField(
		_('name'),
		max_length=255,
		blank=True,
		help_text=_('Name of the mobile phone.')
	)
	id_number = models.CharField(_('id number'), max_length=255)
	operating_system = models.CharField(
		_('operating system'),
		max_length=255,
		blank=True
	)

	def __str__(self):
		return self.id_number


class CustomUser(models.Model):
	"""Abstract custom user model, extended by parents, students, and tutors.
	"""
	# ID and other required fields
	uuid = models.UUIDField(
		_('UUID'),
		default=uuid.uuid4,
		unique=True,
		db_index=True
	)
	mobile_devices = models.ManyToManyField(
		MobileDevice,
		blank=True,
		verbose_name=_('mobile devices')
	)
	full_name = models.CharField(
		_('full name'),
		max_length=255
	)
	phone_number = models.CharField(
		_('phone number'),
		max_length=120,
		unique=True
	)
	is_phone_number_verified = models.BooleanField(
		_('phone number verification status'),
		default=False
	)
	email = models.EmailField(_('email'), blank=True)
	is_email_verified = models.BooleanField(
		_('email verification status'),
		default=False
	)
	country = CountryField(_('country'), default='BD')
	points = models.BigIntegerField(
		_('points'),
		default=0,
		validators=[MinValueValidator(0)]
	)
	sign_up_date = models.DateTimeField(default=timezone.now)

	# Personal information fields
	gender = models.CharField(
		_('gender'),
		max_length=50,
		blank=True,
		choices=(
			('male', 'Male'),
			('female', 'Female')
		)
	)
	date_of_birth = models.DateField(
		_('date of birth'),
		blank=True,
		null=True
	)
	display_picture = models.URLField(
		_('display picture'),
		blank=True,
		help_text=_(
			'Optional. Display picture of the user. Note: The picture must '
			'contain the user\'s face, ideally without any other faces.'
		)
	)
	is_social_media_connected = models.BooleanField(
		_('social media connection status'),
		default=False,
		help_text=_(
			'Set to True if the parent or student has connected their '
			'social media account. Can be used as a sort of verification '
			'status.'
		)
	)
	name_in_social_media = models.CharField(
		_('name in social media'),
		max_length=255,
		blank=True
	)

	# Password related fields
	otp = models.IntegerField(
		_('one-time password'),
		blank=True,
		null=True,
		help_text=_(
			'Can be used for logging in without a password, if the password '
			'is not set.'
		),
		validators=[MinValueValidator(111111), MaxValueValidator(999999)]
	)
	otp_expiry_timestamp = models.BigIntegerField(
		_('otp expiry timestamp'),
		blank=True,
		null=True,
		help_text=_('One-time password (OTP) expiry timestamp.')
	)
	password = models.CharField(_('password'), max_length=128, blank=True)

	# Operations related fields
	is_verified_by_ops = models.BooleanField(
		_('ops verification status'),
		default=False,
		help_text=_(
			'Set to True if the tutor has been verified by the internal '
			'operations team.'
		)
	)
	latest_ops_verification_timestamp = models.BigIntegerField(
		_('latest ops verification timestamp'),
		blank=True,
		null=True,
		help_text=_(
			'Timestamp of the latest time the tutor was verified by the '
			'internal operations team. Note: A failed verification is still a '
			'verification.'
		)
	)
	ops_notes = JSONField(
		_('ops notes'),
		default=get_default_ops_notes,
		blank=True,
		encoder=DjangoJSONEncoder
	)
	last_active_at = models.DateField(
		_('last active at'),
		blank=True,
		null=True,
		help_text=_('Date of the last activity.')
	)
	signed_up_by = models.ForeignKey(
		Account,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='%(app_label)s_%(class)s_related_signed_up_by'
	)
	verified_by = models.ForeignKey(
		Account,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='%(app_label)s_%(class)s_related_verified_by'
	)
	is_suspended_by_ops = models.BooleanField(
		_('ops suspension status'),
		default=False
	)
	is_deleted = models.BooleanField(
		_('deletion status'),
		default=False
	)

	def __str__(self):
		return self.full_name

	def clean(self):
		"""Method overridden to validate the phone number, and make sure no 
		other user exists with the same verified phone number.
		"""
		# Check if the country is accepted for user sign ups
		if not self.country.code in PHONE_NUMBER_VALIDATOR_COUNTRY_MAP:
			raise ValidationError(
				{'country': 'Our service is not available in this country.'}
			)

		# Validate the phone number
		try:
			self.phone_number = PHONE_NUMBER_VALIDATOR_COUNTRY_MAP[
				self.country.code
			](self.phone_number)
		except Exception as e:
			raise ValidationError({'phone_number': e})

		# Make sure no other user exists with the same verified phone number
		if self.__class__.objects.filter(
			phone_number=self.phone_number,
			is_phone_number_verified=True).exclude(pk=self.pk).exists():
			raise ValidationError(
				{
					'phone_number':
					'Another user with that phone number already exists.'
				}
			)

		super(CustomUser, self).clean()

	def set_otp(self):
		"""Set the one-time password, and save the user."""
		self.otp = random.randint(111111, 1000000)
		now = arrow.utcnow()
		otp_expiry = now.shift(hours=+24)
		self.otp_expiry_timestamp = otp_expiry.timestamp

		# Sending SMS
		try:
			if self.country.code in SMS_SENDER_COUNTRY_MAP:
				SMS_SENDER_COUNTRY_MAP[self.country.code](
					self.phone_number,
					str(
						f'[Yoda] Use the OTP {self.otp} to login to your '
						f'account.'
					)
				)
		except Exception as e:
			pass

	def get_auth_jwt(self):
		"""Get the authentication JWT for the user."""
		encoded = jwt.encode({
			'uuid': str(self.uuid),
			'user_type': self.__class__.__name__.lower()
		}, get_auth_jwt_secret())
		return encoded.decode('utf-8')

	def active_daily(self):
		"""Add points and update last_active_at for login."""
		self.last_active_at = arrow.utcnow().date()
		self.points += 5
		self.save()

	class Meta:
		abstract = True
		unique_together = ('phone_number', 'otp')
		ordering = ('id', )


class Parent(CustomUser):
	"""Stores a parent."""
	pass
	

class Student(CustomUser):
	"""Stores a student."""
	pass


class AcademicBackground(models.Model):
	"""Stores an academic background."""
	institution_type = models.CharField(
		_('type of institution'),
		max_length=50,
		choices=(
			('school', 'School'),
			('college', 'College'),
			('university', 'University'),
			('other', 'Other')
		)
	)
	country = CountryField(
		_('country'),
		blank=True,
		null=True,
		default='BD',
		help_text=_('The country where the institution is located.')
	)
	name_of_institution = models.CharField(
		_('name of institution'),
		max_length=255,
		blank=True,
		help_text=_(
			'Eg: North South University, Scholastica, etc.'
		)
	)
	name_of_degree = models.CharField(
		_('name of degree'),
		max_length=255,
		blank=True,
		help_text=_(
			'Eg: SSC, HSC, O-levels, A-levels,  B.Sc. in Computer Science, '
			'BBA, etc.'
		)
	)
	field_of_study = models.CharField(
		_('field of study'),
		max_length=255,
		blank=True,
		help_text=_(
			'Optional. For universities, it can be departments like Computer '
			'Science and Engineering. For schools (and colleges in '
			'Bangladesh), it can be Science, Commerce, Arts, etc.'
		)
	)
	medium = models.CharField(
		_('medium'),
		max_length=50,
		choices=(
			('english-medium', 'English medium'),
			('bangla-medium', 'Bangla medium')
		),
		blank=True,
		help_text=_('Only used in Bangladesh.')
	)
	bangla_medium_version = models.CharField(
		_('bangla medium version'),
		max_length=50,
		choices=(
			('english-version', 'English version'),
			('bangla-version', 'Bangla version')
		),
		blank=True,
		help_text=_(
			'Only used in Bangladesh. Can be empty if the school/college is '
			'english medium.'
		)
	)
	english_medium_curriculum = models.CharField(
		_('english medium curriculum'),
		max_length=50,
		choices=(
			('edexcel', 'Edexcel'),
			('cambridge', 'Cambridge'),
			('ib', 'IB')
		),
		blank=True,
		help_text=_(
			'Only used in Bangladesh. Can be empty if the school/college is '
			'bangla medium.'
		)
	)
	start_year = models.IntegerField(
		_('start year'),
		blank=True,
		null=True,
		validators=[MinValueValidator(1900), MaxValueValidator(3000)]
	)
	end_year = models.IntegerField(
		_('end year'),
		blank=True,
		null=True,
		validators=[MinValueValidator(1900), MaxValueValidator(3000)],
		help_text=_(
			'Can be kept empty if the person still has not completed studying.'
		)
	)
	identification_document_picture = models.URLField(
		_('identification document picture'),
		blank=True
	)
	
	# Copy of the fields
	copy = JSONField(
		_('copy'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder,
		help_text=_(
			'Stores a copy of all the academic background fields. Used to '
			'generate the timestamp of the latest time the tutor changed the '
			'academic background section of their profile.'
		)
	)

	# Check and timestamp
	is_complete = models.BooleanField(
		_('completion status'),
		default=False,
		help_text=_(
			'Set to True if all the background information is provided.'
		)
	)
	latest_change_timestamp = models.BigIntegerField(
		_('latest change timestamp'),
		blank=True,
		null=True,
		help_text=_(
			'Timestamp of the latest time the background informationw was '
			'changed.'
		)
	)

	def check_if_changed_or_completed(self):
		"""Generates the check and timestamp. Called before saving."""
		copy = {}
		now = arrow.utcnow().timestamp

		if field_is_not_null(self.institution_type):
			copy['institution_type'] = self.institution_type
		if field_is_not_null(self.country):
			copy['country'] = self.country.code
		if field_is_not_null(self.name_of_institution):
			copy['name_of_institution'] = self.name_of_institution
		if field_is_not_null(self.name_of_degree):
			copy['name_of_degree'] = self.name_of_degree
		if field_is_not_null(self.field_of_study):
			copy['field_of_study'] = self.field_of_study
		if field_is_not_null(self.medium):
			copy['medium'] = self.medium
		if field_is_not_null(self.bangla_medium_version):
			copy['bangla_medium_version'] = self.bangla_medium_version
		if field_is_not_null(self.english_medium_curriculum):
			copy[
				'english_medium_curriculum'
			] = self.english_medium_curriculum
		if field_is_not_null(self.start_year):
			copy['start_year'] = self.start_year
		if field_is_not_null(self.end_year):
			copy['end_year'] = self.end_year
		if field_is_not_null(self.identification_document_picture):
			copy[
				'identification_document_picture'
			] = self.identification_document_picture

		# Managing the check and timestamp
		if not self.pk:
			self.latest_change_timestamp = now
		else:
			# Checking if academic background information has changed
			if self.copy != copy:
				self.latest_change_timestamp = now

		# Checking if academic background information is complete or not
		if (field_is_not_null(self.country) and 
			field_is_not_null(self.name_of_institution) and 
			field_is_not_null(self.name_of_degree) and
			field_is_not_null(self.start_year) and
			field_is_not_null(self.identification_document_picture)):
			if self.country.code == 'BD':
				if (self.institution_type == 'school' or 
					self.institution_type == 'college'):
					if field_is_not_null(self.medium):
						if self.medium == 'bangla-medium':
							if field_is_not_null(self.bangla_medium_version):
								self.is_complete = True
							else:
								self.is_complete = False
						elif self.medium == 'english-medium':
							if field_is_not_null(
								self.english_medium_curriculum):
								self.is_complete = True
							else:
								self.is_complete = False
					else:
						self.is_complete = False
				else:
					self.is_complete = True
			else:
				self.is_complete = True
		else:
			self.is_complete = False

		# Start year needed only for university
		if self.institution_type == 'university':
			if field_is_not_null(self.start_year):
				self.is_complete = True
			else:
				self.is_complete = False

		self.copy = copy

	def save(self, *args, **kwargs):
		"""Method overridden to check if the academic background information
		has been changed or completed.
		"""
		self.check_if_changed_or_completed()
		super(AcademicBackground, self).save(*args, **kwargs)


class Tutor(CustomUser):
	"""Stores a tutor.

	Notes:
		- Only the personal information fields are stored in this table.
		- The academic background and the teaching preferences of the tutor 
		are stored in two different tables. 
	"""
	sign_up_channel = models.CharField(
		_('sign-up channel'),
		max_length=255,
		blank=True,
		choices=(
			('activation', 'Activation'),
			('campus-ambassador', 'Campus Ambassador'),
			('referral', 'Referral'),
			('direct', 'Direct')
		)
	)
	number_of_public_profile_views = models.BigIntegerField(
		_('number of public profile views'),
		default=0,
		validators=[MinValueValidator(0),]
	)

	# The following university related fields are passed to the academic 
	# background object on create
	undergraduate_university = models.ForeignKey(
		University,
		related_name='tutors_with_undergraduate_university',
		on_delete=models.CASCADE,
		verbose_name=_('undergraduate university')
	)
	undergraduate_university_id_number = models.CharField(
		_('undergraduate university id number'),
		max_length=255,
		blank=True
	)
	undergraduate_university_identification_document_picture = models.URLField(
		_('undergraduate university identification document picture'),
		blank=True
	)

	# Personal information fields (gender, date of birth, and display picture 
	# coming from the CustomUser)
	academic_medium = models.CharField(
		_('academic medium'),
		max_length=50,
		choices=(
			('english-medium', 'English medium'),
			('bangla-medium', 'Bangla medium')
		),
		blank=True,
		help_text=_('Only used in Bangladesh.')
	)
	academic_field_of_study = models.CharField(
		_('academic field of study'),
		max_length=120,
		choices=(
			('engineering', 'Engineering'),
			('business', 'Business'),
			('english', 'English'),
			('health-sciences', 'Health Sciences'),
			('law', 'Law'),
			('economics', 'Economics')
		),
		blank=True,
		help_text=_('Optional. Mainly used for filtering.')
	)
	about = models.TextField(
		_('describe yourself'),
		validators=[MinLengthValidator(150)],
		blank=True,
		help_text=_(
			'Write a short text to let everyone know why you are special. '
			'Minimum 150 characters.'
		)
	)
	home_area = models.ForeignKey(
		Area,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		verbose_name=_('home area'),
		related_name=_('tutors_with_home_area'),
		help_text=_('Select the area where you currently live.')
	)
	government_id_type = models.CharField(
		_('government ID type'),
		max_length=50,
		blank=True,
		choices=(
			('nid', 'NID'),
			('passport', 'Passport'),
			('driving-license', 'Driving license'),
			('birth-certificate', 'Birth certificate')
		),
		help_text=_('Select your identification document type.')
	)
	government_id_number = models.CharField(
		_('government ID number'),
		max_length=255,
		blank=True,
		help_text=_('Enter the unique number of your identification document.')
	)
	government_id_picture = models.URLField(
		_('government ID picture'),
		blank=True
	)

	# Copy of the personal information fields
	personal_information_copy = JSONField(
		_('personal information copy'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder,
		help_text=_(
			'Stores a copy of all the personal information fields. Used to '
			'generate the timestamp of the latest time the tutor changed the '
			'personal information section of their profile.'
		)
	)

	# Personal information check and timestamp
	is_personal_information_complete = models.BooleanField(
		_('personal information completion status'),
		default=False,
		help_text=_(
			'Set to True if the tutor has completed the personal information '
			'section of their profile.'
		)
	)
	latest_personal_information_change_timestamp = models.BigIntegerField(
		_('latest personal information change timestamp'),
		blank=True,
		null=True,
		help_text=_(
			'Timestamp of the latest time the tutor changed the personal '
			'information section of their profile.'
		)
	)

	# Academic backgrounds
	undergraduate_university_academic_bg = models.ForeignKey(
		AcademicBackground,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='tutors_with_undergraduate_university_academic_bg',
		verbose_name=_('undergraduate university academic background'),
	)
	school_academic_bg = models.ForeignKey(
		AcademicBackground,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='tutors_with_school_academic_bg',
		verbose_name=_('school academic background'),
	)
	college_academic_bg = models.ForeignKey(
		AcademicBackground,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='tutors_with_college_academic_bg',
		verbose_name=_('college academic background'),
		help_text=_('Only for use in Bangladesh.')
	)

	# Teaching preferences
	wants_to_teach_offline = models.BooleanField(
		_('wants to teach offline'),
		default=True,
		help_text=_(
			'Set to True if the tutor wants to teach offline tuitions.'
		)
	)
	offline_preferred_teaching_areas = models.ManyToManyField(
		Area,
		blank=True,
		related_name='tutors_with_offline_preferred_teaching_areas'
	)
	wants_to_teach_online = models.BooleanField(
		_('wants to teach online'),
		default=False,
		help_text=_(
			'Set to True if the tutor wants to teach online.'
		)
	)
	offline_preferred_teaching_subjects = models.ManyToManyField(
		OfflineSubject,
		blank=True,
		related_name='tutors_with_offline_preferred_teaching_subjects'
	)
	online_preferred_teaching_subjects = models.ManyToManyField(
		OnlineSubject,
		blank=True,
		related_name='tutors_with_online_preferred_teaching_subjects'
	)
	schedule = ArrayField(
		models.BooleanField(),
		size=21,
		default=get_empty_schedule_array
	)
	schedule_is_flexible = models.BooleanField(default=True)
	salary_range_start = models.DecimalField(
		_('salary range start'),
		max_digits=12,
		decimal_places=2,
		blank=True,
		null=True,
		help_text=_(
			'The currency is the same as the country of the tutor.'
		),
		validators=[MinValueValidator(0),]
	)
	salary_range_end = models.DecimalField(
		_('salary range end'),
		max_digits=12,
		decimal_places=2,
		blank=True,
		null=True,
		help_text=_(
			'The currency is the same as the country of the tutor.'
		),
		validators=[MinValueValidator(0),]
	)

	# Teaching preferences check
	is_teaching_preferences_complete = models.BooleanField(
		_('teaching preferences completion status'),
		default=False,
		help_text=_('Set to True if all the teaching preferences is provided.')
	)

	# Premium and job related fields
	account_type = models.CharField(
		_('account type'),
		max_length=50,
		default='basic',
		choices=(
			('basic', 'Basic'),
			('premium', 'Premium')
		)
	)
	date_till_premium_account_valid = models.DateTimeField(
		_('date till premium account valid'),
		blank=True,
		null=True
	)
	daily_direct_requests_accepted = JSONField(
		_('daily direct requests accepted'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder,
		help_text=_(
			'Stores a dictionary where the keys are days, and the values are '
			'the number of directed reqeusts accepted that day.'
		)
	)
	monthly_direct_requests_accepted = JSONField(
		_('monthly direct requests accepted'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder,
		help_text=_(
			'Stores a dictionary where the keys are months, and the values '
			'are the number of directed reqeusts accepted that month.'
		)
	)
	daily_hot_jobs_applied = JSONField(
		_('daily hot jobs applied'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder,
		help_text=_(
			'Stores a dictionary where the keys are days, and the values are '
			'the number of hot jobs the tutor applied to that day.'
		)
	)
	monthly_hot_jobs_applied = JSONField(
		_('monthly hot jobs applied'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder,
		help_text=_(
			'Stores a dictionary where the keys are months, and the values '
			'are the number of hot jobs the tutor applied to that month.'
		)
	)
	last_hot_job_received_at = models.DateTimeField(
		_('last hot job received at'),
		blank=True,
		null=True
	)

	# Review related fields
	tutor_behavior = models.BigIntegerField(
		_('tutor behavior'),
		default=0,
		validators=[MinValueValidator(0)]
	)
	way_of_teaching = models.BigIntegerField(
		_('way of teaching'),
		default=0,
		validators=[MinValueValidator(0)]
	)
	communication_skills = models.BigIntegerField(
		_('communication skills'),
		default=0,
		validators=[MinValueValidator(0)]
	)
	time_management = models.BigIntegerField(
		_('time management'),
		default=0,
		validators=[MinValueValidator(0)]
	)
	number_of_reviews = models.BigIntegerField(
		_('number of reviews'),
		default=0,
		validators=[MinValueValidator(0)]
	)

	# Other fields
	m2m_fields_serialized = JSONField(
		_('M2M fields serialized'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder
	)

	def check_if_personal_information_changed_or_completed(self):
		"""Validate the personal information and generate the check and 
		timestamp. Called before saving.
		"""
		personal_information_copy = {}
		now = arrow.utcnow().timestamp

		if field_is_not_null(self.academic_medium):
			personal_information_copy['academic_medium'] = self.academic_medium
		if field_is_not_null(self.academic_field_of_study):
			personal_information_copy[
				'academic_field_of_study'
			] = self.academic_field_of_study
		if field_is_not_null(self.gender):
			personal_information_copy['gender'] = self.gender
		if field_is_not_null(self.date_of_birth):
			personal_information_copy['date_of_birth'] = str(
				self.date_of_birth
			)
		if field_is_not_null(self.display_picture):
			personal_information_copy['display_picture'] = self.display_picture
		if field_is_not_null(self.about):
			personal_information_copy['about'] = self.about
		if field_is_not_null(self.home_area):
			personal_information_copy['home_area'] = self.home_area_id
		if field_is_not_null(self.government_id_type):
			personal_information_copy[
				'government_id_type'
			] = self.government_id_type
		if field_is_not_null(self.government_id_number):
			personal_information_copy[
				'government_id_number'
			] = self.government_id_number
		if field_is_not_null(self.government_id_picture):
			personal_information_copy[
				'government_id_picture'
			] = self.government_id_picture

		# Managing the check and timestamp
		if not self.pk:
			self.latest_personal_information_change_timestamp = now
		else:
			# Checking if personal information has changed
			if self.personal_information_copy != personal_information_copy:
				self.latest_personal_information_change_timestamp = now

		# Checking if personal information is complete or not
		if (field_is_not_null(self.gender) and 
			field_is_not_null(self.date_of_birth) and 
			field_is_not_null(self.display_picture) and 
			field_is_not_null(self.about) and 
			field_is_not_null(self.home_area) and 
			field_is_not_null(self.government_id_type) and 
			field_is_not_null(self.government_id_number) and 
			field_is_not_null(self.government_id_picture)):
			if self.country.code == 'BD':
				if field_is_not_null(self.academic_medium):
					self.is_personal_information_complete = True
				else:
					self.is_personal_information_complete = False
			else:
				self.is_personal_information_complete = True
		else:
			self.is_personal_information_complete = False

		self.personal_information_copy = personal_information_copy

	def check_if_teaching_preferences_completed(self):
		"""Validate the teaching preferences and generate the check."""
		if (field_is_not_null(self.salary_range_start) and 
			field_is_not_null(self.salary_range_end)):
			self.is_teaching_preferences_complete = True
		else:
			self.is_teaching_preferences_complete = False

	@transaction.atomic
	def save(self, *args, **kwargs):
		"""Method overridden to create the related academic backgrounds, and 
		update the completion status checks and timestamp.
		"""
		# Undergraduate university academic background
		if not field_is_not_null(self.undergraduate_university_academic_bg):
			ug_uni_academic_bg = AcademicBackground.objects.create(
				institution_type='university',
				name_of_institution=self.undergraduate_university.name,
				country=self.undergraduate_university.country,
				identification_document_picture=
				self.undergraduate_university_identification_document_picture
			)
			self.undergraduate_university_academic_bg = ug_uni_academic_bg

		# School academic background
		if not field_is_not_null(self.school_academic_bg):
			self.school_academic_bg = AcademicBackground.objects.create(
				institution_type='school'
			)

		# College academic background
		if not field_is_not_null(self.college_academic_bg):
			self.college_academic_bg = AcademicBackground.objects.create(
				institution_type='college'
			)

		# Completion checks and timestamp (only on create)
		if self.pk:
			self.check_if_personal_information_changed_or_completed()
			self.check_if_teaching_preferences_completed()

		super(Tutor, self).save(*args, **kwargs)

	@transaction.atomic
	def delete(self, *args, **kwargs):
		"""Method overridden to create the related academic backgrounds."""
		# Undergraduate university academic background
		if field_is_not_null(self.undergraduate_university_academic_bg):
			self.undergraduate_university_academic_bg.delete()

		# School academic background
		if field_is_not_null(self.school_academic_bg):
			self.school_academic_bg.delete()

		# College academic background
		if field_is_not_null(self.college_academic_bg):
			self.college_academic_bg.delete()

		super(Tutor, self).delete(*args, **kwargs)

	def get_jobs_left(self):
		"""Returns a dict of the jobs left for the tutor in that given day and 
		month.
		"""
		now = arrow.utcnow()
		current_date = now.format('DD-MM-YYYY')
		current_month = now.format('MM-YYYY')

		# Getting the currect values or zero if they don't exist
		daily_dr_accepted = self.daily_direct_requests_accepted.get(
			current_date, 0
		)
		daily_hj_applied = self.daily_hot_jobs_applied.get(
			current_date, 0
		)
		monthly_dr_accepted = self.monthly_direct_requests_accepted.get(
			current_month, 0
		)
		monthly_hj_applied = self.monthly_hot_jobs_applied.get(
			current_month, 0
		)

		# Making the calculations
		daily_dr_left = get_positive_or_zero(
			JOBS_LIMIT[self.account_type]['daily_direct_requests'] - 
			daily_dr_accepted
		)
		daily_hj_left = get_positive_or_zero(
			JOBS_LIMIT[self.account_type]['daily_hot_jobs'] - 
			daily_hj_applied
		)
		monthly_dr_left = get_positive_or_zero(
			JOBS_LIMIT[self.account_type]['monthly_direct_requests'] - 
			monthly_dr_accepted
		)
		monthly_hj_left = get_positive_or_zero(
			JOBS_LIMIT[self.account_type]['monthly_hot_jobs'] - 
			monthly_hj_applied
		)

		# Returning the result
		return {
			'current_date': current_date,
			'current_month': current_month,
			'daily_direct_requests_left': daily_dr_left,
			'daily_hot_jobs_left': daily_hj_left,
			'monthly_direct_requests_left': monthly_dr_left,
			'monthly_hot_jobs_left': monthly_hj_left
		}

	class Meta(CustomUser.Meta):
		ordering = ('last_hot_job_received_at', )


class Notification(models.Model):
	"""Stores a notification."""
	notification_type = models.CharField(
		_('notification type'),
		max_length=255,
		blank=True,
		help_text=_('Can be used to sort notifications into groups if needed.')
	)
	parent = models.ForeignKey(
		Parent,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='parent_notifications'
	)
	student = models.ForeignKey(
		Student,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='student_notifications'
	)
	tutor = models.ForeignKey(
		Tutor,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='tutor_notifications'
	)
	created_for = models.CharField(
		_('created for'),
		max_length=50,
		choices=(
			('parent', 'Parent'),
			('student', 'Student'),
			('tutor', 'Tutor')
		)
	)
	created_at = models.DateTimeField(_('created at'), auto_now_add=True)
	title = models.CharField(_('title'), max_length=255)
	body = models.TextField(_('body'))
	url = models.URLField(_('url'), blank=True)
	create_extra_notifications = models.BooleanField(
		default=False,
		help_text=_(
			'If this is True, extra notifications will be created during the '
			'save process. These include mobile app push notifications, '
			'emails, and text messages to the phone numbers of the users.'
		)
	)

	def __str__(self):
		return str(self.id)

	def handle_extra_notifications(self, target_user):
		"""Handles the extra notifications, such as sending SMS."""
		if target_user.country.code in SMS_SENDER_COUNTRY_MAP:
			SMS_SENDER_COUNTRY_MAP[target_user.country.code](
				target_user.phone_number,
				str(f'[Yoda] {self.title}\n{self.url}')
			)

	def save(self, *args, **kwargs):
		"""Method overridden to create and send the extra notifications."""
		if self.create_extra_notifications and not self.pk:
			if self.created_for == 'parent':
				target_user = self.parent
			elif self.created_for == 'student':
				target_user = self.student
			elif self.created_for == 'tutor':
				target_user = self.tutor
			else:
				return

			# Sending the SMS using a thread
			try:
				th = threading.Thread(
					target=self.handle_extra_notifications,
					args=(target_user,)
				)
				th.start()
			except Exception as e:
				pass

		super(Notification, self).save(*args, **kwargs)

	class Meta:
		ordering = ('-created_at',)


class BaseTuitionRequest(models.Model):
	"""Base tuition request."""
	uuid = models.UUIDField(
		_('UUID'),
		default=uuid.uuid4,
		unique=True,
		db_index=True
	)
	parent = models.ForeignKey(
		Parent,
		on_delete=models.CASCADE,
		related_name='%(app_label)s_%(class)s_related',
		verbose_name=_('parent')
	)
	created_at = models.DateTimeField(_('created at'), auto_now_add=True)
	note_by_parent = models.TextField(_('note by parent'), blank=True)

	# Student information
	student_gender = models.CharField(
		_('student gender'),
		max_length=50,
		choices=(
			('male', 'Male'),
			('female', 'Female')
		)
	)
	student_school = models.CharField(
		_('student school'),
		max_length=255,
		blank=True
	)
	student_class = models.CharField(
		_('student class'),
		max_length=255
	)
	student_medium = models.CharField(
		_('student medium'),
		max_length=50,
		choices=(
			('english-medium', 'English medium'),
			('bangla-medium', 'Bangla medium')
		),
		blank=True,
		help_text=_('Only used in Bangladesh.')
	)
	student_bangla_medium_version = models.CharField(
		_('student bangla medium version'),
		max_length=50,
		choices=(
			('english-version', 'English version'),
			('bangla-version', 'Bangla version')
		),
		blank=True,
		help_text=_(
			'Only used in Bangladesh. Can be empty if the school/college is '
			'english medium.'
		)
	)
	student_english_medium_curriculum = models.CharField(
		_('student english medium curriculum'),
		max_length=50,
		choices=(
			('edexcel', 'Edexcel'),
			('cambridge', 'Cambridge'),
			('ib', 'IB')
		),
		blank=True,
		help_text=_(
			'Only used in Bangladesh. Can be empty if the school/college is '
			'bangla medium.'
		)
	)
	tuition_area = models.ForeignKey(
		Area,
		on_delete=models.CASCADE,
		related_name='%(app_label)s_%(class)s_related',
		verbose_name=_('tuition area')
	)
	teaching_place_preference = models.CharField(
		_('teaching place preference'),
		max_length=50,
		choices=(
			('at-students-place', 'At student\'s place'),
			('at-tutors-place', 'At tutor\'s place')
		)
	)
	number_of_days_per_week = models.IntegerField(
		_('number of days per week'),
		validators=[MinValueValidator(1), MaxValueValidator(7)]
	)
	salary = models.DecimalField(
		_('salary'),
		max_digits=12,
		decimal_places=2,
		help_text=_('The currency is the same as the parent\'s country.')
	)
	is_salary_negotiable = models.BooleanField(
		_('is salary negotiable'),
		default=True
	)
	subjects = models.ManyToManyField(
		OfflineSubject,
		related_name='%(app_label)s_%(class)s_related'
	)

	# Ops related fields
	is_rejected_by_ops = models.BooleanField(
		_('ops rejection status'),
		default=False
	)
	confirmation_date = models.DateTimeField(
		_('confirmation date'),
		blank=True,
		null=True
	)
	ops_notes = JSONField(
		_('ops notes'),
		default=get_default_ops_notes,
		blank=True,
		encoder=DjangoJSONEncoder
	)
	country = CountryField(_('country'), default='BD')

	def __str__(self):
		return str(self.uuid)

	def save(self, *args, **kwargs):
		"""Method overridden to set the country to the parent's country."""
		self.country = self.parent.country
		super(BaseTuitionRequest, self).save(*args, **kwargs)

	class Meta:
		abstract = True
		ordering = ('-created_at',)


class RequestForTutor(BaseTuitionRequest):
	"""Stores a request for a tutor."""
	tutor_gender = models.CharField(
		_('tutor gender'),
		max_length=50,
		blank=True,
		choices=(
			('male', 'Male'),
			('female', 'Female')
		),
		help_text=_(
			'If there is no gender preference, this can be kept empty.'
		)
	)
	tutor_undergraduate_university = models.ForeignKey(
		University,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='%(app_label)s_%(class)s_related'
	)
	tutor_academic_medium = models.CharField(
		_('tutor academic medium'),
		max_length=50,
		choices=(
			('english-medium', 'English medium'),
			('bangla-medium', 'Bangla medium')
		),
		blank=True,
		help_text=_(
			'Only used in Bangladesh. If any medium is preferred, this can '
			'be kept empty.'
		)
	)
	tutor_academic_field_of_study = models.CharField(
		_('tutor academic field of study'),
		max_length=120,
		choices=(
			('engineering', 'Engineering'),
			('business', 'Business'),
			('english', 'English'),
			('health-sciences', 'Health Sciences'),
			('law', 'Law'),
			('economics', 'Economics')
		),
		blank=True,
		help_text=_('Optional. Mainly used for filtering.')
	)
	is_confirmed = models.BooleanField(_('confirmation status'), default=False)


class TuitionRequest(BaseTuitionRequest):
	"""Stores a tuition request."""
	status = models.CharField(
		_('status'),
		max_length=50,
		choices=(
			('direct-request', 'Direct request'),
			('hot-job', 'Hot job'),
			('in-process', 'In process'),
			('waiting-for-parent', 'Waiting for parent'),
			('waiting-for-tutor', 'Waiting for tutor'),
			('confirmed', 'Confirmed')
		)
	)
	is_rejected_by_tutor = models.BooleanField(
		_('tutor rejection status'),
		default=False
	)
	find_similar_tutors_for_parent = models.BooleanField(
		_('find similar tutors for parent'),
		default=True,
		help_text=_('Only needed for direct requests.')
	)
	tutor = models.ForeignKey(
		Tutor,
		on_delete=models.CASCADE,
		related_name='tutor_tuition_requests'
	)
	parent_rft = models.ForeignKey(
		RequestForTutor,
		on_delete=models.SET_NULL,
		related_name='tuition_requests',
		blank=True,
		null=True
	)
	notification_created = models.BooleanField(default=False)

	class Meta(BaseTuitionRequest.Meta):
		unique_together = ('tutor', 'parent_rft')


class Review(models.Model):
	"""Stores a review."""
	uuid = models.UUIDField(
		_('UUID'),
		default=uuid.uuid4,
		unique=True
	)
	parent = models.ForeignKey(
		Parent,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='parent_reviews'
	)
	student = models.ForeignKey(
		Parent,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='student_reviews'
	)
	tutor = models.ForeignKey(
		Tutor,
		on_delete=models.CASCADE,
		related_name='tutor_reviews'
	)
	tuition_request = models.ForeignKey(
		TuitionRequest,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		help_text=_(
			'Optional. A review can be associated with a particular tuition '
			'request if needed.'
		)
	)
	reviewed_by = models.CharField(
		_('reviewed by'),
		max_length=50,
		choices=(
			('parent', 'Parent'),
			('student', 'Student')
		)
	)
	created_at = models.DateTimeField(_('created at'), auto_now_add=True)
	tutor_behavior = models.IntegerField(
		_('tutor behavior'),
		choices=(
			(1, 1),
			(2, 2),
			(3, 3),
			(4, 4),
			(5, 5)
		),
		validators=[MinValueValidator(1), MaxValueValidator(5)]
	)
	way_of_teaching = models.IntegerField(
		_('way of teaching'),
		choices=(
			(1, 1),
			(2, 2),
			(3, 3),
			(4, 4),
			(5, 5)
		),
		validators=[MinValueValidator(1), MaxValueValidator(5)]
	)
	communication_skills = models.IntegerField(
		_('communication skills'),
		choices=(
			(1, 1),
			(2, 2),
			(3, 3),
			(4, 4),
			(5, 5)
		),
		validators=[MinValueValidator(1), MaxValueValidator(5)]
	)
	time_management = models.IntegerField(
		_('time management'),
		choices=(
			(1, 1),
			(2, 2),
			(3, 3),
			(4, 4),
			(5, 5)
		),
		validators=[MinValueValidator(1), MaxValueValidator(5)]
	)
	copy = JSONField(
		_('copy'),
		default=dict,
		blank=True,
		encoder=DjangoJSONEncoder,
		help_text=_('Stores a copy of all the scores.')
	)

	def __str__(self):
		return str(self.uuid)

	@transaction.atomic
	def check_if_changed_and_update_tutor(self):
		"""Checks if the review has been changed and updates the tutor."""
		copy = {}

		if field_is_not_null(self.tutor_behavior):
			copy['tutor_behavior'] = self.tutor_behavior
		if field_is_not_null(self.way_of_teaching):
			copy['way_of_teaching'] = self.way_of_teaching
		if field_is_not_null(self.communication_skills):
			copy['communication_skills'] = self.communication_skills
		if field_is_not_null(self.time_management):
			copy['time_management'] = self.time_management

		if not self.pk:
			self.tutor.number_of_reviews += 1
			self.tutor.tutor_behavior += self.tutor_behavior
			self.tutor.way_of_teaching += self.way_of_teaching
			self.tutor.communication_skills += self.communication_skills
			self.tutor.time_management += self.time_management
			self.tutor.save()
		else:
			if self.copy != copy:
				self.tutor.tutor_behavior -= self.copy['tutor_behavior']
				self.tutor.way_of_teaching -= self.copy['way_of_teaching']
				self.tutor.communication_skills -= self.copy[
					'communication_skills'
				]
				self.tutor.time_management -= self.copy['time_management']

				self.tutor.tutor_behavior += self.tutor_behavior
				self.tutor.way_of_teaching += self.way_of_teaching
				self.tutor.communication_skills += self.communication_skills
				self.tutor.time_management += self.time_management
				self.tutor.save()

		self.copy = copy

	def clean(self):
		"""Method overridden to check if the review has been changed and 
		update the tutor.
		"""
		self.check_if_changed_and_update_tutor()
		super(Review, self).clean()

	@transaction.atomic
	def delete(self, *args, **kwargs):
		"""Method overridden to update the tutor."""
		self.tutor.number_of_reviews -= 1
		self.tutor.tutor_behavior -= self.tutor_behavior
		self.tutor.way_of_teaching -= self.way_of_teaching
		self.tutor.communication_skills -= self.communication_skills
		self.tutor.time_management -= self.time_management
		self.tutor.save()
		super(Review, self).delete(*args, **kwargs)


class Transaction(models.Model):
	"""Stores a transaction."""
	uuid = models.UUIDField(
		_('UUID'),
		default=uuid.uuid4,
		unique=True,
		db_index=True
	)
	parent = models.ForeignKey(
		Parent,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='parent_transactions'
	)
	student = models.ForeignKey(
		Student,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='student_transactions'
	)
	tutor = models.ForeignKey(
		Tutor,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='tutor_transactions'
	)
	created_for = models.CharField(
		_('created for'),
		max_length=50,
		choices=(
			('parent', 'Parent'),
			('student', 'Student'),
			('tutor', 'Tutor')
		)
	)
	created_at = models.DateTimeField(_('created at'), auto_now_add=True)
	total_amount = models.DecimalField(
		_('total amount'),
		max_digits=12,
		decimal_places=2
	)
	amount_retained_by_yoda = models.DecimalField(
		_('amount retained by Yoda'),
		max_digits=12,
		decimal_places=2
	)
	currency = models.CharField(_('currency'), max_length=50)
	trx_id = models.CharField(_('trx id'), max_length=50)
	title = models.CharField(_('title'), max_length=255)
	body = models.TextField(_('body'))
	url = models.URLField(_('url'), blank=True)
	vendor_name = models.CharField(
		_('vendor name'),
		max_length=255,
		blank=True
	)

	def __str__(self):
		return str(self.uuid)

	class Meta:
		ordering = ('-created_at',)

