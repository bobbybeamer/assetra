from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assetra", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="webhookdelivery",
            name="attempt_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="webhookdelivery",
            name="dead_lettered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="webhookdelivery",
            name="last_error",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="webhookdelivery",
            name="next_attempt_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="webhookdelivery",
            name="status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("success", "Success"), ("failed", "Failed"), ("dead_letter", "Dead Letter")],
                default="pending",
                max_length=20,
            ),
        ),
    ]
