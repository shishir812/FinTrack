from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile, UserRole


@receiver(post_save, sender=get_user_model())
def ensure_bank_account(sender, instance, created, **kwargs):
    if created:
        role = UserRole.ADMIN if instance.is_staff else UserRole.CUSTOMER
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})
