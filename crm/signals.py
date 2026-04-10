from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import ProductType, SALE_PRODUCT_NAMES


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if sender.name == "django.contrib.auth":
        User = get_user_model()
        email = "admin@jaishreefashion.com"
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(username=email, email=email, password="JaiShreeFashion@123")


@receiver(post_migrate)
def create_default_types(sender, **kwargs):
    if sender.name != "crm":
        return

    for order, name in enumerate(SALE_PRODUCT_NAMES, start=1):
        ProductType.objects.get_or_create(name=name, defaults={"order": order})
