from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0006_followup_completed_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="phone2",
            field=models.CharField(blank=True, default="", max_length=18),
        ),
    ]
