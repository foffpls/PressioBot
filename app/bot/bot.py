import asyncio
import os
from aiogram import Bot, Dispatcher
from app.bot.handlers import calc, order


async def main():
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp = Dispatcher()
    dp.include_router(calc.router)
    dp.include_router(order.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
