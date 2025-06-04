import random
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from management.models import Admin, Attendance, AttendanceFile, Events, Location, Register, Unit, Volunteer
from management.serializers import AdminSerializer, AttendanceFileSerializer, AttendanceSerializer, EventsSerializer, LocationSerializer, LoginSerializer, RegisterSerializer, UnitSerializer, VolunteerSerializer
from management.utils import send_otp_email

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Generate OTP
            otp = str(random.randint(100000, 999999))

            # Temporarily save OTP in validated_data
            serializer.save(otp=otp)

            # Send OTP to email
            email = serializer.validated_data.get('email')
            send_otp_email(email, otp)

            return Response({
                "message": "Registration successful! OTP sent to email.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Register.objects.get(email=email, otp=otp)
            # OTP matched — now clear it from the database
            user.otp = None  # or use '' if you prefer empty string
            user.save()
            
            return Response({"message": "OTP verification successful!"}, status=status.HTTP_200_OK)
        except Register.DoesNotExist:
            return Response({"error": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)
        
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].strip().lower()
        password = serializer.validated_data['password'].strip()

        user_type = serializer.validated_data['user_type']

        if user_type == 'admin':
            try:
                admin = Admin.objects.get(email__iexact=email)
                if check_password(password, admin.password):
                    return Response({
                        "message": "Admin login successful",
                        "user": {
                            "admin_name": admin.name,
                            "email": admin.email,
                            "user_type": "admin",
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Invalid admin credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            except Admin.DoesNotExist:
                return Response({"error": "Invalid admin credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        elif user_type == 'unit':
            # Try Register table first
            user = Register.objects.filter(email__iexact=email, user_type='unit').first()
            if user and check_password(password, user.password):
                return Response({
                    "message": "Unit login successful (via Register)",
                    "user": {
                        "unit_name": user.unit_name,
                        "email": user.email,
                        "user_type": user.user_type,
                    }
                }, status=status.HTTP_200_OK)

            # Try Unit table next
            unit = Unit.objects.filter(email__iexact=email).first()
            if unit and check_password(password, unit.password):
                return Response({
                    "message": "Unit login successful (via Unit)",
                    "user": {
                        "unit_name": unit.unit_name,
                        "email": unit.email,
                        "user_type": "unit",
                    }
                }, status=status.HTTP_200_OK)

            # If both fail
            return Response({"error": "Invalid unit credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"error": "Invalid user_type"}, status=status.HTTP_400_BAD_REQUEST) 
    
    
class EventsAPIView(APIView):
    def get(self, request, event_id=None):
        if event_id:
            # Get single event by id
            event = get_object_or_404(Events, event_id=event_id)
            serializer = EventsSerializer(event)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Get all events
            events = Events.objects.all()
            serializer = EventsSerializer(events, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    def post(self, request):
        serializer = EventsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # event_id generated inside serializer
            return Response(
                {"message": "Event added successfully!", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, event_id=None):
        if not event_id:
            return Response({"error": "ID is required for update."}, status=status.HTTP_400_BAD_REQUEST)

        event = get_object_or_404(Events, event_id=event_id)
        serializer = EventsSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, event_id=None):
        if not event_id:
            return Response({"error": "event_id is required in URL."}, status=status.HTTP_400_BAD_REQUEST)
        event = get_object_or_404(Events, event_id=event_id)
        event.delete()
        return Response({"message": "Unit deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    
    
class LocationAPIView(APIView):
    def get(self, request, location_id=None):
        if location_id:
            # Get single event by id
            location = get_object_or_404(Location, location_id=location_id)
            serializer = LocationSerializer(location)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Get all events
            locations = Location.objects.all()
            serializer = LocationSerializer(locations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # location_id auto-generated in serializer.create()
            return Response({"message": "Location created successfully!", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, location_id=None):
        if not location_id:
            return Response({"error": "ID is required for update."}, status=status.HTTP_400_BAD_REQUEST)

        location = get_object_or_404(Location, location_id=location_id)
        serializer = LocationSerializer(location, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class UnitAPIView(APIView):
    def get(self, request, unit_id=None):
        if unit_id:
            # Get single unit by id
            unit = get_object_or_404(Unit, unit_id=unit_id)
            serializer = UnitSerializer(unit)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Get all units
        else:
            units = Unit.objects.all()
            serializer = UnitSerializer(units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()
        if 'password' in data:
            raw_password = data['password']
            data['plain_password'] = raw_password
            data['password'] = make_password(raw_password)
        serializer = UnitSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unit created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        unit_id = request.data.get('unit_id')  # Ensure the ID is passed in request body
        if not unit_id:
            return Response({"error": "ID is required for update."}, status=status.HTTP_400_BAD_REQUEST)
        
        unit = get_object_or_404(Unit, unitId=unit_id)
        
        data = request.data.copy()  
        if 'password' in data:
            raw_password = data['password']
            data['plain_password'] = raw_password
            data['password'] = make_password(raw_password)
            
        serializer = UnitSerializer(unit, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, unit_id=None):
        if not unit_id:
            return Response({"error": "unit_id is required in URL."}, status=status.HTTP_400_BAD_REQUEST)
        unit = get_object_or_404(Unit, unit_id=unit_id)
        unit.delete()
        return Response({"message": "Unit deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    

class VolunteerAPIView(APIView):
    def get(self, request, volunteer_id=None):
        if volunteer_id:
            # Get single unit by id
            volunteer = get_object_or_404(Volunteer, volunteer_id=volunteer_id)
            serializer = VolunteerSerializer(volunteer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Get all volunteers
        else:
            volunteers = Volunteer.objects.all()
            serializer = VolunteerSerializer(volunteers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VolunteerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Volunteer created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, volunteer_id=None):
        if not volunteer_id:
            return Response({"error": "ID is required for update."}, status=status.HTTP_400_BAD_REQUEST)

        volunteer = get_object_or_404(Volunteer, volunteer_id=volunteer_id)
        serializer = VolunteerSerializer(volunteer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class AdminAPIView(APIView):
    def get(self, request, admin_id=None):
        if admin_id:
            # Get single admin by id
            volunteer = get_object_or_404(Admin, admin_id=admin_id)
            serializer = AdminSerializer(volunteer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Get all admins
        else:
            admins = Admin.objects.all()
            serializer = AdminSerializer(admins, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Admin created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, admin_id=None):
        if not admin_id:
            return Response({"error": "ID is required for update."}, status=status.HTTP_400_BAD_REQUEST)

        admin = get_object_or_404(Admin, admin_id=admin_id)
        serializer = AdminSerializer(admin, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class AttendanceAPIView(APIView):
    def get(self, request, attendance_id=None):
        if attendance_id:
            # Get single attendance by id
            attendance = get_object_or_404(Attendance, atd_id=attendance_id)
            serializer = AttendanceSerializer(attendance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Get all attendance
        else:
            attendance = Attendance.objects.all()
            serializer = AttendanceSerializer(attendance, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    # def post(self, request):
    #     serializer = AttendanceSerializer(data=request.data)
        
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response({"message": "Attendance recorded", "data": serializer.data}, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        is_many = isinstance(request.data, list)
        serializer = AttendanceSerializer(data=request.data, many=is_many)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Attendance recorded",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "message": "Failed to record attendance",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, attendance_id):
        attendance = get_object_or_404(Attendance, atd_id=attendance_id)  # Use atd_id not pk
        serializer = AttendanceSerializer(attendance, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Attendance updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Failed to update attendance.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AttendanceFileAPIView(APIView):
    def get(self, request):
        files = AttendanceFile.objects.all()
        serializer = AttendanceFileSerializer(files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AttendanceFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "File uploaded successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class EventsCountAPIView(APIView):
    def get(self, request):
            total = Events.objects.count()
            return Response({"total_events": total}, status=status.HTTP_200_OK)
        
class VolunteerCountAPIVIew(APIView):
    def get(self, request):
        total = Volunteer.objects.count()
        return Response({"total_volunteers": total}, status=status.HTTP_200_OK)
    
class UnitCountAPIView(APIView):
    def get(self, request):
        total = Unit.objects.count()
        return Response({"total_units": total}, status=status.HTTP_200_OK)
    
class LocationCountAPIView(APIView):
    def get(self, request):
        total = Location.objects.count()
        return Response({"total_locations": total}, status=status.HTTP_200_OK)  
    
    
class DataFechEvenUnitIdAPIView(APIView):
    def post (self, request, unit=None, event=None):
        if unit and event:
            # Get attendance for specific unit and event
            attendance = Attendance.objects.filter(unit__unit_id=unit, event__event_id=event)
            serializer = AttendanceSerializer(attendance, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "unit_id and event_id are required."}, status=status.HTTP_400_BAD_REQUEST) 