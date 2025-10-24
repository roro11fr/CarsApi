# app/actions.py
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from datetime import date as _date
import structlog

from .serializers import InsurancePolicySerializer, ClaimSerializer
from .services import (
    create_policy_for_car, create_claim_for_car,
    get_car_history, is_insured_on_date
)

logger = structlog.get_logger()


# ------------- POLICIES (GET+POST) -------------
def get_or_create_policies_action(view, request, car):
    if request.method.lower() == "get":
        qs = car.policies.all().order_by("-start_date")
        page = view.paginate_queryset(qs)
        ser = InsurancePolicySerializer(page or qs, many=True)
        logger.info("policies_listed", request_id=getattr(request, "id", None), car_id=car.id, count=len(ser.data))
        return view.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    # POST
    obj = create_policy_for_car(
        car=car,
        provider=request.data.get("provider"),
        start_date=request.data.get("start_date"),
        end_date=request.data.get("end_date"),
    )
    logger.info(
        "policy_created",
        request_id=getattr(request, "id", None),
        policy_id=obj.id,
        car_id=car.id,
        start_date=str(obj.start_date),
        end_date=str(obj.end_date),
        provider=obj.provider or None,
    )
    return Response(InsurancePolicySerializer(obj).data, status=status.HTTP_201_CREATED)


# ------------- CLAIMS (GET+POST) -------------
def get_or_create_claims_action(view, request, car):
    if request.method.lower() == "get":
        qs = car.claims.all().order_by("-claim_date")
        page = view.paginate_queryset(qs)
        ser = ClaimSerializer(page or qs, many=True)
        logger.info("claims_listed", request_id=getattr(request, "id", None), car_id=car.id, count=len(ser.data))
        return view.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    # POST
    obj = create_claim_for_car(
        car=car,
        claim_date=request.data.get("claim_date"),
        description=request.data.get("description", ""),
        amount=request.data.get("amount"),
    )
    logger.info(
        "claim_created",
        request_id=getattr(request, "id", None),
        claim_id=obj.id,
        car_id=car.id,
        claim_date=str(obj.claim_date),
        amount=float(obj.amount),
    )
    resp = Response(ClaimSerializer(obj).data, status=201)
    resp["Location"] = f"/api/claims/{obj.id}"
    return resp


# ------------- HISTORY (GET) -------------
def history_action(car):
    data = get_car_history(car)
    logger.info("history_returned", car_id=car.id, items=len(data))
    return Response(data)


# ------------- INSURANCE VALID (GET) -------------
def insurance_valid_action(car, request):
    date_str = request.query_params.get("date")
    if not date_str:
        logger.warning("insurance_valid_missing_date", request_id=getattr(request, "id", None), car_id=car.id)
        return Response(
            {"detail": "Query param 'date' is required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        target = _date.fromisoformat(date_str)
    except ValueError:
        logger.warning("insurance_valid_bad_format", request_id=getattr(request, "id", None), car_id=car.id, date_str=date_str)
        return Response(
            {"detail": "Invalid date format. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not (1900 <= target.year <= 2100):
        logger.warning("insurance_valid_out_of_range", request_id=getattr(request, "id", None), car_id=car.id, date=str(target))
        return Response(
            {"detail": "Date out of allowed range [1900..2100]."},
            status=status.HTTP_400_BAD_REQUEST
        )

    valid = is_insured_on_date(car, target)
    logger.info("insurance_valid_checked", request_id=getattr(request, "id", None), car_id=car.id, date=str(target), valid=bool(valid))
    return Response({"carId": car.id, "date": str(target), "valid": valid})
