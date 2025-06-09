from django.db import models
from django.utils.timezone import now
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class Register(models.Model):
    # register_id = models.CharField(max_length=200, null)
    unit_name = models.CharField(max_length=250)
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=250)
    otp = models.CharField(max_length=10, null=True, blank=True)
    user_type = models.CharField(max_length=50, null=True, default='unit')
    created_at = models.DateTimeField(default=now)
    
    @property
    def is_authenticated(self):
        return True
    
    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unit_name} "
    
class Events(models.Model):
    event_id = models.CharField(max_length=50)
    event_name = models.CharField(max_length=250)
    # location = models.ManyToManyField('management.Location', blank=True, related_name='events')
    units = models.ManyToManyField('Unit', through='EventUnitLocation',  blank=True)
    locations = models.ManyToManyField('Location', through='EventUnitLocation', blank=True)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event_name} - {self.event_id} "
    
class Location(models.Model):
    location_id = models.CharField(max_length=200)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.state} - {self.location_id} "
    
class Unit(models.Model):
    unit_id = models.CharField(max_length=200)
    unit_name = models.CharField(max_length=250)
    password = models.CharField(max_length=250)   
    # plain_password = models.CharField(max_length=250, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=255, null=True)

    @property
    def is_authenticated(self):
        return True
    
    def __str__(self):
        return f"{self.unit_name} - {self.unit_id} "
    
    # def save(self, *args, **kwargs):
    #     if not self.password.startswith('pbkdf2_'):
    #         self.password = make_password(self.password)
    #     super().save(*args, **kwargs)
    
class Volunteer(models.Model):
    volunteer_id = models.CharField(max_length=50)
    name = models.CharField(max_length=250)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    old_personal_number = models.CharField(max_length=255, null=True, blank=True)
    new_personal_number = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ])
    unit = models.ForeignKey('management.Unit', on_delete=models.CASCADE, null=True)
    is_registered = models.BooleanField(default=True) 
    
    def __str__(self):
        return f"{self.name} - {self.volunteer_id} "
    
class Admin(models.Model):
    admin_id = models.CharField(max_length=200)
    name = models.CharField(max_length=250)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=250)
    user_type = models.CharField(max_length=20, null=True, default='admin')
    
    @property
    def is_authenticated(self):
        return True
        
    def __str__(self):
        return f"{self.name} - {self.admin_id} "
    
    def save(self, *args, **kwargs):
        # If password is not hashed yet, hash it
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
class Attendance(models.Model):
    atd_id = models.CharField(max_length=200)
    volunteer = models.ForeignKey('management.Volunteer', on_delete=models.CASCADE, null=True)
    event = models.ForeignKey('management.Events', on_delete=models.CASCADE, null=True)
    unit = models.ForeignKey('management.Unit', on_delete=models.CASCADE, null=True)
    date = models.DateField()
    in_time = models.TimeField(null=True, blank=True)
    out_time = models.TimeField(null=True, blank=True)
    present = models.BooleanField(default=False)
    absent = models.BooleanField(default=False)
    remark = models.CharField(max_length=250, null=True, blank=True)
    
    def __str__(self):
        return f" {self.date} "
    
    def save(self, *args, **kwargs):
        # Manage mutually exclusive flags
        if self.present:
            self.absent = False
            if not self.in_time:
                self.in_time = timezone.now().time()
        elif self.absent:
            self.present = False
            self.in_time = None  # Clear in_time if marked absent

        super().save(*args, **kwargs)
        

class AttendanceFile(models.Model):
    file_id = models.CharField(max_length=200)
    file_name = models.CharField(max_length=250)
    file = models.FileField(upload_to='attendance_files/')
    event = models.ForeignKey('management.Events', on_delete=models.CASCADE, null=True)
    unit = models.ForeignKey('management.Unit', on_delete=models.CASCADE)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.file_id:
            last_obj = AttendanceFile.objects.order_by('-id').first()
            last_id = int(last_obj.file_id.replace('ATD', '')) if last_obj and last_obj.file_id else 0
            self.file_id = f"ATD{last_id + 1:03d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.file_name} - {self.file_id} "
    
    class Meta:
        verbose_name_plural = "Attendance Files"
        

class EventUnitLocation(models.Model):
    event = models.ForeignKey('management.Events', on_delete=models.CASCADE, null=True)
    unit = models.ForeignKey('management.Unit', on_delete=models.CASCADE, null=True)
    location = models.ForeignKey('management.Location', on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return f"{self.event} - {self.unit} - {self.location} "
    
    class Meta:
        verbose_name_plural = "Event Unit Locations"
    


    
