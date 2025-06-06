from django.urls import path

from management.views import AdminAPIView, AttendanceAPIView, AttendanceFileAPIView, AttendanceFileDownloadAPIView, AttendanceReportAPIView, DataFechEvenUnitIdAPIView, EventsAPIView, LocationAPIView, LoginAPIView, RegisterAPIView, TotalCountAPIView, UnitAPIView, UploadFileExtractTextAPIView, UploadVolunteerExcelView, VerifyOTPAPIView, VolunteerAPIView, VolunteersByUnitPostAPIView, VolunteersReportAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register-unit'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
    
    path('login/', LoginAPIView.as_view(), name='login'),
    
    
    
    path('events/', EventsAPIView.as_view(), name='events-api'),
    path('events/<str:event_id>/', EventsAPIView.as_view()),
    
    # path('locations/count/', LocationCountAPIView.as_view(), name='total-location-count'),
    path('locations/', LocationAPIView.as_view(), name='location-api'),
    path('locations/<str:location_id>/', LocationAPIView.as_view()),
    
    # path('units/count/', UnitCountAPIView.as_view(), name='total-unit-count'),
    path('units/', UnitAPIView.as_view(), name='unit-api'),
    path('units/<str:unit_id>/', UnitAPIView.as_view()),
    
    # path ('volinteers/count/', VolunteerCountAPIVIew.as_view(), name='total-volunteer-count'),
    path('volinteers/', VolunteerAPIView.as_view(), name='volunteer-api'),
    path('volinteers/<str:volunteer_id>/', VolunteerAPIView.as_view()),
    path('volinteers/upload-file/<str:unit_id>/', UploadVolunteerExcelView.as_view(), name='upload-file'), 
    
    path('admins/', AdminAPIView.as_view(), name='admin-api'),
    path('admins/<str:admin_id>/', AdminAPIView.as_view()),
    
    path('attendance/', AttendanceAPIView.as_view(), name='attendance-api'),
    path('attendance/<str:attendance_id>/', AttendanceAPIView.as_view()),
    
    path('attendance-files/', AttendanceFileAPIView.as_view(), name='attendance-file-api'),
    path('attendance-file/<str:attendance_file_id>/', AttendanceFileAPIView.as_view()),
    
    path('total-count/', TotalCountAPIView.as_view(), name='total-count-api'),
    
    path ('event-unit-attendance/', DataFechEvenUnitIdAPIView.as_view(), name='event-unit-attendance-api'),
    
    path('download-file/', AttendanceFileDownloadAPIView.as_view(), name='download-file-api'),
    
    path('volunteers-by-unit/', VolunteersByUnitPostAPIView.as_view(), name='volunteers-by-unit-post'),
    
    # path('upload-image-stats/', UploadVolunteerImageStatsView.as_view(), name='upload-image-stats'),
    path('extract-table/', UploadFileExtractTextAPIView.as_view(), name='extract-table-api'),
    
    path('volunteer-report/', VolunteersReportAPIView.as_view(), name='volunteer-report-api'),
    
    path('attendance-report/', AttendanceReportAPIView.as_view()),
    path('attendance-report/<str:event_id>/', AttendanceReportAPIView.as_view(), name='attendance-report-api'),

    
       
]
