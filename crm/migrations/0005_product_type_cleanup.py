from django.db import migrations


CANONICAL_SALE_PRODUCTS = [
    ("Bridal", 1),
    ("Reverse AD", 2),
    ("Fusion", 3),
    ("Copper", 4),
    ("Onegram (Forming)", 5),
    ("Polki", 6),
    ("Mossonite", 7),
    ("Stone", 8),
    ("Microgold", 9),
    ("Anti Tanish", 10),
]


def forwards(apps, schema_editor):
    ProductType = apps.get_model("crm", "ProductType")
    Customer = apps.get_model("crm", "Customer")
    Purchase = apps.get_model("crm", "Purchase")
    db_alias = schema_editor.connection.alias

    def save_product(product):
        product.save(using=db_alias, update_fields=["name", "order"])
        return product

    merged = ProductType.objects.using(db_alias).filter(name="Onegram (Forming)").first()
    onegram = ProductType.objects.using(db_alias).filter(name="Onegram").first()
    forming = ProductType.objects.using(db_alias).filter(name="Forming").first()

    if merged is None and onegram is not None:
        onegram.name = "Onegram (Forming)"
        onegram.order = 5
        merged = save_product(onegram)
    elif merged is None:
        merged = ProductType.objects.using(db_alias).create(name="Onegram (Forming)", order=5)
    else:
        merged.order = 5
        save_product(merged)

    for old_product in [onegram, forming]:
        if old_product is None or old_product.pk == merged.pk:
            continue

        Customer.objects.using(db_alias).filter(product_interest=old_product).update(product_interest=merged)

        for purchase in Purchase.objects.using(db_alias).filter(products=old_product).distinct().prefetch_related("products"):
            purchase.products.add(merged)
            purchase.products.remove(old_product)

        old_product.delete(using=db_alias)

    mossonite = ProductType.objects.using(db_alias).filter(name="Mossonite").first()
    mosoknight = ProductType.objects.using(db_alias).filter(name="Mosoknight").first()

    if mossonite is None and mosoknight is not None:
        mosoknight.name = "Mossonite"
        mosoknight.order = 7
        save_product(mosoknight)
    elif mossonite is None:
        ProductType.objects.using(db_alias).create(name="Mossonite", order=7)
    else:
        mossonite.order = 7
        save_product(mossonite)

    for name, order in CANONICAL_SALE_PRODUCTS:
        if name in {"Onegram (Forming)", "Mossonite"}:
            continue
        product, created = ProductType.objects.using(db_alias).get_or_create(name=name, defaults={"order": order})
        if not created and product.order != order:
            product.order = order
            save_product(product)


def backwards(apps, schema_editor):
    # Keep the cleaned-up product names on reverse migrations too.
    forwards(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0004_purchase_amount_range"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
