from datetime import timedelta

from django.db import migrations


FOLLOWUP_OFFSETS = (3, 7, 15)


def forwards(apps, schema_editor):
    Customer = apps.get_model("crm", "Customer")
    FollowUp = apps.get_model("crm", "FollowUp")
    Purchase = apps.get_model("crm", "Purchase")
    db_alias = schema_editor.connection.alias

    for customer in Customer.objects.using(db_alias).all():
        latest_purchase = Purchase.objects.using(db_alias).filter(customer_id=customer.pk).order_by("-date", "-pk").first()
        followups = FollowUp.objects.using(db_alias).filter(customer_id=customer.pk)

        if latest_purchase is None:
            followups.delete()
            continue

        target_dates = [latest_purchase.date + timedelta(days=offset) for offset in FOLLOWUP_OFFSETS]
        retained_ids = set()

        for target_date in target_dates:
            matches = list(followups.filter(next_followup_date=target_date).order_by("pk"))
            if matches:
                retained_ids.add(matches[0].pk)
                for duplicate in matches[1:]:
                    duplicate.delete()
            else:
                FollowUp.objects.using(db_alias).create(
                    customer_id=customer.pk,
                    next_followup_date=target_date,
                    notes="Auto-generated follow-up",
                    status="Pending",
                    assigned_to_id=latest_purchase.assigned_to_id,
                )

        followups.exclude(next_followup_date__in=target_dates).delete()


def backwards(apps, schema_editor):
    # Non-reversible normalization.
    return


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0007_customer_phone2"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
