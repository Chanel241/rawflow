from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

def get_default_timestamp():
    return timezone.now().timestamp()

class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=[('producer', 'Producteur'), ('processor', 'Transformateur')], null=True, blank=True)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True,
    )

    def __str__(self):
        return self.username

class Transaction(models.Model):
    product_id = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    origin = models.CharField(max_length=100)
    details = models.JSONField()
    timestamp = models.FloatField(default=get_default_timestamp)

    def __str__(self):
        return f"{self.product_id} - {self.industry}"

class BlockModel(models.Model):
    index = models.IntegerField()
    transactions = models.JSONField()
    timestamp = models.IntegerField()  
    previous_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)
    nonce = models.IntegerField(default=0)

    def __str__(self):
        return f"Block {self.index}"

class Profile(models.Model):
    ROLE_CHOICES = [
        ('producer', 'Producteur'),
        ('processor', 'Transformateur'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='producer')

    def __str__(self):
        return f"{self.user.username} - {self.role}"