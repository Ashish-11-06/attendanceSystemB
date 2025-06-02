from django.db import models
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password


class Events(models.Model):
    event_id = models.IntegerField()
    event_name = models.CharField(max_length=250)
    location = models.ForeignKey('management.Location', on_delete=models.CASCADE, null=True)
    date = models.DateField()
    time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event_name} - {self.event_id} "
    
class Location(models.Model):
    location_id = models.IntegerField()
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.state} - {self.location_id} "
    
class Unit(models.Model):
    unit_id = models.IntegerField()
    unit_name = models.CharField(max_length=250)
    password = models.CharField(max_length=250)   
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True)
    
    def __str__(self):
        return f"{self.unit_name} - {self.unit_id} "
    
    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
class Volunteer(models.Model):
    volunteer_id = models.IntegerField()
    name = models.CharField(max_length=250)
    email = models.EmailField(max_length=254, null=True, blank=True)
    old_personal_number = models.CharField(max_length=255, null=True, blank=True)
    new_personal_number = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ])
    unit = models.ForeignKey('management.Unit', on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.volunteer_id} "
    
class Admin(models.Model):
    admin_id = models.IntegerField()
    name = models.CharField(max_length=250)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=250)
    
    def __str__(self):
        return f"{self.name} - {self.admin_id} "
    
    def save(self, *args, **kwargs):
        # If password is not hashed yet, hash it
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
class Attendance(models.Model):
    atd_id = models.IntegerField()
    volunteer = models.ForeignKey('management.Volunteer', on_delete=models.CASCADE, null=True)
    event = models.ForeignKey('management.Events', on_delete=models.CASCADE, null=True)
    date = models.DateField()
    in_time = models.TimeField()
    out_time = models.TimeField(null=True, blank=True)
    present = models.BooleanField(default=False)
    absent = models.BooleanField(default=False)
    remark = models.CharField(max_length=250, null=True, blank=True)
    
    def __str__(self):
        return f" {self.date} "
    
    def save(self, *args, **kwargs):
        # Automatically manage mutually exclusive present/absent fields
        if self.present:
            self.absent = False
        elif self.absent:
            self.present = False
        super().save(*args, **kwargs)
        

class AttendanceFile(models.Model):
    file_id = models.IntegerField()
    file_name = models.CharField(max_length=250)
    file = models.FileField(upload_to='attendance_files/')
    enent = models.ForeignKey('management.Events', on_delete=models.CASCADE, null=True)
    unit = models.ForeignKey('management.Unit', on_delete=models.CASCADE, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.file_id} "
    
    class Meta:
        verbose_name_plural = "Attendance Files"
    


    
