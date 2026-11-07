import logging
from typing import Dict, Any, Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from config import settings
import database

logger = logging.getLogger(__name__)

STATUS_NAMES = {
    "NEW": "🟢 Yangi kelgan",
    "CONTACTED": "🟡 Bog'lanildi",
    "TRIAL_SCHEDULED": "🔵 Sinov darsiga yozildi",
    "TRIAL_ATTENDED": "🟣 Sinov darsiga keldi",
    "PAID": "✅ To'lov qildi (O'quvchi)",
    "CANCELLED": "❌ Rad etdi / Qiziqmadi"
}

STATUS_ICONS = {
    "NEW": "🟢",
    "CONTACTED": "🟡",
    "TRIAL_SCHEDULED": "🔵",
    "TRIAL_ATTENDED": "🟣",
    "PAID": "✅",
    "CANCELLED": "❌"
}

# Bot instance
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

if settings.BOT_TOKEN:
    session = AiohttpSession(proxy=settings.TELEGRAM_PROXY) if settings.TELEGRAM_PROXY else None
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    dp = Dispatcher()

def get_status_label(status: str) -> str:
    return STATUS_NAMES.get(status, status)

def format_lead_message(lead: Dict[str, Any]) -> str:
    clean_phone = "".join(filter(str.isdigit, lead["phone"]))
    wa_link = f"https://wa.me/{clean_phone}" if clean_phone else ""
    tg_search = f"https://t.me/+{clean_phone}" if clean_phone else ""

    reapply_badge = "\n🚨 <b>DIQQAT! QAYTA MUROJAAT (HOT LEAD)!</b>\n<i>Ushbu o'quvchi nemis tili reklamasini 2-marta bosdi!</i>\n" if lead.get("is_reapplied") else ""

    text = (
        f"🇩🇪 <b>YANGI NEMIS TILI LIDI! (#{lead['id']})</b>\n"
        f"{reapply_badge}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Ismi:</b> {lead['full_name']}\n"
        f"📞 <b>Telefon:</b> <code>{lead['phone']}</code>\n"
        f"🎯 <b>Yo'nalish / Maqsad:</b> {lead.get('course') or 'Nemis tili'}\n"
        f"📋 <b>Tafsilotlar:</b> {lead.get('notes') or '-'}\n"
        f"📣 <b>Target:</b> {lead.get('ad_name') or 'Instagram Ads'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Status:</b> {get_status_label(lead['status'])}\n"
    )
    if lead.get("assigned_to"):
        text += f"👨‍💼 <b>Mas'ul kurator:</b> {lead['assigned_to']}\n"
        
    text += f"⏰ <b>Kelgan vaqti:</b> {lead.get('created_at', '')}\n"
    return text

def build_lead_keyboard(lead_id: int, current_status: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📞 Bog'lanildi", callback_data=f"st:CONTACTED:{lead_id}"),
            InlineKeyboardButton(text="📅 Sinov darsi", callback_data=f"st:TRIAL_SCHEDULED:{lead_id}")
        ],
        [
            InlineKeyboardButton(text="✅ To'lov qildi", callback_data=f"st:PAID:{lead_id}"),
            InlineKeyboardButton(text="❌ Qiziqmadi", callback_data=f"st:CANCELLED:{lead_id}")
        ]
    ]
    if current_status != "NEW":
        buttons.append([InlineKeyboardButton(text="🔄 Yangi holatga qaytarish", callback_data=f"st:NEW:{lead_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_lead_notification(lead: Dict[str, Any]) -> Optional[int]:
    """Sends new lead to the configured Telegram Group or Channel."""
    if not bot or not settings.TELEGRAM_GROUP_ID:
        logger.warning("Telegram Bot yoki TELEGRAM_GROUP_ID sozlanmagan. Xabar yuborilmadi.")
        return None

    try:
        chat_id = settings.TELEGRAM_GROUP_ID.strip()
        text = format_lead_message(lead)
        keyboard = build_lead_keyboard(lead["id"], lead["status"])
        
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        # Save message id
        database.update_lead_telegram_msg_id(lead["id"], msg.message_id)
        return msg.message_id
    except Exception as e:
        logger.error(f"Telegramga xabar yuborishda xatolik: {e}")
        return None

# Register Dispatcher Handlers if bot is initialized
if dp:
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        user_name = message.from_user.full_name
        text = (
            f"Assalomu alaykum, {user_name}!\n\n"
            f"🤖 <b>O'quv markaz Target CRM Botiga xush kelibsiz!</b>\n\n"
            f"Ushbu bot Facebook va Instagram target reklamalaridan kelgan har bir lidni "
            f"darhol ushbu guruhga yetkazadi.\n\n"
            f"📌 <b>Mavjud buyruqlar:</b>\n"
            f"• /stats — Lidlar va konversiya statistikasi\n"
            f"• /leads — Oxirgi kelgan lidlar ro'yxati\n"
            f"• /id — Ushbu guruh yoki profilingiz ID sini bilish\n"
        )
        await message.answer(text, parse_mode="HTML")

    @dp.message(Command("id"))
    async def cmd_id(message: types.Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        await message.answer(
            f"🆔 <b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"👤 <b>Foydalanuvchi ID:</b> <code>{user_id}</code>\n\n"
            f"<i>Ushbu Chat ID ni .env faylidagi TELEGRAM_GROUP_ID ga qo'yishingiz mumkin.</i>",
            parse_mode="HTML"
        )

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        stats = database.get_lead_stats()
        text = (
            f"📊 <b>TARGET LIDLARI STATISTIKASI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 <b>Jami kelgan lidlar:</b> {stats['total']} ta\n"
            f"⚡ <b>Bugun tushgan:</b> {stats['today']} ta\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Yangi (kutilmoqda):</b> {stats['new']} ta\n"
            f"🟡 <b>Bog'lanilgan:</b> {stats['contacted']} ta\n"
            f"🔵 <b>Sinov darsida:</b> {stats['trial']} ta\n"
            f"✅ <b>To'lov qilganlar:</b> {stats['paid']} ta\n"
            f"❌ <b>Rad etganlar:</b> {stats['cancelled']} ta\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 <b>Sotuv konversiyasi:</b> <b>{stats['conversion']}%</b>\n"
        )
        await message.answer(text, parse_mode="HTML")

    @dp.message(Command("leads"))
    async def cmd_leads(message: types.Message):
        leads = database.get_all_leads(limit=10)
        if not leads:
            await message.answer("Hozircha hech qanday lid mavjud emas.")
            return

        text = "📋 <b>Oxirgi kelgan 10 ta lid:</b>\n\n"
        for l in leads:
            icon = STATUS_ICONS.get(l['status'], "⚪")
            text += f"{icon} <b>#{l['id']} {l['full_name']}</b> ({l.get('course') or 'Umumiy'})\n"
            text += f"   📞 {l['phone']} | {get_status_label(l['status'])}\n\n"

        await message.answer(text, parse_mode="HTML")

    @dp.callback_query(F.data.startswith("st:"))
    async def handle_status_change(callback: types.CallbackQuery):
        # Format: st:STATUS:LEAD_ID
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("Noto'g'ri so'rov!")
            return

        _, new_status, lead_id_str = parts
        try:
            lead_id = int(lead_id_str)
        except ValueError:
            await callback.answer("Xatolik yuz berdi!")
            return

        user = callback.from_user
        admin_name = f"@{user.username}" if user.username else user.full_name

        updated = database.update_lead_status(
            lead_id=lead_id,
            new_status=new_status,
            changed_by=admin_name
        )

        if not updated:
            await callback.answer("Lid topilmadi!", show_alert=True)
            return

        # Update Telegram message in-place
        new_text = format_lead_message(updated)
        new_kb = build_lead_keyboard(lead_id, new_status)
        
        try:
            await callback.message.edit_text(new_text, reply_markup=new_kb, parse_mode="HTML")
            await callback.answer(f"Status yangilandi: {get_status_label(new_status)}")
        except Exception as e:
            logger.error(f"Xabarni tahrirlashda xatolik: {e}")
            await callback.answer("Status bazada yangilandi!")

