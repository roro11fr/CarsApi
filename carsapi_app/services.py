# app/services.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from .models import Car, InsurancePolicy, Claim, PolicyExpiryLog
from .serializers import InsurancePolicySerializer, ClaimSerializer
import structlog

logger = structlog.get_logger()

# ---------- VALIDITY ----------
def is_insured_on_date(car: Car, target: date) -> bool:
    """True dacă există o poliță activă pentru car la data target (inclusiv capete)."""
    return InsurancePolicy.objects.filter(
        car=car, start_date__lte=target, end_date__gte=target
    ).exists()


# ---------- POLICIES ----------
@transaction.atomic
def create_policy_for_car(
    car: Car, *, provider: Optional[str], start_date: date, end_date: date
) -> InsurancePolicy:
    """
    Creează o poliță pentru mașină.
    Validările (end>=start, 1900..2100, anti-suprapunere) sunt în serializer.
    """
    payload = {
        "car": car.pk,
        "provider": provider or "",
        "start_date": start_date,
        "end_date": end_date,
    }
    ser = InsurancePolicySerializer(data=payload)
    ser.is_valid(raise_exception=True)
    obj = ser.save()
    logger.info("policy_created_service", policy_id=obj.id, car_id=car.id, start_date=str(obj.start_date), end_date=str(obj.end_date), provider=obj.provider or None)
    return obj


# ---------- CLAIMS ----------
@transaction.atomic
def create_claim_for_car(
    car: Car, *, claim_date: date, description: str, amount: str | float
) -> Claim:
    """Creează un claim pentru mașină (validări în serializer)."""
    payload = {
        "car": car.pk,
        "claim_date": claim_date,
        "description": description,
        "amount": amount,
    }
    ser = ClaimSerializer(data=payload)
    ser.is_valid(raise_exception=True)
    return ser.save()


# ---------- HISTORY ----------
@dataclass
class HistoryItem:
    sort_key: str
    payload: Dict[str, Any]

def get_car_history(car: Car) -> List[Dict[str, Any]]:
    """Timeline combinat POLICIES + CLAIMS, ordonat ascendent după dată."""
    items: List[HistoryItem] = []

    for p in car.policies.all():
        items.append(HistoryItem(
            sort_key=str(p.start_date),
            payload={
                "type": "POLICY",
                "policyId": p.id,
                "startDate": str(p.start_date),
                "endDate": str(p.end_date),
                "provider": p.provider or "",
            },
        ))

    for c in car.claims.all():
        items.append(HistoryItem(
            sort_key=str(c.claim_date),
            payload={
                "type": "CLAIM",
                "claimId": c.id,
                "claimDate": str(c.claim_date),
                "amount": float(c.amount),
                "description": c.description,
            },
        ))

    items.sort(key=lambda x: x.sort_key)
    return [x.payload for x in items]


# ---------- EXPIRY (util pt. job-ul de background) ----------
@transaction.atomic
def detect_and_log_expired_policies(run_date: Optional[date] = None) -> int:
    """
    Marchează o singură dată polițele care AU EXPIRAT la `run_date` (sau azi dacă e None).
    Idempotent datorită UniqueConstraint(policy) în PolicyExpiryLog.
    Returnează numărul de loguri create.
    """
    today = run_date or timezone.localdate()
    # polițe care au end_date == azi și nu sunt încă logate
    to_log = (
        InsurancePolicy.objects
        .filter(end_date=today)
        .exclude(id__in=PolicyExpiryLog.objects.values("policy_id"))
        .select_related("car")
    )
    created = 0
    for p in to_log:
        PolicyExpiryLog.objects.create(policy=p)
        created += 1
    return created
