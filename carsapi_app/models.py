from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
# Create your models here.
def current_year():
    return timezone.now().year


class Owner(models.Model):
    owner_name = models.CharField(max_length= 50)
    owner_email = models.EmailField(null=True, blank=True)
    
    def __str__(self):
        return self.owner_name
    
class Car(models.Model):
    vin = models.CharField(max_length=17, unique=True)
    make = models.CharField(max_length=100, blank= True)
    model = models.CharField(max_length=100,blank= True)
    year_of_manufacture = models.PositiveSmallIntegerField(validators=[MinValueValidator(1886), MaxValueValidator(current_year)], null=True, blank=True)
    owner= models.ForeignKey(Owner, on_delete=models.CASCADE, null=False, related_name='cars')

class InsurancePolicy(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='policies')
    provider = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F('start_date')),
                name='policy_end_after_start'
            )
        ]

class Claim(models.Model):
    claim_date = models.DateField(null = False)
    description = models.TextField(null = False)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null = False, related_name='claims')
    amount = models.DecimalField( max_digits=12, decimal_places=2, 
                                validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(auto_now_add= True, null = False)
    
    class Meta:
        ordering = ['-claim_date']
    
class PolicyExpiryLog(models.Model):
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE)
    logged_expiry_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['policy'], name='uniq_policy_once')
        ]
        indexes = [models.Index(fields=['logged_expiry_at'])]

    
    