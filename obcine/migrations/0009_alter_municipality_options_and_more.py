# Generated by Django 4.0.5 on 2023-05-11 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("obcine", "0008_alter_plannedexpense_document_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="municipality",
            options={
                "verbose_name": "Municipality",
                "verbose_name_plural": "Municipality",
            },
        ),
        migrations.AddField(
            model_name="municipalityfinancialyear",
            name="is_published",
            field=models.BooleanField(default=False),
        ),
    ]
