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
from loguru import logger

import tgbot
import tgbot.app
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
    if message.text is None or message.text.isalnum():
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
    await web.admin_app.telegram_bot.models.User(message.text).asave(
        update_fields=["delivery_address"]
    )
    markup = InlineKeyboardBuilder()
    markup.add(
        InlineKeyboardButton(
            text=i18n.t("to_payment", message.chat.id), callback_data="cart.pay"
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
        prices=[LabeledPrice(label="Priced", amount=10000)],
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


@router.message(F.contains("remove_"))
async def remove_item(message: Message, bot: Bot) -> None:
    if message.text is None:
        raise ValueError

    item_id = message.text.split("_")[1]

    await web.admin_app.telegram_bot.models.CartItem(
        chat_id=message.chat.id, item_id=int(item_id)
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
    if (
        await sync_to_async(  # type: ignore
            web.admin_app.telegram_bot.models.CartItem.objects.filter(chat_id=chat_id)
            .all()
            .count()  # type: ignore
        )
        >= 1
    ):
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("checkout", chat_id), callback_data="cart+checkout"
            )
        )

        text = i18n.t("cart.items", chat_id) + "\n"
        async for item in web.admin_app.telegram_bot.models.CartItem.objects.filter(
            chat_id=chat_id
        ).all():
            text += (
                f"\n{item.item_id.name} - x{item.item_amount} - /remove_{item.item_id}"
            )
    else:
        text = i18n.t("cart.empty", chat_id)

    await bot.send_message(
        chat_id, i18n.t("cart", chat_id), reply_markup=markup.as_markup()
    )


@router.callback_query(CallbackDataPrefixFilter("cart"))
async def handle_cart_callback(query: CallbackQuery, bot: Bot, state: FSMContext):
    if not isinstance(query.message, str):
        raise ValueError

    split = query.message.split("+")
    _type: Literal["add", "confirm", "checkout", "pay"] = split[1]  # type: ignore
    item_id = split[2]

    if _type == "add":
        await select_amount(
            query,
            int(item_id),
            bot,
            state,
        )
    elif _type == "confirm":
        await web.admin_app.telegram_bot.models.CartItem(
            chat_id=query.message.chat.id,
            item_id=(await state.get_data())["item_id"],
            item_amount=int((await state.get_data())["amount_of_items"]),
        ).asave()
        await state.clear()
        await bot.send_message(
            query.message.chat.id, i18n.t("added_to_the_cart", query.message.chat.id)
        )
    elif _type == "checkout":
        await select_delivery_address(query, bot, state)
    elif _type == "pay":
        ...
    else:
        return Never


# TODO: make db backups
