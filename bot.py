"""
Telegram-бот для аналитики видео
"""
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем переменные окружения В ПЕРВУЮ ОЧЕРЕДЬ
load_dotenv()

from app.services.query_service import process_user_query

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Привет! Я бот для аналитики видео.\n\n"
        "Задавай мне вопросы."
    )
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 Как пользоваться ботом:\n\n"
        "Просто напиши свой вопрос на русском языке.\n"
        "Примеры вопросов:\n"
        "• Сколько всего видео есть в системе?\n"
        "• Сколько видео у креатора с id XXX?\n"
        "• Сколько видео вышло с 1 по 5 ноября 2025?\n"
        "• На сколько просмотров выросли все видео 28 ноября?\n"
        "• Сколько разных видео получали просмотры 27 ноября?\n"
    )
    await message.answer(help_text)


@dp.message(F.text)
async def handle_text_message(message: Message):
    """Обработчик всех текстовых сообщений"""
    user_query = message.text.strip()
    
    if not user_query:
        await message.answer("Пожалуйста, задайте вопрос.")
        return
    
    logger.info(f"Получен запрос от пользователя {message.from_user.id}: {user_query}")
    
    try:
        # Отправляем индикатор "печатает..."
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        # Обрабатываем запрос через LLM + SQL
        result = await process_user_query(user_query)
        
        # Отправляем результат
        await message.answer(str(result))
        
        logger.info(f"Отправлен ответ пользователю {message.from_user.id}: {result}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        error_message = (
            "😔 Извините, не удалось обработать ваш запрос.\n"
            "Попробуйте переформулировать вопрос."
        )
        await message.answer(error_message)


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")
    
    # Проверяем наличие необходимых переменных окружения
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY не установлен!")
        return
    
    logger.info("Бот успешно запущен и готов к работе!")
    
    # Запускаем polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем.")
