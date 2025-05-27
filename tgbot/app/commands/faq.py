from dataclasses import dataclass
from typing import Any

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from rapidfuzz import fuzz

import web.admin_app.telegram_bot.models

router = Router(name=__name__)


@dataclass
class InlineElement:
    e_id: Any
    title: str
    description: str
    input_message_content: InputTextMessageContent
    fuzz: float


async def get_faq_info(text: str):
    faq_info = web.admin_app.telegram_bot.models.FAQArticle.objects.all()
    results: list[InlineElement] = []

    async for faq_point in faq_info:
        fuzz_ratio = fuzz.ratio(text, faq_point.title + "\n\n" + faq_point.text)
        if fuzz_ratio / 100 <= 0.2:
            continue

        results.append(
            InlineElement(
                e_id=faq_point.id,
                title=faq_point.title,
                description=faq_point.text,
                input_message_content=InputTextMessageContent(
                    message_text=faq_point.text
                ),
                fuzz=fuzz_ratio,
            )
        )

    return results


@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    await inline_query.answer(
        [
            InlineQueryResultArticle(
                id=str(info.e_id),
                title=info.title,
                description=f"{info.description}\n\n{round(info.fuzz, 2)}",
                input_message_content=info.input_message_content,
            )
            for info in sorted(
                list(await get_faq_info(inline_query.query)), key=lambda x: x.fuzz
            )
        ],
        is_personal=True,
    )
