from django.conf import settings
from django.db import models

SALE_PRODUCT_CHOICES = [
    ("Bridal", "Bridal"),
    ("Reverse AD", "Reverse AD"),
    ("Fusion", "Fusion"),
    ("Copper", "Copper"),
    ("Onegram (Forming)", "Onegram (Forming)"),
    ("Polki", "Polki"),
    ("Mossonite", "Mossonite"),
    ("Stone", "Stone"),
    ("Microgold", "Microgold"),
    ("Anti Tanish", "Anti Tanish"),
]

SALE_PRODUCT_NAMES = [name for name, _label in SALE_PRODUCT_CHOICES]

AMOUNT_RANGE_CHOICES = [
    ("0-5000", "Rs. 0 - 5k"),
    ("5000-10000", "Rs. 5k - 10k"),
    ("10000-20000", "Rs. 10k - 20k"),
    ("20000-30000", "Rs. 20k - 30k"),
    ("30000-50000", "Rs. 30k - 50k"),
    ("50000-100000", "Rs. 50k - 1L"),
    ("100000+", "Rs. 1L+"),
]

AMOUNT_RANGE_VALUES = {
    "0-5000": 0,
    "5000-10000": 5000,
    "10000-20000": 10000,
    "20000-30000": 20000,
    "30000-50000": 30000,
    "50000-100000": 50000,
    "100000+": 100000,
}


def amount_to_range(amount):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "0-5000"
    if amount < 5000:
        return "0-5000"
    if amount < 10000:
        return "5000-10000"
    if amount < 20000:
        return "10000-20000"
    if amount < 30000:
        return "20000-30000"
    if amount < 50000:
        return "30000-50000"
    if amount < 100000:
        return "50000-100000"
    return "100000+"

PRICE_CHOICES = [
    ("10-20", "₹10k–20k"),
    ("20-40", "₹20k–40k"),
    ("40-80", "₹40k–80k"),
    ("80+", "₹80k+")
]

PRODUCT_CHOICES = [
    ("Ring", "Ring"),
    ("Chain", "Chain"),
    ("Earrings", "Earrings"),
    ("Bridal Set", "Bridal Set"),
]

CUSTOMER_TYPE_CHOICES = [
    ("Regular", "Regular"),
    ("VIP", "VIP"),
    ("High Value", "High Value"),
]

OCCASION_CHOICES = [
    ("Wedding", "Wedding"),
    ("Gift", "Gift"),
    ("Festival", "Festival"),
    ("Other", "Other"),
]

FOLLOWUP_STATUS = [
    ("Pending", "Pending"),
    ("Completed", "Completed"),
]


class ProductType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class OccasionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=18, unique=True, db_index=True)
    whatsapp = models.CharField(max_length=18, blank=True)
    phone2 = models.CharField(max_length=18, blank=True, default="")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers",
    )
    price_range = models.CharField(max_length=12, choices=PRICE_CHOICES, default="10-20", db_index=True)
    product_interest = models.ForeignKey(ProductType, null=True, blank=True, on_delete=models.SET_NULL, related_name="customers")
    customer_type = models.CharField(max_length=16, choices=CUSTOMER_TYPE_CHOICES, default="Regular", db_index=True)
    notes = models.TextField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def whatsapp_link(self):
        number = self.whatsapp or self.phone
        digits = "".join(ch for ch in number if ch.isdigit())
        return f"https://wa.me/{digits}" if digits else ""

    def latest_purchase_date(self):
        if not self.pk:
            return None
        latest = self.purchases.order_by("-date").first()
        return latest.date if latest else None

    def total_spent(self):
        if not self.pk:
            return 0
        return self.purchases.aggregate(models.Sum("amount"))["amount__sum"] or 0

    def latest_purchase_range_display(self):
        if not self.pk:
            return "-"
        latest = None
        for purchase in self.purchases.all():
            if latest is None or purchase.date > latest.date:
                latest = purchase
        return latest.amount_range_display() if latest else "-"


class Purchase(models.Model):
    customer = models.ForeignKey(Customer, related_name="purchases", on_delete=models.CASCADE)
    products = models.ManyToManyField(ProductType, related_name="purchases", blank=True)
    amount_range = models.CharField(max_length=20, choices=AMOUNT_RANGE_CHOICES, default="5000-10000")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchases",
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Sale for {self.customer.name}"

    def product_summary(self):
        if not self.pk:
            return ""
        return ", ".join(self.products.values_list("name", flat=True))

    def amount_range_display(self):
        return dict(AMOUNT_RANGE_CHOICES).get(self.amount_range, self.amount_range)


class FollowUp(models.Model):
    customer = models.ForeignKey(Customer, related_name="followups", on_delete=models.CASCADE)
    next_followup_date = models.DateField(db_index=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=FOLLOWUP_STATUS, default="Pending", db_index=True)
    completed_at = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="followups",
    )

    class Meta:
        ordering = ["next_followup_date"]

    def is_overdue(self):
        from django.utils import timezone
        return self.status == "Pending" and self.next_followup_date < timezone.localdate()

    def __str__(self):
        return f"Follow-up for {self.customer.name} on {self.next_followup_date}"
