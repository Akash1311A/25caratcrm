from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0005_product_type_cleanup"),
    ]

    operations = [
        migrations.AddField(
            model_name="followup",
            name="completed_at",
            field=models.DateField(blank=True, null=True),
        ),
    ]
