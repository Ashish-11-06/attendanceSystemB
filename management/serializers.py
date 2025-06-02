from rest_framework import serializers
from .models import Admin, Attendance, AttendanceFile, Events, Location, Unit, Volunteer


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

# class EventsSerializer(serializers.ModelSerializer):
#     location = LocationSerializer()
#     class Meta:
#         model = Events
#         fields = ['id', 'eventId', 'event_name', 'date', 'time','location', 'created_at']
        
class EventsSerializer(serializers.ModelSerializer):
    # This allows writing using just the ID
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    class Meta:
        model = Events
        fields = ['id', 'event_id', 'event_name', 'date', 'time','location', 'created_at']

    # Use nested LocationSerializer only for reading
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['location'] = LocationSerializer(instance.location).data
        return representation

        
    
       
class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit # Assuming Unit is defined in management.models
        fields = '__all__'
        
class VolunteerSerializer(serializers.ModelSerializer):
    # Accept only unit ID in write operations
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all())

    class Meta:
        model = Volunteer
        fields = ['id', 'volunteer_id', 'name', 'email', 'old_personal_number', 'new_personal_number', 'gender', 'unit']

    # Return full nested unit data in read operations
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['unit'] = UnitSerializer(instance.unit).data
        return representation

        
class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin  # Assuming Admin is defined in management.models
        fields = '__all__'
        
class AttendanceSerializer(serializers.ModelSerializer):
    # Use ID for write
    volunteer = serializers.PrimaryKeyRelatedField(queryset=Volunteer.objects.all())
    event = serializers.PrimaryKeyRelatedField(queryset=Events.objects.all())

    class Meta:
        model = Attendance
        fields = ['id', 'atd_id', 'present', 'absent', 'in_time', 'out_time', 'date', 'remark', 'volunteer', 'event']

    # Use nested serializer for read
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['volunteer'] = VolunteerSerializer(instance.volunteer).data
        representation['event'] = EventsSerializer(instance.event).data
        return representation

class AttendanceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceFile  # Assuming AttendanceFile is a model related to Attendance
        fields = '__all__'