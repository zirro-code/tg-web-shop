# Generated by Django 5.2.1 on 2025-05-27 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0005_alter_item_media"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="delivery_address",
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="item",
            name="media",
            field=models.FileField(upload_to="media"),
        ),
    ]
