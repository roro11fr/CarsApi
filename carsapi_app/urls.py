from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    health_check,
    OwnerViewSet, CarViewSet, InsurancePolicyViewSet,
    ClaimViewSet, PolicyExpiryLogViewSet
)

router = DefaultRouter()
router.register(r"owners", OwnerViewSet, basename="owner")
router.register(r"cars", CarViewSet, basename="car")
router.register(r"policies", InsurancePolicyViewSet, basename="policy")
router.register(r"claims", ClaimViewSet, basename="claim")
router.register(r"policy-expiry-logs", PolicyExpiryLogViewSet, basename="policy-expiry-log")

urlpatterns = [
    path("health/", health_check, name="health"),
    path("", include(router.urls)),
]
