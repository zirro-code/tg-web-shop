import os
from dataclasses import dataclass
from enum import Enum

import django
from aiogram import Router

# TODO: hack to make it work asap
os.environ.setdefault("DJANGO_MODULE_NAME", "web.admin_app.telegram_bot")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.admin_app.admin_app.settings")
django.setup()

import tgbot.app.commands.cart
import tgbot.app.commands.catalog
import tgbot.app.commands.check_subscription
import tgbot.app.commands.faq
import tgbot.app.commands.help
import tgbot.app.commands.menu
import tgbot.app.commands.start


@dataclass
class Command:
    command: str
    description: str
    router: Router


class Commands(Enum):
    start = Command(
        command="start",
        description="Start the bot",
        router=tgbot.app.commands.start.router,
    )
    help = Command(
        command="help",
        description="Get help with any of the questions",
        router=tgbot.app.commands.help.router,
    )
    check = Command(
        command="check",
        description="Check required subscriptions",
        router=tgbot.app.commands.check_subscription.router,
    )
    menu = Command(
        command="menu",
        description="Get main menu",
        router=tgbot.app.commands.menu.router,
    )
    catalog = Command(
        command="catalog",
        description="Open items catalog",
        router=tgbot.app.commands.catalog.router,
    )
    cart = Command(
        command="cart",
        description="Open your shopping cart",
        router=tgbot.app.commands.cart.router,
    )


misc_routers = (tgbot.app.commands.faq.router,)
