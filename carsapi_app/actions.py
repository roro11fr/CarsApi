# app/actions.py
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from datetime import date as _date


from .serializers import InsurancePolicySerializer, ClaimSerializer
from .services import (
    create_policy_for_car, create_claim_for_car,
    get_car_history, is_insured_on_date
)


# ------------- POLICIES (GET+POST) -------------
def get_or_create_policies_action(view, request, car):
    if request.method.lower() == "get":
        qs = car.policies.all().order_by("-start_date")
        page = view.paginate_queryset(qs)
        ser = InsurancePolicySerializer(page or qs, many=True)
        return view.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    obj = create_policy_for_car(
        car=car,
        provider=request.data.get("provider"),
        start_date=request.data.get("start_date"),
        end_date=request.data.get("end_date"),
    )
    return Response(InsurancePolicySerializer(obj).data, status=status.HTTP_201_CREATED)


# ------------- CLAIMS (GET+POST) -------------
def get_or_create_claims_action(view, request, car):
    if request.method.lower() == "get":
        ...
    obj = create_claim_for_car(
        car=car,
        claim_date=request.data.get("claim_date"),
        description=request.data.get("description", ""),
        amount=request.data.get("amount"),
    )
    resp = Response(ClaimSerializer(obj).data, status=201)
    resp["Location"] = f"/api/claims/{obj.id}"
    return resp


# ------------- HISTORY (GET) -------------
def history_action(car):
    return Response(get_car_history(car))


# ------------- INSURANCE VALID (GET) -------------
def insurance_valid_action(car, request):
    date_str = request.query_params.get("date")
    if not date_str:
        return Response(
            {"detail": "Query param 'date' is required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        target = _date.fromisoformat(date_str)
    except ValueError:
        return Response(
            {"detail": "Invalid date format. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not (1900 <= target.year <= 2100):
        return Response(
            {"detail": "Date out of allowed range [1900..2100]."},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "carId": car.id,
        "date": str(target),
        "valid": is_insured_on_date(car, target)
    })
