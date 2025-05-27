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
async def command(message: Message | CallbackQuery, bot: Bot) -> None:
    if isinstance(message, Message):
        chat_id = message.chat.id
    elif isinstance(message, CallbackQuery):  # type: ignore
        if not message.message:
            raise ValueError
        chat_id = message.message.chat.id
    else:
        return Never
    markup = InlineKeyboardBuilder()
    markup.add(InlineKeyboardButton(text="Каталог", callback_data="menu+catalog"))
    markup.add(InlineKeyboardButton(text="Корзина", callback_data="menu+cart"))

    await bot.send_message(
        chat_id,
        i18n.t("menu", chat_id),
        reply_markup=markup.as_markup(),
    )


@router.callback_query(CallbackDataPrefixFilter("menu"))
async def handle_delivery_callback(query: CallbackQuery, bot: Bot):
    if not query.data or not query.message:
        raise ValueError

    split = query.data.split("+")
    _type: Literal["catalog", "cart"] = split[1]  # type: ignore

    if _type == "catalog":
        await tgbot.app.commands.catalog.command(query, bot)
    elif _type == "cart":
        await tgbot.app.commands.cart.command(query, bot)
    else:
        return Never

    await query.answer()
