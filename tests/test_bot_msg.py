import asyncio
import os
import ssl
import certifi
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

load_dotenv()

async def test_telegram():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_GROUP_ID")
    print(f"Testing with Token: {token[:10]}... and Chat ID: {chat_id}")
    
    bot = Bot(token=token)
    try:
        me = await bot.get_me()
        print(f"✅ Bot topildi: @{me.username} ({me.first_name})")
        
        msg = await bot.send_message(
            chat_id=chat_id,
            text="🇩🇪 <b>Nemis Tili Target CRM Boti muvaffaqiyatli ulandi!</b>\n\nTarget reklamalardan kelgan barcha lidlar ushbu guruhga tushadi.",
            parse_mode="HTML"
        )
        print(f"✅ Guruhga xabar muvaffaqiyatli bordi! Message ID: {msg.message_id}")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_telegram())
