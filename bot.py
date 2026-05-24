import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from handlers.changing_bot_status import router as changing_bot_status_router
from handlers.offer_handler import router as offer_router
from handlers.restarting_bot import restore_bot_status, periodic_status_check
from handlers.start_help import router as start_help_router
from keyboards.commands import set_commands
from database.models import init_db
# Загружаем переменные из .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
                                            

async def main():
    # Создаем базу данных
    await init_db()

    # Создаём бота и диспетчер
    bot = Bot(token=TOKEN)
    dp = Dispatcher() # диспетчер распределяет события по обработчикам

    await set_commands(bot)
    
    await restore_bot_status(bot)

    asyncio.create_task(periodic_status_check(bot, 60))
    
    # Подключаем роутер с обработчиками
    for router in [
        changing_bot_status_router,
        offer_router,
        start_help_router
    ]:
        dp.include_router(router)

    # Запускаем бота
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())