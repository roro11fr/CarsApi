from rest_framework import serializers
from .models import Car, Owner, InsurancePolicy, Claim, PolicyExpiryLog
from datetime import date

class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'

class CarSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        source="owner", queryset=Owner.objects.all(), write_only=True
    )
    year_of_manufacture = serializers.IntegerField(
        min_value=1886, max_value=2100, required=False, allow_null=True
    )

    class Meta:
        model = Car
        fields = [
            "id", "vin", "make", "model", "year_of_manufacture",
            "owner", "owner_id"
        ]

MIN_YEAR, MAX_YEAR = 1900, 2100

def _check_year_range(d: date, field: str):
    if d.year < MIN_YEAR or d.year > MAX_YEAR:
        raise serializers.ValidationError({field: f"Year must be in [{MIN_YEAR}..{MAX_YEAR}]."})

class InsurancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePolicy
        fields = ["id", "car", "provider", "start_date", "end_date"]

    def validate(self, attrs):
        # preia valorile lipsă din instance pentru PATCH
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))

        if start is None or end is None:
            raise serializers.ValidationError("Both start_date and end_date are required.")

        _check_year_range(start, "start_date")
        _check_year_range(end, "end_date")
        if end < start:
            raise serializers.ValidationError("end_date must be >= start_date")

        car = attrs.get("car") or (self.instance.car if self.instance else None)
        if car:
            qs = InsurancePolicy.objects.filter(car=car)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.filter(start_date__lte=end, end_date__gte=start).exists():
                raise serializers.ValidationError(
                    "Policy interval overlaps an existing policy for this car."
                )
        return attrs

class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ["id", "claim_date", "description", "car", "amount", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        d = attrs["claim_date"]
        _check_year_range(d, "claim_date")
        if not attrs["description"].strip():
            raise serializers.ValidationError({"description": "Description must not be empty."})
        return attrs

class PolicyExpiryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyExpiryLog
        fields = '__all__'
