from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import ProductType, SALE_PRODUCT_NAMES

DEFAULT_STAFF_PASSWORD = "JaiShreeFashion@123"

DEFAULT_STAFF_USERS = [
    "shivam",
    "shashank",
    "komal",
    "seema",
    "julie",
    "akash",
]


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if sender.name == "django.contrib.auth":
        User = get_user_model()
        email = "admin@jaishreefashion.com".lower()
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(username=email, email=email, password=DEFAULT_STAFF_PASSWORD)


@receiver(post_migrate)
def create_default_staff(sender, **kwargs):
    if sender.name != "django.contrib.auth":
        return

    User = get_user_model()
    for name in DEFAULT_STAFF_USERS:
        email = f"{name.lower()}@gmail.com"
        display_name = name.strip().title()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": display_name,
                "is_staff": True,
                "is_active": True,
            },
        )
        updated_fields = []
        if (user.username or "").lower() != email:
            user.username = email
            updated_fields.append("username")
        if (user.email or "").lower() != email:
            user.email = email
            updated_fields.append("email")
        if user.first_name != display_name:
            user.first_name = display_name
            updated_fields.append("first_name")
        if not user.is_staff:
            user.is_staff = True
            updated_fields.append("is_staff")
        if not user.is_active:
            user.is_active = True
            updated_fields.append("is_active")
        if created or not user.has_usable_password():
            user.set_password(DEFAULT_STAFF_PASSWORD)
            updated_fields.append("password")
        if updated_fields:
            user.save(update_fields=updated_fields)


@receiver(post_migrate)
def create_default_types(sender, **kwargs):
    if sender.name != "crm":
        return

    for order, name in enumerate(SALE_PRODUCT_NAMES, start=1):
        ProductType.objects.get_or_create(name=name, defaults={"order": order})
