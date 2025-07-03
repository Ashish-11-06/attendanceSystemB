from rest_framework import serializers
from .models import Admin, Attendance, AttendanceFile, EventUnitLocation, Events, Khetra, Location, Register, Unit, Volunteer
from django.utils import timezone


class RegisterSerializer(serializers.ModelSerializer):
    otp = serializers.CharField(max_length=10, required=False, write_only=True)
    unit_name = serializers.CharField(max_length=250, write_only=True)

    class Meta:
        model = Register  # your model name
        fields = ['email', 'password', 'otp', 'unit_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }
        
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    user_type = serializers.ChoiceField(choices=['admin', 'unit'], required=True)

class LocationSerializer(serializers.ModelSerializer):
    location_id = serializers.CharField(read_only=True)
    class Meta:
        model = Location
        fields = '__all__'
        
    def create(self, validated_data):
        # Generate location_id like LOC001, LOC002 ...
        last_location = Location.objects.order_by('location_id').last()
        if last_location:
            last_id_num = int(last_location.location_id.replace('LOC', ''))
            new_id_num = last_id_num + 1
        else:
            new_id_num = 1

        validated_data['location_id'] = f"LOC{new_id_num:03d}"
        return super().create(validated_data)


# class EventsSerializer(serializers.ModelSerializer):
#     location = LocationSerializer()
#     class Meta:
#         model = Events
#         fields = ['id', 'eventId', 'event_name', 'date', 'time','location', 'created_at']
        
class EventsSerializer(serializers.ModelSerializer):
    locations = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Location.objects.all(), required=False 
    )
    units = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Unit.objects.all(), required=False 
    )

    class Meta:
        model = Events
        fields = ['id', 'event_id', 'event_name', 'start_date', 'end_date', 'time', 'locations', 'units', 'created_at']
        read_only_fields = ('event_id',)

    def create(self, validated_data):
        locations = validated_data.pop('locations', [])
        units = validated_data.pop('units', [])

        last_event = Events.objects.order_by('event_id').last()
        if last_event:
            last_id_num = int(last_event.event_id.replace('EVE', ''))
            new_id_num = last_id_num + 1
        else:
            new_id_num = 1

        validated_data['event_id'] = f"EVE{new_id_num:03d}"
        event = Events.objects.create(**validated_data)
        event.locations.set(locations)
        event.units.set(units)
        return event

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['locations'] = LocationSerializer(instance.locations.all(), many=True).data
        rep['units'] = UnitSerializer(instance.units.all(), many=True).data
        return rep
       
class UnitSerializer(serializers.ModelSerializer):
    khetra = serializers.PrimaryKeyRelatedField(queryset=Khetra.objects.all())
    password = serializers.CharField(required=False, write_only=True)
    class Meta:
        model = Unit # Assuming Unit is defined in management.models
        fields = '__all__'
        extra_kwargs = {
            'unit_id': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
        
class VolunteerSerializer(serializers.ModelSerializer):
    # Accept only unit ID during write
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all())

    class Meta:
        model = Volunteer
        fields = ['id', 'volunteer_id', 'name', 'email', 'phone', 'old_personal_number', 'new_personal_number', 'gender', 'unit', 'is_registered']
        read_only_fields = ('volunteer_id',)

    def create(self, validated_data):
        # Generate volunteer_id like VOL001, VOL002 ...
        last_volunteer = Volunteer.objects.order_by('volunteer_id').last()
        if last_volunteer:
            last_id_num = int(last_volunteer.volunteer_id.replace('VOL', ''))
            new_id_num = last_id_num + 1
        else:
            new_id_num = 1

        validated_data['volunteer_id'] = f"VOL{new_id_num:03d}"
        return super().create(validated_data)

    # Return full nested unit data in read
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['unit'] = UnitSerializer(instance.unit).data
        return representation
    
    
class AdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False, write_only=True)
    class Meta:
        model = Admin  # Assuming Admin is defined in management.models
        fields = '__all__'
        read_only_fields = ('admin_id',)

    def create(self, validated_data):
        # Generate admin_id like ADM001, ADM002 ...
        last_admin = Admin.objects.order_by('admin_id').last()
        if last_admin:
            last_id_num = int(last_admin.admin_id.replace('ADM', ''))
            new_id_num = last_id_num + 1
        else:
            new_id_num = 1

        validated_data['admin_id'] = f"ADM{new_id_num:03d}"
        return super().create(validated_data)

        
class AttendanceSerializer(serializers.ModelSerializer):
    volunteer = serializers.PrimaryKeyRelatedField(queryset=Volunteer.objects.all())
    event = serializers.PrimaryKeyRelatedField(queryset=Events.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all(), required=False)

    class Meta:
        model = Attendance
        fields = ['id', 'atd_id', 'present', 'absent', 'in_time', 'out_time', 'date', 'remark', 'volunteer', 'event', 'unit']
        read_only_fields = ('atd_id',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['volunteer'] = VolunteerSerializer(instance.volunteer).data
        representation['event'] = EventsSerializer(instance.event).data
        return representation

    def create(self, validated_data):
        present = validated_data.get('present', False)
        absent = validated_data.get('absent', False)
        in_time = validated_data.get('in_time')

        if present and not in_time:
            validated_data['in_time'] = timezone.now().time()
        elif absent:
            validated_data['in_time'] = None

        last_atd = Attendance.objects.order_by('atd_id').last()
        if last_atd and last_atd.atd_id:
            last_id_num = int(last_atd.atd_id.replace('ATD', ''))
            new_id_num = last_id_num + 1
        else:
            new_id_num = 1

        validated_data['atd_id'] = f"ATD{new_id_num:03d}"
        return super().create(validated_data)

    def update(self, instance, validated_data):
        present = validated_data.get('present', instance.present)
        absent = validated_data.get('absent', instance.absent)
        in_time = validated_data.get('in_time', instance.in_time)

        if present and not in_time:
            validated_data['in_time'] = timezone.now().time()
        elif absent:
            validated_data['in_time'] = None

        return super().update(instance, validated_data)

class AttendanceFileSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Events.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all())
    
    class Meta:
        model = AttendanceFile  # Assuming AttendanceFile is a model related to Attendance
        fields = '__all__'
        read_only_fields = ['file_id'] 
        
class EventUnitLocationSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Events.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    class Meta:
        model = EventUnitLocation  # Assuming EventUnitLocation is a model related to Events, Unit, and Location
        fields = ['id', 'event', 'unit', 'location']
        read_only_fields = ['id']  # Assuming id is auto-generated
        

class KhetraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Khetra  
        fields = '__all__'    
