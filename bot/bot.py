import os
import asyncio
import httpx
import json

from aiogram import Dispatcher, Bot, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv

load_dotenv()
dp = Dispatcher()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY") 

translations_file = "PracticeBotTranslations.json"
translations_data = {}

def load_translations(filepath):
    global translations_data
    with open(filepath, 'r', encoding='utf-8') as f:
        translations_data = json.load(f)
        
def get_translated_text(key, lang_code="en", **kwargs):
    translation_dict = translations_data.get(key, {})
    text = translation_dict.get(lang_code, translation_dict.get("en", ""))
    return text.format(**kwargs)

def is_button_text_for_key(message_text: str, key: str) -> bool:
    translations_for_key = translations_data.get(key, {})
    for translated_text in translations_for_key.values():
        if translated_text == message_text:
            return True
    return False

load_translations(translations_file)

async def keyboard_buttons(lang_code:str):
    button_user = KeyboardButton(text=get_translated_text("button_user", lang_code))
    button_history = KeyboardButton(text=get_translated_text("button_history", lang_code))
    button_projects = KeyboardButton(text=get_translated_text("button_projects", lang_code))
    button_help = KeyboardButton(text=get_translated_text("button_help", lang_code))
    button_settings = KeyboardButton(text=get_translated_text("button_settings", lang_code))
    button_request = KeyboardButton(text=get_translated_text("button_request", lang_code))

    keyboard_button_markup = ReplyKeyboardMarkup(
        keyboard=[
            [button_user, button_history, button_projects],
            [button_settings, button_request, button_help],
        ],
        resize_keyboard=True
    )
    return keyboard_button_markup

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    language_code = message.from_user.language_code if message.from_user.language_code else "en"

    user_data = {
        "telegram_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "language_code": language_code
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_KEY}/users", json=user_data)
        response.raise_for_status()

    choose_lang_text = get_translated_text("choose_language_text", language_code)

    button_en = InlineKeyboardButton(text="English", callback_data="set_lang:en") 
    button_ru = InlineKeyboardButton(text="Русский", callback_data="set_lang:ru")
    button_hy = InlineKeyboardButton(text="Հայերեն", callback_data="set_lang:hy")

    choose_language_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [button_en, button_ru, button_hy]
        ]
    )

    await message.answer(choose_lang_text, reply_markup=choose_language_markup)

@dp.callback_query(F.data.startswith("set_lang:"))
async def set_language_handler(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{API_KEY}/users/{user_id}/language", 
            json={"language_code": lang}
        )
        response.raise_for_status()

    welcome_text = get_translated_text("welcome_message", lang)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(welcome_text, reply_markup=await keyboard_buttons(lang))

    await callback.answer()

@dp.message(lambda message: is_button_text_for_key(message.text, "button_user"))
async def user_button_handler(message: types.Message):
    user_id = message.from_user.id
    
    user_data = None
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_KEY}/users/{user_id}")
        response.raise_for_status()
        user_data = response.json()

    current_lang = user_data.get("language_code", "en") 

    username = user_data.get("username")
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")
    language_code_from_db = user_data.get("language_code")

    null_text = get_translated_text("null_user", current_lang)

    user_text = (
        f"{get_translated_text('user_info_title', current_lang)}\n\n"
        f"{get_translated_text('username', current_lang)}: {username if username else null_text}\n"
        f"{get_translated_text('first_name', current_lang)}: {first_name if first_name else null_text}\n"
        f"{get_translated_text('last_name', current_lang)}: {last_name if last_name else null_text}\n"
        f"{get_translated_text('language_code', current_lang)}: {language_code_from_db if language_code_from_db else null_text}\n"
    )

    await message.answer(user_text)

@dp.message(lambda message: is_button_text_for_key(message.text, "button_projects"))
async def projects_button_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = None
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_KEY}/users/{user_id}")
        response.raise_for_status()
        user_data = response.json()

    current_lang = user_data.get("language_code", "en")

    project_text = get_translated_text("project_text", current_lang)

    await message.answer(project_text)

@dp.message(lambda message: is_button_text_for_key(message.text, "button_request"))
async def request_button_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = None
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_KEY}/users/{user_id}")
        response.raise_for_status()
        user_data = response.json()

    current_lang = user_data.get("language_code", "en")

    request_text = get_translated_text("request_btn_text", current_lang)

    await message.answer(request_text)

@dp.message(lambda message: is_button_text_for_key(message.text, "button_settings"))
async def settings_button_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = None

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_KEY}/users/{user_id}")
        response.raise_for_status()
        user_data = response.json()

    current_lang = user_data.get("language_code", "en")

    settings_text = get_translated_text("choose_language_text", current_lang)

    button_en = InlineKeyboardButton(text="English", callback_data="set_lang:en") 
    button_ru = InlineKeyboardButton(text="Русский", callback_data="set_lang:ru")
    button_hy = InlineKeyboardButton(text="Հայերեն", callback_data="set_lang:hy")

    settings_language = InlineKeyboardMarkup(
        inline_keyboard=[
            [button_en, button_ru, button_hy]
        ]
    )

    await message.answer(settings_text, reply_markup = settings_language)

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())