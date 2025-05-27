from aiogram.filters import Filter
from aiogram.types import CallbackQuery


class CallbackDataPrefixFilter(Filter):
    def __init__(self, prefix: str):
        self.prefix = prefix

    async def __call__(self, callback: CallbackQuery) -> bool:
        if not callback.data:
            return False
        return callback.data.startswith(self.prefix)
