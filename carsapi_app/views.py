# app/views.py
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Owner, Car, InsurancePolicy, Claim, PolicyExpiryLog
from .serializers import (
    OwnerSerializer, CarSerializer,
    InsurancePolicySerializer, ClaimSerializer, PolicyExpiryLogSerializer,
)
from . import actions
import structlog
logger = structlog.get_logger()


# ------------ HEALTH ------------
@api_view(["GET"])
def health_check(_request):
    logger.info("health_check", now=timezone.now().isoformat())
    return Response({"status": "ok", "time": timezone.now().isoformat()})


# ------------ OWNER ------------
class OwnerViewSet(viewsets.ModelViewSet):
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer

    filterset_fields = ["owner_email"]
    search_fields = ["owner_name", "owner_email"]
    ordering_fields = ["owner_name", "owner_email"]
    ordering = ["owner_name"]


# ------------ CAR ------------
class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.select_related("owner").all()
    serializer_class = CarSerializer

    filterset_fields = {
        "owner": ["exact"],
        "year_of_manufacture": ["exact", "gte", "lte"],
        "make": ["exact", "icontains"],
        "model": ["exact", "icontains"],
        "vin": ["exact", "icontains"],
    }
    search_fields = ["vin", "make", "model", "owner__owner_name"]
    ordering_fields = ["year_of_manufacture", "make", "model", "vin"]
    ordering = ["-year_of_manufacture", "make", "model"]

    # --- POLICIES (nested) ---
    @action(detail=True, methods=["get", "post"], url_path="policies")
    def policies(self, request, pk=None):
        car = self.get_object()
        return actions.get_or_create_policies_action(self, request, car)

    # --- CLAIMS (nested) ---
    @action(detail=True, methods=["get", "post"], url_path="claims")
    def claims(self, request, pk=None):
        car = self.get_object()
        return actions.get_or_create_claims_action(self, request, car)

    # --- HISTORY ---
    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        car = self.get_object()
        return actions.history_action(car)

    # --- INSURANCE VALID ---
    @action(detail=True, methods=["get"], url_path="insurance-valid")
    def insurance_valid(self, request, pk=None):
        car = self.get_object()
        return actions.insurance_valid_action(car, request)


# ------------ POLICY ------------
class InsurancePolicyViewSet(viewsets.ModelViewSet):
    queryset = InsurancePolicy.objects.select_related("car").all()
    serializer_class = InsurancePolicySerializer
    filterset_fields = ["car", "provider", "start_date", "end_date"]
    ordering_fields = ["start_date", "end_date", "provider"]
    ordering = ["-end_date"]


# ------------ CLAIM ------------
class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.select_related("car").all()
    serializer_class = ClaimSerializer
    filterset_fields = ["car", "claim_date"]
    ordering_fields = ["claim_date", "amount", "created_at"]
    ordering = ["-claim_date"]


# ------------ EXPIRY LOG (read-only) ------------
class PolicyExpiryLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PolicyExpiryLog.objects.select_related("policy").all()
    serializer_class = PolicyExpiryLogSerializer
    ordering = ["-logged_expiry_at"]
