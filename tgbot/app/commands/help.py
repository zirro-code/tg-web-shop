from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from tgbot.app import i18n

router = Router(name=__name__)


@router.message(Command("help"))
async def command(message: Message, bot: Bot) -> None:
    await bot.send_message(message.chat.id, i18n.t("help", message.chat.id))
