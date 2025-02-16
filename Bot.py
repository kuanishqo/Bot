import asyncio
import logging
import os
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from flask import Flask

# Загружаем токен и ID группы из переменных окружения
TOKEN = os.getenv("TOKEN")
GROUP_ID = os.getenv("GROUP_ID")  # Вставь ID своей группы

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Веб-сервер для UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = threading.Thread(target=run)
    server.start()

# Определяем состояния для FSM (Finite State Machine)
class SupportForm(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone_number = State()
    waiting_for_question = State()

# Клавиатура
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📩 Задать вопрос")],
        [KeyboardButton(text="ℹ️ О нас")]
    ],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await message.answer("Привет! Введите ваше *Имя и Фамилию*:", parse_mode="Markdown")
    await state.set_state(SupportForm.waiting_for_full_name)

# Получение имени
@dp.message(SupportForm.waiting_for_full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Теперь введите ваш *номер телефона*:", parse_mode="Markdown")
    await state.set_state(SupportForm.waiting_for_phone_number)

# Получение номера
@dp.message(SupportForm.waiting_for_phone_number)
async def get_phone_number(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer("Спасибо! Теперь можете задать вопрос.", reply_markup=menu_keyboard)
    await state.set_state(SupportForm.waiting_for_question)

# Отправка вопроса в группу поддержки
@dp.message(SupportForm.waiting_for_question)
async def forward_question(message: Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = user_data.get("full_name", "Не указано")
    phone_number = user_data.get("phone_number", "Не указан")
    user_name = f"@{message.from_user.username}" if message.from_user.username else f"[{full_name}](tg://user?id={message.from_user.id})"
    question = message.text

    support_message = (
        f"🆕 *Новый вопрос!*\n\n"
        f"👤 *Имя:* {full_name}\n"
        f"📞 *Телефон:* {phone_number}\n"
        f"🔗 *Профиль:* {user_name}\n"
        f"❓ *Вопрос:* {question}\n\n"
        f"👤 ID: `{message.from_user.id}`"
    )

    if GROUP_ID:
        await bot.send_message(GROUP_ID, support_message, parse_mode="Markdown")
        await message.answer("Ваш вопрос отправлен в поддержку!", reply_markup=menu_keyboard)
    else:
        await message.answer("Ошибка: GROUP_ID не задан. Сначала получите ID группы!")

# Команда "О нас"
@dp.message(lambda message: message.text == "ℹ️ О нас")
async def about_us(message: Message):
    await message.answer("Мы – служба поддержки. Задайте вопрос, и наши админы ответят вам!")

# Функция получения ID группы
@dp.message()
async def get_group_id(message: Message):
    if message.chat.type in ["group", "supergroup"]:
        await message.answer(f"ID этой группы: `{message.chat.id}`", parse_mode="Markdown")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()  # Запускаем веб-сервер для UptimeRobot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
