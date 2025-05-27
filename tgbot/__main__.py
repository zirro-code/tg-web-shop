import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

import tgbot.app.config


async def main() -> None:
    dispatcher = Dispatcher()
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])

    for command in tgbot.app.config.Commands:
        dispatcher.include_router(command.value.router)
    for misc_router in tgbot.app.config.misc_routers:
        dispatcher.include_router(misc_router)

    await bot.set_my_commands(
        [
            BotCommand(command.name.value, command.description.value)  # type: ignore
            for command in tgbot.app.config.Commands
        ]
    )  # language_code="RU"

    await dispatcher.start_polling(bot)  # type: ignore # noqa


if __name__ == "__main__":
    asyncio.run(main())
