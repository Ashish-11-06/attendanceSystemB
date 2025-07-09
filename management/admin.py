from django.contrib import admin

from management.models import Admin, Attendance, AttendanceFile, EventUnitLocation, Events, Khetra, Location, Register, Unit, Volunteer

# Register your models here.

admin.site.register(Register)
admin.site.register(Events)
admin.site.register(Unit)
admin.site.register(Location)
admin.site.register(Volunteer)
admin.site.register(Admin)
admin.site.register(Attendance)
admin.site.register(AttendanceFile)
admin.site.register(EventUnitLocation)
admin.site.register(Khetra)





