import asyncio, os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


async def main():
    async with Bot(os.environ["TELEGRAM_TOKEN"]) as bot:
        me = await bot.get_me()
        print("Connected as @" + me.username)


asyncio.run(main())