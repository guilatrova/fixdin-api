from .base import IntegrationSettings
from django.db import models

class CPFL_Settings(models.Model):
    settings = models.ForeignKey(IntegrationSettings)
    name = models.CharField(max_length=150)
    documento = models.CharField(max_length=14)
    imovel = models.CharField(max_length=12)