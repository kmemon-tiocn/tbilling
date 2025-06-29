# Generated by Django 5.1.6 on 2025-06-26 09:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_awsaccount_is_approved_alter_awsaccount_customer_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="awsaccount",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aws_accounts",
                to="main.group",
            ),
        ),
    ]
