from django.db import models
from django.contrib.auth.models import User

class Integration(models.Model):
    name_id = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=50)

class HasStatus:
    SUCCESS = 0
    FAIL = 1
    PARTIAL = 2

    STATUS = (
        (SUCCESS, 'Success'),
        (FAIL, 'Fail'),
        (PARTIAL, 'Partial success')
    )

class IntegrationSettings(models.Model, HasStatus):
    class Meta:
        unique_together = ('user', 'integration')

    integration = models.ForeignKey(Integration)
    user = models.ForeignKey(User)
    last_sync = models.DateTimeField()
    status = models.PositiveIntegerField(choices=HasStatus.STATUS)

class SyncHistory(models.Model, HasStatus):
    AUTO = 0
    MANUAL = 1

    TRIGGER_CHOICES = (
        (AUTO, 'Auto'),
        (MANUAL, 'Manual')
    )

    settings = models.ForeignKey(IntegrationSettings)
    status = models.PositiveIntegerField(choices=HasStatus.STATUS)
    result = models.CharField(max_length=120)
    details = models.TextField()
    trigger = models.PositiveIntegerField(choices=TRIGGER_CHOICES)
    