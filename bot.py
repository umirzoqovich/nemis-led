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
    "NEW": "🟢 Yangi lid",
    "CONTACTED": "🟡 Bog'lanildi",
    "CONFIRMED": "🔵 Tasdiqlandi",
    "TRIAL_SCHEDULED": "🟣 Sinov darsida",
    "PAID": "✅ To'lov qildi",
    "CANCELLED": "❌ Rad etdi"
}

STATUS_ICONS = {
    "NEW": "🟢",
    "CONTACTED": "🟡",
    "CONFIRMED": "🔵",
    "TRIAL_SCHEDULED": "🟣",
    "PAID": "✅",
    "CANCELLED": "❌"
}

# Bot instance
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

def init_bot(token: Optional[str] = None, proxy: Optional[str] = None):
    global bot, dp
    t = token or settings.BOT_TOKEN
    p = proxy or settings.TELEGRAM_PROXY
    if t:
        session = AiohttpSession(proxy=p) if p else None
        bot = Bot(token=t, session=session)
        dp = Dispatcher()
        register_handlers(dp)
    else:
        bot = None
        dp = None

def get_status_label(status: str) -> str:
    return STATUS_NAMES.get(status, status)

def format_lead_message(lead: Dict[str, Any]) -> str:
    clean_phone = "".join(filter(str.isdigit, lead["phone"]))
    reapply_badge = "\n🚨 <b>DIQQAT! QAYTA MUROJAAT (HOT LEAD)!</b>\n" if lead.get("is_reapplied") else ""

    text = (
        f"🇩🇪 <b>YANGI NEMIS TILI LIDI! (#{lead['id']})</b>\n"
        f"🏫 <b>Markaz:</b> Start Education\n"
        f"{reapply_badge}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>F.I.SH:</b> {lead['full_name']}\n"
        f"📞 <b>Tel:</b> <code>{lead['phone']}</code>\n"
        f"🎯 <b>Kurs:</b> {lead.get('course') or 'Nemis tili'}\n"
    )
    if lead.get("notes"):
        text += f"📋 <b>Ma'lumot:</b> {lead['notes']}\n"
    if lead.get("ad_name"):
        text += f"📣 <b>Target:</b> {lead['ad_name']}\n"
        
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📊 <b>Status:</b> {get_status_label(lead['status'])}\n"
    if lead.get("assigned_to"):
        text += f"👨‍💼 <b>Mas'ul:</b> {lead['assigned_to']}\n"
    if lead.get("trial_date"):
        text += f"📅 <b>Sinov darsi:</b> {lead['trial_date']}\n"
    if lead.get("cancel_reason"):
        text += f"❌ <b>Rad sababi:</b> {lead['cancel_reason']}\n"
    text += f"⏰ <b>Kelgan vaqti:</b> {lead.get('created_at', '')}\n"
    return text

def build_lead_keyboard(lead_id: int, current_status: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📞 Bog'lanildi", callback_data=f"st:CONTACTED:{lead_id}"),
            InlineKeyboardButton(text="🔵 Tasdiqlandi", callback_data=f"st:CONFIRMED:{lead_id}")
        ],
        [
            InlineKeyboardButton(text="🟣 Sinov darsi", callback_data=f"st:TRIAL_SCHEDULED:{lead_id}"),
            InlineKeyboardButton(text="✅ To'lov qildi", callback_data=f"st:PAID:{lead_id}")
        ],
        [
            InlineKeyboardButton(text="❌ Rad etdi", callback_data=f"st:CANCELLED:{lead_id}")
        ]
    ]
    if current_status != "NEW":
        buttons.append([InlineKeyboardButton(text="🔄 Yangi holatga qaytarish", callback_data=f"st:NEW:{lead_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def check_and_update_migration(e: Exception) -> Optional[str]:
    """If Telegram group was upgraded to supergroup, automatically updates settings and SQLite DB."""
    import re
    msg = str(e)
    match = re.search(r"migrated to a supergroup with id\s+(-?\d+)", msg)
    if match:
        new_id = match.group(1).strip()
        logger.info(f"Telegram guruhi yangi superguruhga o'tdi: {new_id}. Sozlamalar avtomatik yangilanmoqda...")
        settings.TELEGRAM_GROUP_ID = new_id
        try:
            database.set_setting("TELEGRAM_GROUP_ID", new_id)
        except Exception:
            pass
        return new_id
    return None

async def notify_status_update(lead: Dict[str, Any], new_status: str, admin_name: str) -> None:
    """Sends status change notification to the Telegram group."""
    if not bot or not settings.TELEGRAM_GROUP_ID:
        return
    chat_id = settings.TELEGRAM_GROUP_ID.strip()
    status_label = get_status_label(new_status)
    text = (
        f"🔔 <b>STATUS YANGILANDI! (#{lead['id']})</b>\n"
        f"👤 <b>O'quvchi:</b> {lead['full_name']}\n"
        f"📞 <b>Tel:</b> <code>{lead['phone']}</code>\n"
        f"📊 <b>Yangi status:</b> {status_label}\n"
        f"👨‍💼 <b>O'zgartirdi:</b> {admin_name}"
    )
    if lead.get("trial_date") and new_status == "TRIAL_SCHEDULED":
        text += f"\n📅 <b>Sinov darsi:</b> {lead['trial_date']}"
    if lead.get("cancel_reason") and new_status == "CANCELLED":
        text += f"\n❌ <b>Sabab:</b> {lead['cancel_reason']}"

    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    except Exception as e:
        new_id = check_and_update_migration(e)
        if new_id:
            try:
                await bot.send_message(chat_id=new_id, text=text, parse_mode="HTML")
            except Exception:
                pass
        else:
            logger.warning(f"Telegramga status bildirishnomasi yuborishda xatolik: {e}")

async def send_lead_notification(lead: Dict[str, Any]) -> Optional[int]:
    """Sends new lead to the configured Telegram Group or Channel."""
    if not bot or not settings.TELEGRAM_GROUP_ID:
        logger.warning("Telegram Bot yoki TELEGRAM_GROUP_ID sozlanmagan. Xabar yuborilmadi.")
        return None

    chat_id = settings.TELEGRAM_GROUP_ID.strip()
    text = format_lead_message(lead)
    keyboard = build_lead_keyboard(lead["id"], lead["status"])

    try:
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        database.update_lead_telegram_msg_id(lead["id"], msg.message_id)
        return msg.message_id
    except Exception as e:
        new_id = check_and_update_migration(e)
        if new_id:
            try:
                msg = await bot.send_message(
                    chat_id=new_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                database.update_lead_telegram_msg_id(lead["id"], msg.message_id)
                logger.info(f"Xabar yangi superguruhga ({new_id}) muvaffaqiyatli yetkazildi!")
                return msg.message_id
            except Exception as e2:
                logger.error(f"Yangi superguruhga yuborishda xatolik: {e2}")
        logger.error(f"Telegramga xabar yuborishda xatolik: {e}")
        return None

def register_handlers(target_dp: Dispatcher):
    @target_dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        user_name = message.from_user.full_name
        text = (
            f"Assalomu alaykum, {user_name}!\n\n"
            f"🇩🇪 <b>Start Education («Deutsch Mit Nurxo'ja») — Nemis Tili Target CRM Boti!</b>\n\n"
            f"Ushbu bot Instagram va Facebook target reklamalaridan kelgan har bir lidni "
            f"darhol ushbu guruhga yetkazadi.\n\n"
            f"📌 <b>Mavjud buyruqlar:</b>\n"
            f"• /stats — Umumiy statistika va eng ko'p tanlangan yo'nalishlar\n"
            f"• /bugun — Bugungi kelgan lidlar hisoboti\n"
            f"• /find &lt;ism yoki tel&gt; — O'quvchini tezkor qidirish (Masalan: <code>/find Sardor</code>)\n"
            f"• /leads — Oxirgi kelgan 10 ta lid\n"
            f"• /id — Ushbu guruhning Chat ID sini bilish\n"
        )
        await message.answer(text, parse_mode="HTML")

    @target_dp.message(Command("id"))
    async def cmd_id(message: types.Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        await message.answer(
            f"🆔 <b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"👤 <b>Foydalanuvchi ID:</b> <code>{user_id}</code>\n\n"
            f"<i>Ushbu Chat ID ni CRM Sozlamalarida TELEGRAM_GROUP_ID ga qo'yishingiz mumkin.</i>",
            parse_mode="HTML"
        )

    @target_dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        stats = database.get_lead_stats()
        courses_text = ""
        for c_name, count in stats.get("by_course", {}).items():
            courses_text += f"   • {c_name}: <b>{count} ta</b>\n"

        text = (
            f"📊 <b>NEMIS TILI LIDLARI STATISTIKASI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 <b>Jami kelgan lidlar:</b> {stats['total']} ta\n"
            f"⚡ <b>Bugun tushgan:</b> {stats['today']} ta\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Yangi:</b> {stats['new']} ta\n"
            f"🟡 <b>Bog'lanilgan:</b> {stats['contacted']} ta\n"
            f"🔵 <b>Tasdiqlangan:</b> {stats.get('confirmed', 0)} ta\n"
            f"🟣 <b>Sinov darsida:</b> {stats['trial']} ta\n"
            f"✅ <b>To'lov qilganlar:</b> {stats['paid']} ta\n"
            f"❌ <b>Rad etganlar:</b> {stats['cancelled']} ta\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 <b>Sotuv konversiyasi:</b> <b>{stats['conversion']}%</b>\n\n"
            f"🎯 <b>Yo'nalishlar bo'yicha:</b>\n"
            f"{courses_text or '   (Hozircha ma''lumot yo''q)'}"
        )
        await message.answer(text, parse_mode="HTML")

    @target_dp.message(Command("today"))
    @target_dp.message(Command("bugun"))
    async def cmd_today(message: types.Message):
        all_leads = database.get_all_leads(limit=50)
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_leads = [l for l in all_leads if l.get("created_at", "").startswith(today_str)]

        if not today_leads:
            await message.answer(f"📅 Bugun ({today_str}) hali yangi lidlar tushmadi.")
            return

        text = f"⚡ <b>Bugungi lidlar hisoboti ({len(today_leads)} ta):</b>\n\n"
        for l in today_leads:
            icon = STATUS_ICONS.get(l['status'], "⚪")
            text += f"{icon} <b>#{l['id']} {l['full_name']}</b>\n"
            text += f"   📞 {l['phone']} | {l.get('course') or 'Nemis tili'}\n"
            text += f"   Status: {get_status_label(l['status'])}\n\n"

        await message.answer(text, parse_mode="HTML")

    @target_dp.message(Command("find"))
    @target_dp.message(Command("qidiruv"))
    async def cmd_find(message: types.Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("⚠️ Iltimos, qidirish uchun ism yoki telefon raqamini yozing.\nMisol: <code>/find Sardor</code> yoki <code>/find 90123</code>", parse_mode="HTML")
            return

        query = args[1].strip()
        results = database.get_all_leads(search=query, limit=5)

        if not results:
            await message.answer(f"🔍 '<b>{query}</b>' bo'yicha hech qanday lid topilmadi.", parse_mode="HTML")
            return

        text = f"🔍 <b>Qidiruv natijalari ('{query}'):</b>\n\n"
        for l in results:
            text += (
                f"👤 <b>#{l['id']} {l['full_name']}</b>\n"
                f"📞 <code>{l['phone']}</code> | {l.get('course') or 'Nemis tili'}\n"
                f"📊 Status: {get_status_label(l['status'])}\n"
            )
            if l.get("assigned_to"):
                text += f"👨‍💼 Kurator: {l['assigned_to']}\n"
            if l.get("trial_date"):
                text += f"📅 Sinov darsi: {l['trial_date']}\n"
            if l.get("notes"):
                text += f"📝 Izoh: {l['notes']}\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n"

        await message.answer(text, parse_mode="HTML")

    @target_dp.message(Command("leads"))
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

    @target_dp.callback_query(F.data.startswith("st:"))
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

# Initialize on module import if BOT_TOKEN is present
if settings.BOT_TOKEN:
    init_bot()

