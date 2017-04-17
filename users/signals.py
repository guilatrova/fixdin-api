from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework_expiring_authtoken.models import ExpiringToken
from django.conf import settings

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        ExpiringToken.objects.create(user=instance)