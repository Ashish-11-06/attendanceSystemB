import io
import mimetypes
import os
import random
import sys
import uuid
from wsgiref.util import FileWrapper 
import zipfile
from django.http import FileResponse, StreamingHttpResponse
import openpyxl
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from management.models import Admin, Attendance, AttendanceFile, EventUnitLocation, Events, Location, Register, Unit, Volunteer
from management.serializers import AdminSerializer, AttendanceFileSerializer, AttendanceSerializer, EventUnitLocationSerializer, EventsSerializer, LocationSerializer, LoginSerializer, RegisterSerializer, UnitSerializer, VolunteerSerializer
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
            events = Events.objects.filter(event_id=event_id)
        else:
            events = Events.objects.all().order_by('-created_at')

        result = []

        for event in events:
            event_data = {
                "id":event.id,
                "event_id": event.event_id,
                "event_name": event.event_name,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "time": event.time,
                "locations": []
            }

            event_locations = EventUnitLocation.objects.filter(event=event)

            location_map = {}

            for entry in event_locations:
                if not entry.unit or not entry.location:
                    continue

                loc_id = entry.location.id
                if loc_id not in location_map:
                    location_map[loc_id] = {
                        "location_id": entry.location.id,
                        "location_name": entry.location.city,  # Assuming `name` field in Location
                        "units": []
                    }

                unit_data = {
                    "unit_id": entry.unit.unit_id,
                    "unit_name": entry.unit.unit_name,
                    "email": entry.unit.email,
                    "phone": entry.unit.phone,
                    "location": entry.unit.location
                }

                location_map[loc_id]["units"].append(unit_data)

            event_data["locations"] = list(location_map.values())
            result.append(event_data)

        return Response(result, status=200)


    def post(self, request):
        data = request.data.copy()

        # Generate unique event_id
        event_id = str(uuid.uuid4())[:8]
        data['event_id'] = event_id

        # Extract locations with units
        locations_data = data.pop("locations", [])

        # Serialize and save event
        serializer = EventsSerializer(data=data)
        if serializer.is_valid():
            event = serializer.save()

            # Save EventUnitLocation entries
            for loc in locations_data:
                location_id = loc.get("location_id")
                unit_ids = loc.get("unit", [])
                try:
                    location = Location.objects.get(id=location_id)
                    for unit_id in unit_ids:
                        unit = Unit.objects.get(id=unit_id)
                        EventUnitLocation.objects.create(
                            event=event,
                            location=location,
                            unit=unit
                        )
                except Location.DoesNotExist:
                    return Response({"error": f"Location ID {location_id} not found."}, status=400)
                except Unit.DoesNotExist:
                    return Response({"error": f"Unit ID {unit_id} not found."}, status=400)

            # Prepare full response
            response_data = {
                "id": event.id,
                "event_id": event.event_id,
                "event_name": event.event_name,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "time": event.time,
                "locations": []
            }

            # Fetch full details from EventUnitLocation
            event_locations = EventUnitLocation.objects.filter(event=event)
            location_map = {}

            for entry in event_locations:
                if not entry.unit or not entry.location:
                    continue

                loc_id = entry.location.id
                if loc_id not in location_map:
                    location_map[loc_id] = {
                        "location_id": loc_id,
                        "location_name": entry.location.city,  # assuming field name
                        "units": []
                    }

                unit = entry.unit
                location_map[loc_id]["units"].append({
                    "unit_id": unit.id,
                    "unit_name": unit.unit_name,
                    "email": unit.email,
                    "phone": unit.phone,
                    "location": unit.location
                })

            response_data["locations"] = list(location_map.values())

            return Response({
                "message": "Event created successfully!",
                "data": response_data
            }, status=201)

        return Response(serializer.errors, status=400)
    
    def put(self, request, event_id=None):
        if not event_id:
            return Response({"error": "event_id is required in URL."}, status=status.HTTP_400_BAD_REQUEST)

        event = get_object_or_404(Events, event_id=event_id)
        serializer = EventsSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Event updated successfully!", "data": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, event_id=None):
        if not event_id:
            return Response({"error": "event_id is required in URL."}, status=status.HTTP_400_BAD_REQUEST)
        event = get_object_or_404(Events, event_id=event_id)
        event.delete()
        return Response({"message": "Event deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
  
    
    
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

    def put(self, request, unit_id):
        # print("Received request data for update:", request.data)
        if not unit_id:
            return Response({"error": "Unit ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            unit = Unit.objects.get(id=unit_id)  # Or `id=unit_id` if you're using PK
        except Unit.DoesNotExist:
            return Response({"error": "No Unit matches the given ID."}, status=status.HTTP_404_NOT_FOUND)
    
        unit = get_object_or_404(Unit, id=unit_id)
        # print("Found unit for update:", unit)
        
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
        event_id = request.query_params.get('event')
        unit_id = request.query_params.get('unit')

        files = AttendanceFile.objects.all()

        if event_id:
            files = files.filter(event_id=event_id)  # assuming event is a ForeignKey named event
        if unit_id:
            files = files.filter(unit_id=unit_id)    # assuming unit is a ForeignKey named unit

        serializer = AttendanceFileSerializer(files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # print('hello')
        serializer = AttendanceFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "File uploaded successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TotalCountAPIView(APIView):
    def get(self, request):
        total_events = Events.objects.count()
        total_volunteers = Volunteer.objects.count()
        total_units = Unit.objects.count()
        total_locations = Location.objects.count()

        return Response({
            "total_events": total_events,
            "total_volunteers": total_volunteers,
            "total_units": total_units,
            "total_locations": total_locations
        }, status=status.HTTP_200_OK)

# class VolunteerCountAPIVIew(APIView):
#     def get(self, request):
#         total = Volunteer.objects.count()
#         return Response({"total_volunteers": total}, status=status.HTTP_200_OK)
    
# class UnitCountAPIView(APIView):
#     def get(self, request):
#         total = Unit.objects.count()
#         return Response({"total_units": total}, status=status.HTTP_200_OK)
    
# class LocationCountAPIView(APIView):
#     def get(self, request):
#         total = Location.objects.count()
#         return Response({"total_locations": total}, status=status.HTTP_200_OK)  
    
    
class DataFechEvenUnitIdAPIView(APIView):
    def post (self, request, unit=None, event=None):
        unit = request.data.get('unit')
        event = request.data.get('event')
        
        if unit and event:
            # Get attendance for specific unit and event
            attendance = Attendance.objects.filter(unit_id=unit, event_id=event)
            serializer = AttendanceSerializer(attendance, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "unit_id and event_id are required."}, status=status.HTTP_400_BAD_REQUEST) 
        
class EventUnitLocationAPIView(APIView):
    def get(self, request):
        locations = EventUnitLocation.objects.all()
        serializer = EventUnitLocationSerializer(locations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def post(self, request):
    #     serializer = EventUnitLocationSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response({"message": "Event-Unit-Location created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AttendanceFileDownloadAPIView(APIView):
    def post(self, request):
        event_id = request.data.get('event')
        unit_id = request.data.get('unit')

        if not event_id or not unit_id:
            return Response({"error": "Event and Unit are required."}, status=status.HTTP_400_BAD_REQUEST)

        attendance_file = AttendanceFile.objects.filter(event_id=event_id, unit_id=unit_id).first()

        if not attendance_file:
            return Response({"error": "No file found."}, status=status.HTTP_404_NOT_FOUND)

        file_path = attendance_file.file.path

        if not os.path.exists(file_path):
            return Response({"error": "File not found on disk."}, status=status.HTTP_404_NOT_FOUND)

        wrapper = FileWrapper(open(file_path, 'rb'))
        file_name = os.path.basename(file_path)

        response = FileResponse(wrapper, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    
      
class VolunteersByUnitPostAPIView(APIView):
    def post(self, request):
        unit_id = request.data.get("unit")

        if not unit_id:
            return Response({"error": "Unit ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Use `unit_id=unit_id` to filter by ForeignKey properly
        volunteers = Volunteer.objects.filter(unit_id=unit_id)

        if not volunteers.exists():
            return Response({"message": "No volunteers found for this unit."}, status=status.HTTP_404_NOT_FOUND)

        serializer = VolunteerSerializer(volunteers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
