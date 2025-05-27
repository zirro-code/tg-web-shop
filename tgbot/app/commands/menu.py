from typing import Literal, Never

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import tgbot.app.commands.cart
import tgbot.app.commands.catalog
from tgbot.app import i18n
from tgbot.app.utils import CallbackDataPrefixFilter

router = Router(name=__name__)


@router.message(Command("menu"))
async def command(message: Message, bot: Bot) -> None:
    await bot.send_message(message.chat.id, i18n.t("menu", message.chat.id))

    markup = InlineKeyboardBuilder()
    markup.add(InlineKeyboardButton(text="Каталог", callback_data="menu+catalog"))
    markup.add(InlineKeyboardButton(text="Корзина", callback_data="menu+cart"))


@router.callback_query(CallbackDataPrefixFilter("menu"))
async def handle_delivery_callback(query: CallbackQuery, bot: Bot):
    if not isinstance(query.message, str):
        raise ValueError

    split = query.message.split("+")
    _type: Literal["catalog", "cart"] = split[1]  # type: ignore

    if _type == "catalog":
        await tgbot.app.commands.catalog.command(query, bot)
    elif _type == "cart":
        await tgbot.app.commands.cart.command(query, bot)
    else:
        return Never
