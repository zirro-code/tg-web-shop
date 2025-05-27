import os

from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = os.environ.get("DJANGO_MODULE_NAME", "telegram_bot")
