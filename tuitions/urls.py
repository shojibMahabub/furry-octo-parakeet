from django.conf.urls import url
from . import views

uuid_regex_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-(8|9|a|b|A|B)[0-9a-fA-F]{3}-[0-9a-fA-F]{12}'

urlpatterns = [
	url(r'^test/$', views.Test.as_view()),

	url(r'^$', views.Index.as_view()),

	# Sign up URLs
	url(r'^parent-sign-up/$', views.ParentSignUp.as_view()),
	url(r'^student-sign-up/$', views.StudentSignUp.as_view()),

	# Login set OTP URLs
	url(r'^parent-login-set-otp/$', views.ParentLoginSetOTP.as_view()),
	url(r'^student-login-set-otp/$', views.StudentLoginSetOTP.as_view()),
	url(r'^tutor-login-set-otp/$', views.TutorLoginSetOTP.as_view()),

	# Login confirm OTP URLs
	url(r'^parent-login-confirm-otp/$', views.ParentLoginConfirmOTP.as_view()),
	url(r'^student-login-confirm-otp/$', views.StudentLoginConfirmOTP.as_view()),
	url(r'^tutor-login-confirm-otp/$', views.TutorLoginConfirmOTP.as_view()),

	# User details URLs
	url(r'^parent-details/$', views.ParentDetails.as_view()),
	url(r'^student-details/$', views.StudentDetails.as_view()),
	url(r'^tutor-details/$', views.TutorDetails.as_view()),

	# Tutor profile URLs
	url(r'^tutor-personal-information/$', views.TutorPersonalInformation.as_view()),
	url(r'^tutor-teaching-preferences/$', views.TutorTeachingPreferences.as_view()),
	url(r'^tutor-academic-background/$', views.TutorAcademicBackground.as_view()),

	# Area, subject, school, and university field of study list view URLs
	url(r'^(?P<country>[_a-zA-Z]+)/area-list/$', views.AreaList.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/offline-subject-list/$', views.OfflineSubjectList.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/offline-subject-list/(?P<subject_type>[_a-zA-Z0-9]+)/$', views.OfflineSubjectList.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/school-list/$', views.SchoolList.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/university-list/$', views.UniversityList.as_view()),
	url(r'^university-field-of-study-list/$', views.UniversityFieldOfStudyList.as_view()),
	url(r'^university-degree-list/$', views.UniversityDegreeList.as_view()),

	# Tutor filter URL
	url(r'^(?P<country>[_a-zA-Z]+)/tutor-filter/$', views.TutorFilter.as_view()),

	# Tutor public view URLs
	url(r'^tutor-public-details/(?P<tutor_uuid>'+uuid_regex_pattern+r')/$', views.TutorPublicDetails.as_view()),
	url(r'^tutor-public-add-view/(?P<tutor_uuid>'+uuid_regex_pattern+r')/$', views.TutorPublicAddView.as_view()),

	# Jobs URLs
	url(r'^rft-create/$', views.RequestForTutorCreate.as_view()),
	url(r'^rft-list/$', views.RequestForTutorList.as_view()),
	url(r'^rft-details/(?P<rft_uuid>'+uuid_regex_pattern+r')/$', views.RequestForTutorDetails.as_view()),

	url(r'^direct-request-create/(?P<tutor_uuid>'+uuid_regex_pattern+r')/$', views.DirectRequestCreate.as_view()),
	url(r'^parent-tuition-request-list/(?P<status>direct-request|hot-job|in-process|confirmed)/$', views.ParentTuitionRequestList.as_view()),
	url(r'^tutor-tuition-request-list/(?P<status>direct-request|hot-job|in-process|confirmed)/$', views.TutorTuitionRequestList.as_view()),
	url(r'^parent-tuition-request-details/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.ParentTuitionRequestDetails.as_view()),
	url(r'^tutor-tuition-request-details/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.TutorTuitionRequestDetails.as_view()),
	url(r'^accept-direct-request/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.AcceptDirectRequest.as_view()),
	url(r'^apply-to-hot-job/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.ApplyToHotJob.as_view()),
	url(r'^tutor-reject-tuition-request/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.TutorRejectTuitionRequest.as_view()),
	url(r'^tutor-confirm-tuition-request/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.TutorConfirmTuitionRequest.as_view()),
	url(r'^parent-confirm-tuition-request/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.ParentConfirmTuitionRequest.as_view()),

	# Notification URLs
	url(r'^parent-notification-list/$', views.ParentNotificationList.as_view()),
	url(r'^student-notification-list/$', views.StudentNotificationList.as_view()),
	url(r'^tutor-notification-list/$', views.TutorNotificationList.as_view()),
	url(r'^parent-read-notification/(?P<notification_id>[0-9]+)/$', views.ParentReadNotification.as_view()),
	url(r'^student-read-notification/(?P<notification_id>[0-9]+)/$', views.StudentReadNotification.as_view()),
	url(r'^tutor-read-notification/(?P<notification_id>[0-9]+)/$', views.TutorReadNotification.as_view()),

	# Transaction URLs
	url(r'^parent-transaction-list/$', views.ParentTransactionList.as_view()),
	url(r'^student-transaction-list/$', views.StudentTransactionList.as_view()),
	url(r'^tutor-transaction-list/$', views.TutorTransactionList.as_view()),

	# Ops related URLs
	url(r'^ops-login/$', views.OpsLogin.as_view()),

	# Sign up URLs
	url(r'^ops-parent-sign-up/$', views.OpsParentSignUp.as_view()),
	url(r'^ops-student-sign-up/$', views.OpsStudentSignUp.as_view()),
	url(r'^activation-tutor-sign-up/$', views.ActivationTutorSignUp.as_view()),
	url(r'^campus-ambassador-tutor-sign-up/$', views.CampusAmbassadorTutorSignUp.as_view()),

	# List view URLs
	url(r'^(?P<country>[_a-zA-Z]+)/ops-parent-list/$', views.OpsParentList.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-student-list/$', views.OpsStudentList.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-tutor-list/$', views.OpsTutorList.as_view()),

	# Details view URLs
	url(r'^ops-parent-details/(?P<user_uuid>'+uuid_regex_pattern+r')/$', views.OpsParentDetails.as_view()),
	url(r'^ops-student-details/(?P<user_uuid>'+uuid_regex_pattern+r')/$', views.OpsStudentDetails.as_view()),
	url(r'^ops-tutor-details/(?P<user_uuid>'+uuid_regex_pattern+r')/$', views.OpsTutorDetails.as_view()),

	# Filter view URLs
	url(r'^(?P<country>[_a-zA-Z]+)/ops-parent-filter/$', views.OpsParentFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-student-filter/$', views.OpsStudentFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-tutor-filter/$', views.OpsTutorFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-parent-filter/(?P<get_all>get-all)/$', views.OpsParentFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-student-filter/(?P<get_all>get-all)/$', views.OpsStudentFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-tutor-filter/(?P<get_all>get-all)/$', views.OpsTutorFilter.as_view()),

	# Verification view URLs
	url(r'^ops-change-parent-verification/(?P<user_uuid>'+uuid_regex_pattern+r')/(?P<new_ops_verification_status>verify|unverify)/$', views.OpsChangeParentVerification.as_view()),
	url(r'^ops-change-student-verification/(?P<user_uuid>'+uuid_regex_pattern+r')/(?P<new_ops_verification_status>verify|unverify)/$', views.OpsChangeStudentVerification.as_view()),
	url(r'^ops-change-tutor-verification/(?P<user_uuid>'+uuid_regex_pattern+r')/(?P<new_ops_verification_status>verify|unverify)/$', views.OpsChangeTutorVerification.as_view()),

	# Job view URLs
	url(r'^ops-rft-create/$', views.OpsRequestForTutorCreate.as_view()),
	url(r'^ops-rft-details/(?P<job_uuid>'+uuid_regex_pattern+r')/$', views.OpsRequestForTutorDetails.as_view()),
	url(r'^ops-tuition-request-details/(?P<job_uuid>'+uuid_regex_pattern+r')/$', views.OpsTuitionRequestDetails.as_view()),
	url(r'^ops-change-rft-rejection/(?P<job_uuid>'+uuid_regex_pattern+r')/(?P<new_ops_rejection_status>reject|unreject)/$', views.OpsChangeRequestForTutorRejection.as_view()),
	url(r'^ops-change-tuition-request-rejection/(?P<job_uuid>'+uuid_regex_pattern+r')/(?P<new_ops_rejection_status>reject|unreject)/$', views.OpsChangeTuitionRequestRejection.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-rft-filter/$', views.OpsRequestForTutorFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-rft-filter/(?P<get_all>get-all)/$', views.OpsRequestForTutorFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-tuition-request-filter/$', views.OpsTuitionRequestFilter.as_view()),
	url(r'^(?P<country>[_a-zA-Z]+)/ops-tuition-request-filter/(?P<get_all>get-all)/$', views.OpsTuitionRequestFilter.as_view()),
	url(r'^ops-rft-to-hot-job/(?P<rft_uuid>'+uuid_regex_pattern+r')/$', views.OpsRftToHotJob.as_view()),
	url(r'^ops-parent-confirm-tuition-request/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.OpsParentConfirmTuitionRequest.as_view()),

	# Add ops note view URLs
	url(r'^add-ops-note/parent/(?P<obj_uuid>'+uuid_regex_pattern+r')/$', views.ParentAddOpsNote.as_view()),
	url(r'^add-ops-note/student/(?P<obj_uuid>'+uuid_regex_pattern+r')/$', views.StudentAddOpsNote.as_view()),
	url(r'^add-ops-note/tutor/(?P<obj_uuid>'+uuid_regex_pattern+r')/$', views.TutorAddOpsNote.as_view()),
	url(r'^add-ops-note/rft/(?P<obj_uuid>'+uuid_regex_pattern+r')/$', views.RequestForTutorAddOpsNote.as_view()),
	url(r'^add-ops-note/tuition-request/(?P<obj_uuid>'+uuid_regex_pattern+r')/$', views.TuitionRequestAddOpsNote.as_view()),

	# Review view URLs
	url(r'^parent-review-list/$', views.ParentReviewList.as_view()),
	url(r'^tutor-review-list/$', views.TutorReviewList.as_view()),
	url(r'^ops-review-list/$', views.OpsReviewList.as_view()),
	url(r'^parent-review-details/(?P<review_uuid>'+uuid_regex_pattern+r')/$', views.ParentReviewDetails.as_view()),
	url(r'^tutor-review-details/(?P<review_uuid>'+uuid_regex_pattern+r')/$', views.TutorReviewDetails.as_view()),
	url(r'^ops-review-details/(?P<review_uuid>'+uuid_regex_pattern+r')/$', views.OpsReviewDetails.as_view()),
	url(r'^parent-review-create/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.ParentReviewCreate.as_view()),
	url(r'^ops-review-create/(?P<tuition_request_uuid>'+uuid_regex_pattern+r')/$', views.OpsReviewCreate.as_view()),

	# Upgrade to premium and payment view URLs
	url(r'^upgrade-tutor-to-premium-with-points/$', views.UpgradeTutorToPremiumWithPoints.as_view()),
	url(r'^ops-upgrade-tutor-to-premium/(?P<tutor_uuid>'+uuid_regex_pattern+r')/$', views.OpsUpgradeTutorToPremium.as_view()),
	url(r'^bkash-create-payment/$', views.BkashCreatePayment.as_view()),
	url(r'^bkash-execute-payment/$', views.BkashExecutePayment.as_view()),

	# Hot jobs list from RFT view URLs
	url(r'^parent-hot-jobs-list-from-rft/(?P<rft_uuid>'+uuid_regex_pattern+r')/$', views.ParentHotJobsListFromRFT.as_view()),
	url(r'^ops-hot-jobs-list-from-rft/(?P<rft_uuid>'+uuid_regex_pattern+r')/$', views.OpsHotJobsListFromRFT.as_view()),

	# SMS sender view URLs
	url(r'^ops-send-sms-to-parent/$', views.OpsSendSMSToParent.as_view()),
	url(r'^ops-send-sms-to-student/$', views.OpsSendSMSToStudent.as_view()),
	url(r'^ops-send-sms-to-tutor/$', views.OpsSendSMSToTutor.as_view()),

	# Ops tutor transaction list URLs
	url(r'^ops-tutor-transaction-list-all/$', views.OpsTutorTransactionListAll.as_view()),
	url(r'^ops-tutor-transaction-list/(?P<tutor_uuid>'+uuid_regex_pattern+r')/$', views.OpsTutorTransactionList.as_view()),

	# Ops SMS log list URLs
	url(r'^ops-parent-sms-log-list/(?P<user_uuid>'+uuid_regex_pattern+r')/$', views.OpsParentSMSLogList.as_view()),
	url(r'^ops-student-sms-log-list/(?P<user_uuid>'+uuid_regex_pattern+r')/$', views.OpsStudentSMSLogList.as_view()),
	url(r'^ops-tutor-sms-log-list/(?P<user_uuid>'+uuid_regex_pattern+r')/$', views.OpsTutorSMSLogList.as_view()),

	# Tutor slug to UUID
	url(r'^tutor-slug-to-uuid/(?P<tutor_slug>[0-9a-zA-Z-]+)/$', views.TutorSlugToUUID.as_view()),

	# Make bkash payment using app URL
	url(r'^make-bkash-payment-using-app/$', views.make_bkash_payment_using_app),

]

