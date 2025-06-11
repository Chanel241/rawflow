from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class Transaction(models.Model):
    product_id = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    origin = models.CharField(max_length=100)
    details = models.JSONField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product_id} - {self.industry}"

class BlockModel(models.Model):
    index = models.IntegerField()
    transactions = models.JSONField()
    timestamp = models.DateTimeField()
    previous_hash = models.CharField(max_length=256)
    hash = models.CharField(max_length=256)
    nonce = models.IntegerField()

    def __str__(self):
        return f"Block {self.index}"

class Profile(models.Model):
    ROLE_CHOICES = [
        ('producer', 'Producteur'),
        ('processor', 'Transformateur'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='producer')

    def __str__(self):
        return f"{self.user.username} - {self.role}"