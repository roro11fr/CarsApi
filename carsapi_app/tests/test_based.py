import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "carsapi.settings")
import django
django.setup()

import pytest
from rest_framework.test import APIClient
from carsapi_app.models import Owner, Car, InsurancePolicy, Claim

def mk_owner(name="Alice", email="a@example.com"):
    return Owner.objects.create(owner_name=name, owner_email=email)

def mk_car(vin="WVWZZZ1JZXW000001"):
    owner = mk_owner()
    return Car.objects.create(
        vin=vin, make="VW", model="Golf", year_of_manufacture=2018, owner=owner
    )

def mk_policy(car=None, start="2025-01-01", end="2025-12-31", premium=1000):
    car = car or mk_car()
    return InsurancePolicy.objects.create(
        car=car, start_date=start, end_date=end, premium_amount=premium
    )

def mk_claim(car, policy, desc="Accident ușor", amount=500, status="OPEN"):
    return Claim.objects.create(
        car=car, policy=policy, description=desc, claim_amount=amount, status=status
    )

# ================== TESTE ==================

#  Health
@pytest.mark.django_db
def test_health_ok():
    client = APIClient()
    r = client.get("/api/health/")   # ai confirmat că acesta e path-ul corect
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

# Policies: creare 201
@pytest.mark.django_db
def test_policy_create_201():
    client = APIClient()
    car = mk_car(vin="WVWZZZ1JZXW000001")
    payload = {"start_date": "2025-01-01", "end_date": "2025-12-31", "premium_amount": 1500}
    r = client.post(f"/api/cars/{car.id}/policies/", data=payload, format="json")
    assert r.status_code == 201
    body = r.json()
    assert body["car"] == car.id
    assert body["end_date"] == "2025-12-31"

# Policies: 400  end_date < start_date
@pytest.mark.django_db
def test_policy_create_400_end_before_start():
    client = APIClient()
    car = mk_car(vin="WVWZZZ1JZXW000002")
    payload = {"start_date": "2025-12-31", "end_date": "2025-01-01", "premium_amount": 1500}
    r = client.post(f"/api/cars/{car.id}/policies/", data=payload, format="json")
    assert r.status_code == 400

#  Validity: true/false
@pytest.mark.django_db
def test_validity_true_then_false():
    client = APIClient()
    car = mk_car(vin="WVWZZZ1JZXW000003")
    mk_policy(car=car, start="2025-01-01", end="2025-12-31")
    r1 = client.get(f"/api/cars/{car.id}/insurance-valid", {"date": "2025-06-01"})
    assert r1.status_code == 200
    assert r1.json()["valid"] is True
    r2 = client.get(f"/api/cars/{car.id}/insurance-valid", {"date": "2026-01-01"})
    assert r2.status_code == 200
    assert r2.json()["valid"] is False

#  Claims: creare 201 + câmpuri esențiale
@pytest.mark.django_db
def test_claim_create_201_minimal():
    client = APIClient()
    car = mk_car(vin="WVWZZZ1JZXW000004")
    policy = mk_policy(car=car)
    payload = {"description": "Accident ușor", "claim_amount": 500, "policy": policy.id, "status": "OPEN"}
    r = client.post(f"/api/cars/{car.id}/claims/", data=payload, format="json")
    assert r.status_code == 201
    body = r.json()
    assert body["car"] == car.id
    assert body["policy"] == policy.id

#  Policies: 404 masina nu există
@pytest.mark.django_db
def test_policy_create_404_car_not_found():
    client = APIClient()
    payload = {"start_date": "2025-01-01", "end_date": "2025-12-31", "premium_amount": 900}
    r = client.post("/api/cars/999999/policies/", data=payload, format="json")
    assert r.status_code == 404

# Claims: 404 masina nu există
@pytest.mark.django_db
def test_claim_create_404_car_not_found():
    client = APIClient()
    payload = {"description": "X", "claim_amount": 100, "policy": 1, "status": "OPEN"}
    r = client.post("/api/cars/999999/claims/", data=payload, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_validity_400_out_of_range_date():
    client = APIClient()
    car = mk_car(vin="WVWZZZ1JZXW000006")
    # presupunere: view-ul respinge date mult în trecut/viitor (ex. <1900 sau >2100)
    r = client.get(f"/api/cars/{car.id}/insurance-valid", {"date": "1800-01-01"})
    assert r.status_code == 400

# History: ordering & shapes
@pytest.mark.django_db
def test_history_shapes_and_ordering():
    client = APIClient()
    car = mk_car(vin="WVWZZZ1JZXW000007")
    # două polițe (end_date desc așteptat)
    p1 = mk_policy(car=car, start="2024-01-01", end="2024-12-31", premium=800)
    p2 = mk_policy(car=car, start="2025-01-01", end="2025-12-31", premium=900)
    # două claims (în endpoint, ordonează desc după created_at/claim_date)
    mk_claim(car, p1, desc="zgârietură", amount=100)
    mk_claim(car, p2, desc="bară față", amount=300)

    r = client.get(f"/api/cars/{car.id}/history/")
    assert r.status_code == 200
    data = r.json()

    # shapes
    assert data["carId"] == car.id
    assert isinstance(data["policies"], list)
    assert isinstance(data["claims"], list)
    assert len(data["policies"]) >= 2
    assert len(data["claims"]) >= 2

    # ordering policies: desc by end_date
    policy_end_dates = [p["end_date"] for p in data["policies"]]
    assert policy_end_dates == sorted(policy_end_dates, reverse=True)
