from django.contrib import admin

# Register your models here.
from .models import Car, Owner, InsurancePolicy, Claim, PolicyExpiryLog

admin.site.register(Car)
admin.site.register(Owner)
admin.site.register(InsurancePolicy)
admin.site.register(Claim)
admin.site.register(PolicyExpiryLog)
