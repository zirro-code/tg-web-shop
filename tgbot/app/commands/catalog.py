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

    paginator = Paginator(
        object_list,
        per_page=per_page,
    )
    page_results = await sync_to_async(paginator.get_page(page))  # type: ignore

    if page != 1:
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("previous", chat_id),
                callback_data=f"{_type}+page+{page - 1}+{category}",
            )
        )
    for category in page_results:
        logger.info(category)
        text: str = category.category if _type == "category" else category.subcategory  # type: ignore  # noqa
        markup.add(
            InlineKeyboardButton(
                text=text,  # type: ignore
                callback_data=f"{_type}+page+1+{text}+{category}",
            )
        )
    if paginator.count > page:
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
    paginator = Paginator(object_list, per_page=1)

    markup = InlineKeyboardBuilder()

    item: web.admin_app.telegram_bot.models.Item = await sync_to_async(  # type: ignore
        paginator.get_page(int(page))  # type: ignore
    )
    logger.warning(item)

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
            callback_data=f"item+add_to_cart+{item.id}",  # type: ignore
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
async def command(message: Message, bot: Bot) -> None:
    await bot.send_message(message.chat.id, i18n.t("catalog", message.chat.id))

    await generate_categories(bot, 1, message.chat.id, "category")


@router.callback_query(CallbackDataPrefixFilter("category"))
async def handle_category_callback(query: CallbackQuery, bot: Bot):
    if not isinstance(query.message, str):
        raise ValueError

    split = query.message.split("+")
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


@router.callback_query(CallbackDataPrefixFilter("subcategory"))
async def handle_subcategory_callback(query: CallbackQuery, bot: Bot):
    if not isinstance(query.message, str):
        raise ValueError

    split = query.message.split("+")
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


@router.callback_query(CallbackDataPrefixFilter("item"))
async def handle_item_callback(query: CallbackQuery, bot: Bot):
    if not isinstance(query.message, str):
        raise ValueError

    split = query.message.split("+")
    _type: Literal["add_to_cart", "page"] = split[1]  # type: ignore
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
    elif _type == "add_to_cart":
        ...
    else:
        return Never
