import os
from typing import Literal, Never

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    LabeledPrice,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from loguru import logger

import tgbot
import tgbot.app
import tgbot.app.commands
import tgbot.app.commands.menu
import tgbot.app.google_sheets
import web.admin_app.telegram_bot.models
from tgbot.app import i18n
from tgbot.app.utils import CallbackDataPrefixFilter

router = Router(name=__name__)


class Form(StatesGroup):
    item_id = State()
    amount_of_items = State()


class Delivery(StatesGroup):
    address = State()


async def select_amount(
    query: CallbackQuery, item_id: int, bot: Bot, state: FSMContext
):
    if not query.message:
        raise ValueError
    await state.set_state(Form.item_id)
    await state.update_data(item_id=item_id)
    await bot.send_message(
        query.message.chat.id, i18n.t("select_amount", query.message.chat.id)
    )


@router.message(Form.item_id)
async def handle_amount(message: Message, bot: Bot, state: FSMContext) -> None:
    if message.text is None or not message.text.isalnum():
        await bot.send_message(
            message.chat.id, i18n.t("incorrect_amount", message.chat.id)
        )
        return

    await state.set_state(Form.amount_of_items)
    await state.update_data(amount_of_items=int(message.text))
    markup = InlineKeyboardBuilder()
    markup.add(
        InlineKeyboardButton(
            text=i18n.t("confirm", message.chat.id), callback_data="cart+confirm"
        )
    )
    markup.add(
        InlineKeyboardButton(
            text=i18n.t("cancel", message.chat.id), callback_data="remove_message"
        )
    )

    await bot.send_message(
        message.chat.id,
        i18n.t("confirm_item_addition", message.chat.id),
        reply_markup=markup.as_markup(),
    )


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    logger.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        i18n.t("cancelled", message.chat.id),
        reply_markup=ReplyKeyboardRemove(),
    )


async def select_delivery_address(query: CallbackQuery, bot: Bot, state: FSMContext):
    if query.message is None:
        raise ValueError

    await state.set_state(Delivery.address)

    await bot.send_message(
        query.message.chat.id,
        i18n.t("send_delivery_address", query.message.chat.id),
    )


@router.message(Delivery.address)
async def handle_delivery_callback(message: Message, bot: Bot, state: FSMContext):
    user = await web.admin_app.telegram_bot.models.User.objects.aget(
        chat_id=message.chat.id
    )
    user.delivery_address = message.text
    await user.asave()

    markup = InlineKeyboardBuilder()
    markup.add(
        InlineKeyboardButton(
            text=i18n.t("to_payment", message.chat.id), callback_data="cart+pay"
        )
    )
    await bot.send_message(
        message.chat.id,
        i18n.t("address_updated", message.chat.id),
        reply_markup=markup.as_markup(),
    )
    await state.clear()


async def handle_payment(query: CallbackQuery, bot: Bot):
    if query.message is None:
        raise ValueError

    await bot.send_invoice(
        chat_id=query.message.chat.id,
        title="Payment",
        description="Description",
        currency="RUB",
        provider_token=os.environ["YKASSA_JWT"],
        payload="demo",
        start_parameter="test",
        prices=[LabeledPrice(label="Priced", amount=100 * 100)],
    )


@router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot) -> None:
    await bot.send_message(
        message.chat.id,
        i18n.t("payment_successful", message.chat.id),
    )
    google_sheets_client = tgbot.app.google_sheets.GoogleSheets(
        os.environ["GOOGLE_SHEETS_JWT"]
    )
    # TODO: possible edgecase if deleted item from the cart before paying
    await google_sheets_client.add_row_to_sheet(
        str(os.environ["SPREADSHEET_ID"]),
        values=[
            message.chat.id,
            [
                item
                async for item in web.admin_app.telegram_bot.models.CartItem.objects.filter(
                    chat_id=message.chat.id
                ).all()
            ],
            (
                await web.admin_app.telegram_bot.models.User.objects.filter(
                    chat_id=message.chat.id
                )
                .all()
                .afirst()
            ).delivery_address,  # type: ignore
        ],
    )
    await web.admin_app.telegram_bot.models.CartItem(chat_id=message.chat.id).adelete()


@router.callback_query(CallbackDataPrefixFilter("remove_message"))
async def remove_message_callback(query: CallbackQuery, bot: Bot, state: FSMContext):
    if not query.message:
        raise ValueError
    await query.message.delete()  # type: ignore
    await query.answer()


@router.message(F.text.startswith("/remove_"))
async def remove_item(message: Message, bot: Bot) -> None:
    if message.text is None:
        raise ValueError

    item_id = message.text.split("_")[1]

    user = await sync_to_async(get_object_or_404)(
        web.admin_app.telegram_bot.models.User, chat_id=message.chat.id
    )
    item = await sync_to_async(get_object_or_404)(
        web.admin_app.telegram_bot.models.Item,
        id=int(item_id),
    )
    await web.admin_app.telegram_bot.models.CartItem(
        chat_id=user, item_id=item
    ).adelete()

    await bot.send_message(message.chat.id, i18n.t("item_removed", message.chat.id))


@router.message(Command("cart"))
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
    # TODO: refactor pls
    user = await sync_to_async(get_object_or_404)(
        web.admin_app.telegram_bot.models.User, chat_id=chat_id
    )
    if (
        await sync_to_async(
            web.admin_app.telegram_bot.models.CartItem.objects.filter(chat_id=user)
            .all()
            .count
        )()
        >= 1
    ):
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("checkout", chat_id), callback_data="cart+checkout"
            )
        )

        text = i18n.t("cart.items", chat_id) + "\n"
        async for item in (
            web.admin_app.telegram_bot.models.CartItem.objects.filter(chat_id=chat_id)
            .all()
            .prefetch_related("item_id")
            .all()
        ):
            text += f"\n{item.item_id.name} - x{item.item_amount} - /remove_{item.item_id.id}"
    else:
        text = i18n.t("cart.empty", chat_id)

    await bot.send_message(chat_id, text, reply_markup=markup.as_markup())


@router.callback_query(CallbackDataPrefixFilter("cart"))
async def handle_cart_callback(query: CallbackQuery, bot: Bot, state: FSMContext):
    if not query.data or not query.message:
        raise ValueError

    split = query.data.split("+")
    _type: Literal["add", "confirm", "checkout", "pay"] = split[1]  # type: ignore
    item_id = None
    if len(split) >= 3:
        item_id = split[2]

    if _type == "add" and item_id is not None:
        await select_amount(
            query,
            int(item_id),
            bot,
            state,
        )
    elif _type == "confirm":
        user = await sync_to_async(get_object_or_404)(
            web.admin_app.telegram_bot.models.User, chat_id=query.message.chat.id
        )
        item = await sync_to_async(get_object_or_404)(
            web.admin_app.telegram_bot.models.Item,
            id=(await state.get_data())["item_id"],
        )
        await web.admin_app.telegram_bot.models.CartItem(
            chat_id=user,
            item_id=item,
            item_amount=int((await state.get_data())["amount_of_items"]),
        ).asave()
        await state.clear()
        await bot.send_message(
            query.message.chat.id, i18n.t("added_to_the_cart", query.message.chat.id)
        )
        await tgbot.app.commands.menu.command(query, bot)
    elif _type == "checkout":
        await select_delivery_address(query, bot, state)
    elif _type == "pay":
        await handle_payment(query, bot)
    else:
        return Never

    await query.answer()


# TODO: make db backups
# TODO: make state persistant
