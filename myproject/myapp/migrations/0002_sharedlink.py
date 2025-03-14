# Generated by Django 5.1.6 on 2025-03-13 23:05

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SharedLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "token",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("is_used", models.BooleanField(default=False)),
                (
                    "file",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="myapp.filemetadata",
                    ),
                ),
            ],
        ),
    ]
