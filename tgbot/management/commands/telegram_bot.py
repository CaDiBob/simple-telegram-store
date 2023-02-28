import logging
import textwrap as tw

from django.conf import settings
from django.core.management.base import BaseCommand

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from clients.models import Client
from ._tools import (
    create_client,
    get_catigories,
    get_category,
)


HANDLE_CATEGORIES, HANDLE_MENU, START_OVER = range(3)


logger = logging.getLogger(__name__)


class TelegramLogsHandler(logging.Handler):

    def __init__(self, chat_id, bot):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


async def start(update, context):

    text = 'Выберете действие:'

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    '📋 Каталог',
                    callback_data='catalog'
                )
            ],
            [
                InlineKeyboardButton(
                    '🛒Корзина',
                    callback_data='cart'
                )
            ],
            [
                InlineKeyboardButton(
                    '🗣 FAQ',
                    callback_data='faq'
                )
            ]
        ]
    )
    tg_user_id = update.message.chat_id
    context.user_data['tg_user_id'] = tg_user_id
    if context.user_data.get(START_OVER):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard
        )

    else:
        tg_user_id = update.message.chat_id
        context.user_data['tg_user_id'] = tg_user_id
        first_name = update.message.chat.first_name

        await create_client(tg_user_id, first_name)

    await update.message.reply_text(
        tw.dedent(f'''
        Здравствуйте {first_name}\!
        Добро пожаловать в наш "Магазин в Телеграме"
        '''),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboard
    )

    context.user_data[START_OVER] = True

    return HANDLE_MENU


async def handle_menu(update, context):
    categories = await get_catigories()

    keyboard = [InlineKeyboardButton(category.name, callback_data=category.id) for category in categories]

    reply_markup = InlineKeyboardMarkup.from_column(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text='Выберите категорию:', reply_markup=reply_markup)
    return HANDLE_CATEGORIES


async def handle_categories(update, context):
    super_category_id = update.callback_query.data
    category = await get_category(super_category_id)
    categories = await get_catigories(category)
    keyboard = [InlineKeyboardButton(category.name, callback_data=category.id) for category in categories]

    reply_markup = InlineKeyboardMarkup.from_column(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text='Выберите категорию:', reply_markup=reply_markup)
    return HANDLE_CATEGORIES



async def cancel(update, context):
    user = update.message.from_user
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


async def handle_error(update, context):
    logger.error(context.error)


def bot_starting():
    tg_token = settings.TG_TOKEN
    tg_chat_id = settings.TG_CHAT_ID
    application = Application.builder().token(tg_token).build()
    logger.addHandler(TelegramLogsHandler(tg_chat_id, application.bot))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
                CallbackQueryHandler(start, pattern=r'Главное меню')
            ],
            HANDLE_CATEGORIES: [
                CallbackQueryHandler(handle_categories, pattern=r'[0-9]')
            ]


        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


class Command(BaseCommand):
    help = "Telegram bot"

    def handle(self, *args, **options):
        bot_starting()
