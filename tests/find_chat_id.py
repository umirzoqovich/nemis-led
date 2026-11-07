import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

async def find_chats():
    token = os.getenv("BOT_TOKEN")
    current_id = os.getenv("TELEGRAM_GROUP_ID")
    bot = Bot(token=token)
    
    print(f"Baza sozlamasidagi Chat ID: {current_id}")
    
    # 1. Hozirgi ID ni tekshirish
    try:
        chat = await bot.get_chat(chat_id=current_id)
        print(f"👉 Hozirgi ulangan chat: '{chat.title}' (Turi: {chat.type}, ID: {chat.id})")
    except Exception as e:
        print(f"❌ Hozirgi Chat ID bo'yicha topilmadi: {e}")

    # 2. Agar -100 qo'shilsa (Supergroup)
    if not current_id.startswith("-100") and current_id.startswith("-"):
        supergroup_id = "-100" + current_id[1:]
        try:
            chat2 = await bot.get_chat(chat_id=supergroup_id)
            print(f"💡 TO'G'RI SUPERGROUP ID: '{chat2.title}' (ID: {chat2.id})")
        except Exception as e:
            print(f"ℹ️ Supergroup (-100...): {e}")

    # 3. Oxirgi botga kelgan xabarlardan barcha guruhlarni ko'rish
    try:
        updates = await bot.get_updates(limit=10)
        print(f"\n📋 Bot oxirgi ko'rgan chatlar ({len(updates)} ta yangilanish):")
        seen_chats = set()
        for u in updates:
            msg = u.message or u.channel_post or u.my_chat_member
            if msg and hasattr(msg, "chat"):
                c = msg.chat
                if c.id not in seen_chats:
                    seen_chats.add(c.id)
                    print(f"   • Nomi: '{c.title or c.full_name}' | Turi: {c.type} | Aniq ID: {c.id}")
    except Exception as e:
        print(f"Updates xatolik: {e}")

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(find_chats())

