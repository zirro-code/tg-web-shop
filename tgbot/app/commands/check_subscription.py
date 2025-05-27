from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from tgbot.app import i18n
from tgbot.app.utils import CallbackDataPrefixFilter

router = Router(name=__name__)

GROUPS_TO_CHECK: tuple[int, ...] = (-1001942325874, -1002563819307)


@router.message(Command("check_subscriptions"))
async def command(message: Message, bot: Bot) -> None:
    if message.from_user is None:
        raise ValueError

    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id, bot)

    if not is_subscribed:
        invite_links = [
            await bot.export_chat_invite_link(group_id) for group_id in GROUPS_TO_CHECK
        ]

        markup = InlineKeyboardBuilder()
        for link in invite_links:
            markup.add(
                InlineKeyboardButton(
                    text=i18n.t("Join", chat_id=message.chat.id), url=link
                )
            )
        markup.add(
            InlineKeyboardButton(
                text=i18n.t("Check Again", chat_id=message.chat.id),
                callback_data="check_subscription",
            )
        )

        await message.reply(
            i18n.t(
                "Please join the group and subscribe to the channel:",
                chat_id=message.chat.id,
            ),
            reply_markup=markup.as_markup(),
        )
        return

    await message.reply(
        i18n.t(key="You're already subscribed!", chat_id=message.chat.id)
    )


@router.callback_query(CallbackDataPrefixFilter("check_subscription"))
async def check_subscription_callback(query: CallbackQuery, bot: Bot):
    if query.message is None:
        raise ValueError

    user_id = query.from_user.id
    is_subscribed = await check_subscription(user_id, bot)

    if is_subscribed:
        # TODO: optimize
        await bot.send_message(
            query.from_user.id,
            i18n.t(
                "You are now a member and subscribed! Great!",
                chat_id=query.message.chat.id,
            ),
        )
        await query.answer()

    else:
        await query.answer(
            i18n.t(
                "You haven't joined yet! Please check again.",
                chat_id=query.message.chat.id,
            ),
        )


async def check_subscription(user_id: int, bot: Bot) -> bool:
    results: list[bool] = []
    try:
        for group_id in GROUPS_TO_CHECK:
            results.append(
                (await bot.get_chat_member(chat_id=group_id, user_id=user_id)).status
                in ("member", "administrator", "creator")
            )

        return all(results)

    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False
