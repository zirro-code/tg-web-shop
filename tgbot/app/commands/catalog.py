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


async def generate_categories(
    bot: Bot,
    page: int,
    chat_id: int,
    _type: Literal["category", "subcategory"],
    category: str | None = None,
):
    per_page = 6

    # TODO: unhandled edgecase of subcategories with the same name

    markup = InlineKeyboardBuilder()
    if _type == "category":
        object_list = (
            web.admin_app.telegram_bot.models.Item.objects.all()
            .order_by(_type)
            .distinct(_type)
        )
    elif _type == "subcategory":
        object_list = (
            web.admin_app.telegram_bot.models.Item.objects.all()
            .filter(category=category)
            .order_by(_type)
            .distinct(_type)
        )

    paginator = await sync_to_async(Paginator)(
        object_list,
        per_page=per_page,
    )
    page_results = await sync_to_async(paginator.get_page)(page)

    if page != 1:
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("previous", chat_id),
                callback_data=f"{_type}+page+{page - 1}+{category}",
            )
        )
    async for category in page_results.object_list.all():
        text = category.category if _type == "category" else category.subcategory  # type: ignore
        markup.add(
            InlineKeyboardButton(
                text=text,  # type: ignore
                callback_data=f"{_type}+{_type}+1+{text}+{category.category}",  # type: ignore
            )
        )
    if paginator.num_pages > page:
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("next", chat_id),
                callback_data=f"{_type}+page+{page + 1}+{category}",
            )
        )

    await bot.send_message(
        chat_id, f"{i18n.t(_type, chat_id)} {page}", reply_markup=markup.as_markup()
    )


async def generate_item(
    bot: Bot, chat_id: int, category: str, subcategory: str, page: int
):
    # TODO: unhandled edgecase of adding new items
    # TODO: logically incorrect orderby because of wrong id param in model

    object_list = (
        web.admin_app.telegram_bot.models.Item.objects.all()
        .filter(category=category, subcategory=subcategory)
        .order_by("name")
    )
    paginator = await sync_to_async(Paginator)(object_list, per_page=1)

    markup = InlineKeyboardBuilder()

    item: web.admin_app.telegram_bot.models.Item = await (
        await sync_to_async(  # type: ignore
            paginator.get_page  # type: ignore
        )(int(page))
    ).object_list.afirst()

    if page > 1:
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("previous", chat_id),
                callback_data=f"item+page+{category}+{subcategory}+{page - 1}",
            )
        )
    markup.add(
        InlineKeyboardButton(
            text=i18n.t("add_to_cart", chat_id),
            callback_data=f"cart+add+{item.id}",  # type: ignore
        )
    )
    if paginator.count > page:
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("next", chat_id),
                callback_data=f"item+page+{category}+{subcategory}+{page + 1}",
            )
        )
    # TODO: implement message edit wrapper
    await bot.send_message(
        chat_id,
        f"{item.name}\n\n{item.description}",  # type: ignore
        reply_markup=markup.as_markup(),
    )


@router.message(Command("catalog"))
async def command(message: Message | CallbackQuery, bot: Bot) -> None:
    if isinstance(message, Message):
        chat_id = message.chat.id
    elif isinstance(message, CallbackQuery):  # type: ignore
        if not message.message:
            raise ValueError
        chat_id = message.message.chat.id
    else:
        return Never

    await generate_categories(bot, 1, chat_id, "category")


@router.callback_query(CallbackDataPrefixFilter("category"))
async def handle_category_callback(query: CallbackQuery, bot: Bot):
    if not query.data or not query.message:
        raise ValueError

    split = query.data.split("+")
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

    await query.answer()


@router.callback_query(CallbackDataPrefixFilter("subcategory"))
async def handle_subcategory_callback(query: CallbackQuery, bot: Bot):
    if not query.data or not query.message:
        raise ValueError

    split = query.data.split("+")
    _type: Literal["subcategory", "page"] = split[1]  # type: ignore
    page = split[2]
    sub_category = None if len(split) < 4 else split[3]
    category = None if len(split) < 5 else split[4]

    if _type == "page":
        await generate_categories(bot, int(page), query.message.chat.id, "category")
    elif _type == "subcategory":
        await generate_item(bot, query.message.chat.id, category, sub_category, 1)  # type: ignore
    else:
        return Never

    await query.answer()


@router.callback_query(CallbackDataPrefixFilter("item"))
async def handle_item_callback(query: CallbackQuery, bot: Bot):
    if not query.data or not query.message:
        raise ValueError

    split = query.data.split("+")
    _type: Literal["page"] = split[1]  # type: ignore
    page = split[2]
    sub_category = None if len(split) < 4 else split[3]
    category = None if len(split) < 5 else split[4]

    if _type == "page":
        await generate_item(
            bot,
            query.message.chat.id,
            category,  # type: ignore
            sub_category,  # type: ignore
            int(page),
        )
    else:
        return Never

    await query.answer()
