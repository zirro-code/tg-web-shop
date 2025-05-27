from typing import Literal, Never

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from loguru import logger

import web.admin_app.telegram_bot.models
from tgbot.app import i18n
from tgbot.app.utils import CallbackDataPrefixFilter

router = Router(name=__name__)


@router.message(Command("cart"))
async def command(message: Message, bot: Bot) -> None:
    await bot.send_message(message.chat.id, i18n.t("cart", message.chat.id))


@router.callback_query(CallbackDataPrefixFilter("category"))
async def handle_category_callback(query: CallbackQuery, bot: Bot):
    if not isinstance(query.message, str):
        raise ValueError

    split = query.message.split("+")
    _type: Literal["category", "page"] = split[1]  # type: ignore
    page = split[2]
    category = None if len(split) < 4 else split[3]

    if _type == "page":
        await generate_categories(bot, int(page), query.message.chat.id, "category")
    elif _type == "category":
        await generate_categories(
            bot, 1, query.message.chat.id, "subcategory", category
        )
    else:
        return Never
