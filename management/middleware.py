# core/middleware.py
from django.utils.deprecation import MiddlewareMixin

class SocketIOMonitorMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Check if the incoming request is targeting socket.io
        if request.path.startswith("/socket.io"):
            print("\n⚡ [Socket.IO Request Detected]")
            print(f"Path: {request.path}")
            print(f"Query: {request.META.get('QUERY_STRING')}")
            print(f"Method: {request.method}")
            print(f"IP Address: {request.META.get('REMOTE_ADDR')}")
            print(f"User-Agent: {request.META.get('HTTP_USER_AGENT')}")
            print(f"Full URL: {request.build_absolute_uri()}")
            print("--------------------------------------------------")
        return None
