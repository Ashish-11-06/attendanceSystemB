from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from management.models import Admin, Attendance, AttendanceFile, Events, Location, Unit, Volunteer
from management.serializers import AdminSerializer, AttendanceFileSerializer, AttendanceSerializer, EventsSerializer, LocationSerializer, UnitSerializer, VolunteerSerializer

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
            serializer.save()
            return Response({"message": "Event added successfully!", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        event_id = request.data.get('event_id')  # Ensure the ID is passed in request body
        if not event_id:
            return Response({"error": "ID is required for update."}, status=status.HTTP_400_BAD_REQUEST)
        
        event = get_object_or_404(Events, eventId=event_id)
        serializer = EventsSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        location_id = request.data.get('location_id')  # Ensure the ID is passed in request body
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
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unit created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):
        unit_id = request.data.get('unit_id')  # Ensure the ID is passed in request body
        if not unit_id:
            return Response({"error": "ID is required for update."}, status=status.HTTP_400_BAD_REQUEST)
        
        unit = get_object_or_404(Unit, unitId=unit_id)
        serializer = UnitSerializer(unit, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VolunteerAPIView(APIView):
    def get(self, request, volunteer_id=None):
        if volunteer_id:
            # Get single unit by id
            volunteer = get_object_or_404(Volunteer, volunteerId=volunteer_id)
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
    
    def put(self, request):
        volunteer_id = request.data.get('volunteer_id')  # Ensure the ID is passed in request body
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
    
    def put(self, request):
        admin_id = request.data.get('admin_id')  # Ensure the ID is passed in request body
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

    def post(self, request):
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Attendance recorded", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, attendance_id):
        attendance = get_object_or_404(Attendance, pk=attendance_id)
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