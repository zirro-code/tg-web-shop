# Generated by Django 5.2.1 on 2025-05-24 21:25

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="chat_id",
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="first_name",
            field=models.CharField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="last_name",
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(null=True),
        ),
    ]
