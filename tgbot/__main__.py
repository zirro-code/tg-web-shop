import asyncio
import os

from aiogram import Bot, Dispatcher

import tgbot.app.config


async def main() -> None:
    dispatcher = Dispatcher()

    for command in tgbot.app.config.Commands:
        dispatcher.include_router(command.value.router)
    for misc_router in tgbot.app.config.misc_routers:
        dispatcher.include_router(misc_router)

    await dispatcher.start_polling(Bot(token=os.environ["TELEGRAM_BOT_TOKEN"]))  # type: ignore # noqa


if __name__ == "__main__":
    asyncio.run(main())
