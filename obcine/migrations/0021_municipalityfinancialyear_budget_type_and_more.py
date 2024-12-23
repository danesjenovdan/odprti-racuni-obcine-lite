# Generated by Django 4.0.5 on 2023-10-13 12:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("obcine", "0020_remove_monthlyexpense_timestamp_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="municipalityfinancialyear",
            name="budget_type",
            field=models.CharField(
                choices=[
                    ("REBALANS", "Rebalans"),
                    ("VALID", "Valid"),
                    ("ADOPTED", "Adopted"),
                ],
                default="VALID",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="municipalityfinancialyear",
            name="financial_year",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="municipalityfinancialyears",
                to="obcine.financialyear",
                verbose_name="Leto",
            ),
        ),
        migrations.AlterField(
            model_name="municipalityfinancialyear",
            name="is_published",
            field=models.BooleanField(
                default=False, verbose_name="Javno prikazano leto"
            ),
        ),
    ]
