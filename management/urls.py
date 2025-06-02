from django.urls import path


from management.views import AdminAPIView, AttendanceAPIView, AttendanceFileAPIView, EventsAPIView, LocationAPIView, UnitAPIView, VolunteerAPIView

urlpatterns = [
    path('events/', EventsAPIView.as_view(), name='events-api'),
    path('events/<int:event_id>/', EventsAPIView.as_view()),
    

    path('locations/', LocationAPIView.as_view(), name='location-api'),
    path('locations/<int:location_id>/', LocationAPIView.as_view()),
    
    path('units/', UnitAPIView.as_view(), name='unit-api'),
    path('units/<int:unit_id>/', UnitAPIView.as_view()),
    
    path('volunteers/', VolunteerAPIView.as_view(), name='volunteer-api'),
    path('volunteers/<int:volunteer_id>/', VolunteerAPIView.as_view()),
    
    path('admins/', AdminAPIView.as_view(), name='admin-api'),
    path('admins/<int:admin_id>/', AdminAPIView.as_view()),
    
    path('attendance/', AttendanceAPIView.as_view(), name='attendance-api'),
    path('attendance/<int:attendance_id>/', AttendanceAPIView.as_view()),
    
    path('attendance-files/', AttendanceFileAPIView.as_view(), name='attendance-file-api'),

]
