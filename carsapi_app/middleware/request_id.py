# app/middleware/request_id.py
import uuid
from django.utils.deprecation import MiddlewareMixin

class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.id = str(uuid.uuid4())

    def process_response(self, request, response):
        response["X-Request-ID"] = getattr(request, "id", "")
        return response
