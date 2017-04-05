from django.db import models
from django.utils import timezone

class VariableClassifcation(models.Model):
    varName = models.CharField(max_length=15)
    desc = models.CharField(max_length=200)
    tags = models.CharField(max_length=128)

    def __str__(self):
        return self.varName

class AccessAttempts(models.Model):
    client_id = models.CharField(max_length=200, default='NULL')
    customer_ip = models.CharField(max_length=16)
    path_hit = models.CharField(max_length=200)
    response_time = models.CharField(max_length=20, default='-', null=True)
    country = models.CharField(max_length=50, default='NULL', null=True)
    lat = models.CharField(max_length=10, default='NULL', null=True)
    long = models.CharField(max_length=10, default='NULL', null=True)
    city = models.CharField(max_length=50, default='NULL', null=True)
    country_code = models.CharField(max_length=5, default='NULL', null=True)
    postal_code = models.CharField(max_length=10, default='NULL', null=True)
    region = models.CharField(max_length=5, default='NULL', null=True)
    dma_code = models.CharField(max_length=10, default='NULL', null=True)
    date = models.DateTimeField(default=timezone.now, null=True)

    def __str__(self):
        return self.client_id
