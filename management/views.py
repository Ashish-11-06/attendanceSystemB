import random
import sys
import openpyxl
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
    
    
    # Ashish --
    
class UploadVolunteerExcelView(APIView):
    def post(self, request, unit_id):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        # Use the unit_id from the URL directly
        try:
            unit_from_url = Unit.objects.get(id=unit_id)
        except Unit.DoesNotExist:
            return Response({'error': f"Unit ID {unit_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wb = openpyxl.load_workbook(file)
            inserted = {}

            for sheet in wb.worksheets:
                sheet_name = sheet.title.strip().lower()
                count = 0

                # Detect gender and registration status based on sheet name
                gender = None
                is_registered = True

                if sheet_name == 'gents':
                    gender = 'Male'
                elif sheet_name == 'ladies':
                    gender = 'Female'
                elif sheet_name == 'un-reg gents':
                    gender = 'Male'
                    is_registered = False
                elif sheet_name == 'un-reg ladies':
                    gender = 'Female'
                    is_registered = False

                # Step 1: Get headers from row 3
                raw_headers = [str(cell.value).strip().lower() if cell.value else '' for cell in sheet[3]]

                # Normalize column_map keys to lowercase too
                column_map = {
                    'new p#': 'new_personal_number',
                    'old p#': 'old_personal_number',
                    'name': 'name',
                    'contact no.': 'phone',
                    'email': 'email',
                    'volunteer id': 'volunteer_id',
                    'unit id': 'unit_id',
                    's#': 's_number'  # Add S# to the column map
                }

                # Map column index to model field using normalized header
                header_field_map = {}
                for idx, header in enumerate(raw_headers):
                    field = column_map.get(header)
                    if field:
                        header_field_map[idx] = field

                # print("Header field map:", header_field_map)

                for row in sheet.iter_rows(min_row=4, values_only=True):
                    if not any(row):
                        continue

                    row_data = {}
                    for idx, value in enumerate(row):
                        field_name = header_field_map.get(idx)
                        if field_name:
                            row_data[field_name] = value

                    # Check if S# is 'X' and skip the row if it is
                    s_number = row_data.get('s_number')
                    if s_number == 'X':
                        print("Skipping row due to S# being 'X'")
                        continue  # Skip this row if S# is 'X'

                    # Clean and validate data
                    name = row_data.get('name', '').strip()

                    if not name:
                        # print("Skipping row due to empty name")
                        continue  # Skip this row if name is empty

                    # Determine unit instance
                    unit = unit_from_url  # Use the unit from the URL directly
                    unit_id_in_row = row_data.get('unit_id')
                    if unit_id_in_row:
                        try:
                            unit = Unit.objects.get(id=unit_id_in_row)
                        except Unit.DoesNotExist:
                            print(f"Unit ID {unit_id_in_row} not found, using default unit")

                    data = {
                        'name': name,
                        'email': row_data.get('email'),
                        'phone': row_data.get('phone'),
                        'old_personal_number': row_data.get('old_personal_number'),
                        'new_personal_number': row_data.get('new_personal_number'),
                        'gender': gender,  # Use the gender determined by the sheet name
                        'unit': unit.id if unit else None,
                        'is_registered': is_registered,
                    }

                    # print("Row data passed to serializer:", data)
                    serializer = VolunteerSerializer(data=data)
                    if serializer.is_valid():
                        serializer.save()
                        count += 1
                    else:
                        print(f"Validation errors: {serializer.errors}")

                inserted[sheet.title] = f"{count} rows imported"

            return Response({'message': 'Import successful', 'details': inserted}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        unit = request.data.get('unit')
        event = request.data.get('event')
        
        if unit and event:
            # Get attendance for specific unit and event
            attendance = Attendance.objects.filter(unit__unit_id=unit, event__event_id=event)
            serializer = AttendanceSerializer(attendance, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "unit_id and event_id are required."}, status=status.HTTP_400_BAD_REQUEST) 