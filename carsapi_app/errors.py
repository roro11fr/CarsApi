from rest_framework.views import exception_handler
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, NotFound) and context and context.get("view"):
        view = context["view"]
        view_name = view.__class__.__name__
        if view_name == "CarViewSet":
            return Response({"detail": "Car not found"}, status=status.HTTP_404_NOT_FOUND)

    return response
