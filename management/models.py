from django.db import models

class Events(models.Model):
    eventId = models.IntegerField()
    event_name = models.CharField(max_length=250)
    location = models.ForeignKey('management.Location', on_delete=models.CASCADE, null=True)
    date_time = models. DateTimeField()
    
    def __str__(self):
        return f"{self.event_name} - {self.eventId} "
    
class Location(models.Model):
    locationId = models.IntegerField()
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.state} - {self.locationId} "
    

    
