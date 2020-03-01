import jwt
import uuid

from .env_variables_manager import get_main_api_key, get_auth_jwt_secret
from .models import *

# Permissions

class BasePermission(object):
	"""Base permission extended by other permissions."""
	def has_permission(self, request, view):
		return True

	def has_object_permission(self, request, view, obj):
		return True


class CorrectAPIKeyPermission(BasePermission):
	"""Returns True if the user is an admin (with access to the API), and/or
	the request has the correct API key.
	"""
	def has_permission(self, request, view):
		if request.META.get('HTTP_X_API_KEY') == get_main_api_key():
			return True

		if not request.user.is_authenticated:
			return False

		if request.user.is_superuser:
			return True

		return False


class UserPermission(BasePermission):
	"""JWT based auth permission for parents, tutors, and students."""

	def get_parent(self, payload):
		return Parent.objects.get(
			uuid=uuid.UUID(payload['uuid']),
			is_suspended_by_ops=False,
			is_deleted=False
		)

	def get_student(self, payload):
		return Student.objects.get(
			uuid=uuid.UUID(payload['uuid']),
			is_suspended_by_ops=False,
			is_deleted=False
		)

	def get_tutor(self, payload):
		return Tutor.objects.get(
			uuid=uuid.UUID(payload['uuid']),
			is_suspended_by_ops=False,
			is_deleted=False
		)

	def has_permission(self, request, view):
		if request.user.is_authenticated:
			if request.user.is_superuser:
				return True

		if request.META.get('HTTP_X_API_KEY') == get_main_api_key():
			try:
				# Decode the payload
				payload = jwt.decode(
					request.META.get('HTTP_AUTH_JWT'),
					get_auth_jwt_secret()
				)

				# If user is a parent
				if payload['user_type'] == 'parent':
					view.user = self.get_parent(payload)
					view.user.update_mobile_user_id(
						request.META.get('HTTP_MOBILE_USER_ID')
					)
					view.user.active_daily() # Saves if required
					return True

				# If user is a student
				elif payload['user_type'] == 'student':
					view.user = self.get_student(payload)
					view.user.update_mobile_user_id(
						request.META.get('HTTP_MOBILE_USER_ID')
					)
					view.user.active_daily() # Saves if required
					return True

				# If user is a tutor
				elif payload['user_type'] == 'tutor':
					view.user = self.get_tutor(payload)
					view.user.update_mobile_user_id(
						request.META.get('HTTP_MOBILE_USER_ID')
					)
					view.user.active_daily() # Saves if required
					return True

				# Otherwise, return False
				else:
					return False

			except Exception as e:
				# If something goes wrong, return False
				return False
		else:
			return False

		return False


class UserPermissionTutorSelectRelated(UserPermission):
	"""Extended UserPermission where related objects for the tutor is returned
	for faster loads.
	"""
	def get_tutor(self, payload):
		return Tutor.objects.select_related(
			'undergraduate_university_academic_bg', 'school_academic_bg',
			'college_academic_bg'
		).get(
			uuid=uuid.UUID(payload['uuid']),
			is_suspended_by_ops=False,
			is_deleted=False
		)


class OpsPermission(BasePermission):
	"""JWT based auth permission for operations team, and admin."""
	def get_accepted_user_types(self):
		return ['operations', 'admin']

	def has_permission(self, request, view):
		if request.user.is_authenticated:
			if request.user.is_superuser:
				return True

		if request.META.get('HTTP_X_API_KEY') == get_main_api_key():
			try:
				# Decode the payload
				payload = jwt.decode(
					request.META.get('HTTP_AUTH_JWT'),
					get_auth_jwt_secret()
				)

				# Get the account
				view.account = Account.objects.select_related(
					'user', 'university'
				).get(id=payload['id'])

				# Check if the user type is acceptable or not
				if view.account.account_type in self.get_accepted_user_types():
					return True
				else:
					return False

			except Exception as e:
				return False
		else:
			return False

		return False


class ActivationManagerPermission(OpsPermission):
	"""JWT based auth permission for activation manager."""
	def get_accepted_user_types(self):
		return ['activation-manager', 'admin']


class CampusAmbassadorPermission(OpsPermission):
	"""JWT based auth permission for campus ambassadors."""
	def get_accepted_user_types(self):
		return ['campus-ambassador']

