from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

import tgbot.app.utils
from tgbot.app import i18n

router = Router(name=__name__)


@router.message(Command("start"))
async def command(message: Message, bot: Bot) -> None:
    await bot.send_message(message.chat.id, i18n.t("start", message.chat.id))

    await tgbot.app.utils.create_telegram_user(
        message.chat.id,
        message.chat.first_name or message.chat.full_name,
        message.chat.last_name,
        message.chat.username,
    )
