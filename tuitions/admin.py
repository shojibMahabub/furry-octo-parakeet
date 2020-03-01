from django.contrib import admin
from django.contrib.admin.models import LogEntry
from solo.admin import SingletonModelAdmin

from .models import *


# Setting up admin site titles

admin.site.site_title = 'Yoda admin'
admin.site.site_header = 'Yoda admin'
admin.site.index_title = 'Yoda admin'


# Admin model registrations

admin.site.register(LogEntry)
admin.site.register(SiteConfig, SingletonModelAdmin)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
	list_display = ('user', 'account_type')
	search_fields = (
		'account_type', 'user__username', 'user__email'
	)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'city', 'zip_code', 'country')
	search_fields = ('name', 'city', 'zip_code', 'country')


@admin.register(OfflineSubject)
@admin.register(OnlineSubject)
class SubjectAdmin(admin.ModelAdmin):
	list_display = (
		'id', 'name', 'category', 'sub_category', 'english_medium_curriculum',
		'country'
	)
	search_fields = ('name', 'category', 'sub_category', 'country')

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'country')
	search_fields = ('name', 'country')


@admin.register(UniversityFieldOfStudy)
class UniversityFieldOfStudyAdmin(admin.ModelAdmin):
	list_display = ('id', 'name',)
	search_fields = ('name',)


@admin.register(UniversityDegree)
class UniversityDegreeAdmin(admin.ModelAdmin):
	list_display = ('id', 'name',)
	search_fields = ('name',)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'country')
	search_fields = ('name', 'country')


@admin.register(Parent)
@admin.register(Student)
class ParentAndStudentAdmin(admin.ModelAdmin):
	list_display = (
		'uuid', 'full_name', 'phone_number', 'is_phone_number_verified',
		'is_verified_by_ops', 'country'
	)
	search_fields = ('uuid', 'full_name', 'phone_number', 'country')


admin.site.register(AcademicBackground)


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
	list_display = (
		'uuid', 'full_name', 'phone_number', 'is_phone_number_verified',
		'is_verified_by_ops', 'country', 'undergraduate_university',
		'academic_medium'
	)
	search_fields = ('uuid', 'full_name', 'phone_number', 'country',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = (
		'title', 'created_for', 'created_at'
	)
	search_fields = ('title', 'created_for')


@admin.register(RequestForTutor)
class RequestForTutorAdmin(admin.ModelAdmin):
	list_display = (
		'uuid', 'created_at', 'tuition_area', 'salary', 'tutor_gender',
		'tutor_undergraduate_university', 'tutor_academic_medium'
	)
	search_fields = (
		'uuid', 'tuition_area', 'tutor_undergraduate_university',
		'tutor_academic_medium',
	)


@admin.register(TuitionRequest)
class TuitionRequestAdmin(admin.ModelAdmin):
	list_display = (
		'uuid', 'status', 'is_rejected_by_tutor', 'created_at',
		'tuition_area', 'salary',
	)
	search_fields = ('uuid', 'status', 'tuition_area')


@admin.register(Review)
class ReviewModelAdmin(admin.ModelAdmin):
	list_display = (
		'uuid', 'tutor', 'created_at', 'tutor_behavior', 'way_of_teaching',
		'communication_skills', 'time_management',
	)
	search_fields = ('uuid',)


@admin.register(Transaction)
class TransactionModelAdmin(admin.ModelAdmin):
	list_display = (
		'uuid', 'created_for', 'created_at', 'total_amount', 'currency',
		'trx_id', 'vendor_name'
	)
	search_fields = ('uuid', 'created_for', 'trx_id', 'vendor_name')


admin.site.register(SMSLog)

