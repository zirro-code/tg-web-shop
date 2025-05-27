from aiogram.filters import Filter
from aiogram.types import CallbackQuery

import web.admin_app.telegram_bot.models


class CallbackDataPrefixFilter(Filter):
    def __init__(self, prefix: str):
        self.prefix = prefix

    async def __call__(self, callback: CallbackQuery) -> bool:
        if not callback.data:
            return False
        return callback.data.startswith(self.prefix)


async def create_telegram_user(
    chat_id: int,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
):
    if (
        web.admin_app.telegram_bot.models.User.objects.filter(chat_id=chat_id)
        .all()
        .count()
        >= 1
    ):
        return

    await web.admin_app.telegram_bot.models.User(
        chat_id=chat_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
    ).asave()
