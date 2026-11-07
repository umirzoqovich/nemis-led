import asyncio
import io
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional, Set

from fastapi import FastAPI, Request, Response, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook

from config import settings
import database
import models
import bot
import meta_service

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("studentbot")

# SSE Subscribers
subscribers: Set[asyncio.Queue] = set()

async def broadcast_event(event_type: str, data: dict):
    msg = json.dumps({"type": event_type, "data": data})
    for queue in list(subscribers):
        try:
            queue.put_nowait(msg)
        except Exception:
            subscribers.discard(queue)

# Background polling task for Telegram bot
polling_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task
    # 1. Initialize SQLite Database
    database.init_db()
    logger.info("Database muvaffaqiyatli ishga tushdi.")

    # 2. Start Telegram Bot polling if token provided
    if bot.bot and bot.dp and settings.BOT_TOKEN:
        logger.info("Telegram Bot polling ishga tushirilmoqda...")
        # Delete webhook if any previously set
        try:
            await bot.bot.delete_webhook(drop_pending_updates=True)
            polling_task = asyncio.create_task(bot.dp.start_polling(bot.bot))
            logger.info("Telegram Bot polling faol holatda!")
        except Exception as e:
            logger.error(f"Telegram Bot pollingni boshlashda xatolik: {e}")
    else:
        logger.warning("BOT_TOKEN ko'rsatilmagan. Telegram bot offline rejimda.")

    yield

    # Teardown
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    if bot.bot:
        await bot.bot.session.close()
    logger.info("Tizim to'xtatildi.")

app = FastAPI(
    title="O'quv Markaz Target CRM API",
    description="Facebook va Instagram reklamalaridan keluvchi lidlarni qabul qilish va Telegram guruhga yuborish tizimi",
    version="1.0.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="templates")

# ==========================================
# WEB CRM DASHBOARD
# ==========================================
@app.get("/form", response_class=HTMLResponse)
async def public_lead_form(
    request: Request,
    course: Optional[str] = None,
    ref: Optional[str] = "Instagram Target",
    ad: Optional[str] = None
):
    """
    Instagram / Facebook Target reklamasidagi 'Batafsil' tugmasiga qo'yiladigan ochiq forma.
    Misol: /form?course=IELTS&ref=Instagram_Story_Noyabr
    """
    campaign_ref = ad or ref or "Instagram Target"
    return templates.TemplateResponse(
        request=request,
        name="lead_form.html",
        context={
            "course": course,
            "ref": campaign_ref
        }
    )

@app.get("/", response_class=HTMLResponse)
async def web_dashboard(request: Request, search: Optional[str] = None):
    stats = database.get_lead_stats()
    all_leads = database.get_all_leads(search=search, limit=200)

    # Group leads by status for Kanban columns
    leads_by_status = {
        "NEW": [],
        "CONTACTED": [],
        "TRIAL_SCHEDULED": [],
        "PAID": [],
        "CANCELLED": []
    }
    for lead in all_leads:
        st = lead["status"]
        if st in leads_by_status:
            leads_by_status[st].append(lead)
        else:
            leads_by_status["NEW"].append(lead)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "stats": stats,
            "leads_by_status": leads_by_status,
            "search": search,
            "bot_active": bool(bot.bot and settings.BOT_TOKEN and settings.TELEGRAM_GROUP_ID)
        }
    )

# ==========================================
# EXCEL EXPORT
# ==========================================
@app.get("/export/excel")
async def export_excel():
    leads = database.get_all_leads(limit=10000)
    wb = Workbook()
    ws = wb.active
    ws.title = "Target Lidlar"

    headers = ["ID", "F.I.SH", "Telefon", "Kurs", "Manba", "Kampaniya nomi", "Status", "Mas'ul admin", "Izoh", "Vaqti"]
    ws.append(headers)

    for l in leads:
        ws.append([
            l["id"],
            l["full_name"],
            l["phone"],
            l.get("course") or "",
            l.get("source") or "",
            l.get("ad_name") or "",
            l.get("status") or "",
            l.get("assigned_to") or "",
            l.get("notes") or "",
            l.get("created_at") or ""
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = "target_lidlar.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==========================================
# REST API: LEADS
# ==========================================
@app.post("/api/leads", response_model=models.LeadResponse)
async def create_new_lead(payload: models.LeadCreate):
    """
    Yangi lidni qabul qilish:
    1. Bazaga yozadi.
    2. Telegram guruhga barcha kerakli tugmalar bilan xabar yuboradi.
    3. Web CRM ga real vaqtda hodisa yuboradi.
    """
    lead = database.create_lead(
        full_name=payload.full_name,
        phone=payload.phone,
        course=payload.course,
        source=payload.source,
        ad_name=payload.ad_name,
        notes=payload.notes
    )

    # Send instant notification to Telegram Group/Channel
    await bot.send_lead_notification(lead)

    # Broadcast to Web Dashboard
    await broadcast_event("NEW_LEAD", lead)

    return lead

@app.get("/api/leads")
async def list_leads(status: Optional[str] = None, search: Optional[str] = None, limit: int = 100):
    return database.get_all_leads(status=status, search=search, limit=limit)

@app.get("/api/leads/{lead_id}")
async def get_lead(lead_id: int):
    lead = database.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lid topilmadi")
    return lead

@app.get("/api/leads/{lead_id}/timeline")
async def get_lead_timeline(lead_id: int):
    return database.get_lead_timeline(lead_id)

@app.post("/api/leads/{lead_id}/notes")
async def add_lead_note(lead_id: int, payload: dict):
    note = payload.get("note", "").strip()
    author = payload.get("author", "Admin")
    if not note:
        raise HTTPException(status_code=400, detail="Izoh matni bo'sh bo'lishi mumkin emas")
    updated = database.add_lead_note(lead_id, note, author)
    if not updated:
        raise HTTPException(status_code=404, detail="Lid topilmadi")
    await broadcast_event("NOTE_ADDED", updated)
    return updated

@app.patch("/api/leads/{lead_id}/status")
async def update_status(lead_id: int, payload: models.LeadUpdateStatus):
    updated = database.update_lead_status(
        lead_id=lead_id,
        new_status=payload.status,
        changed_by=payload.assigned_to or "Admin",
        note=payload.note,
        trial_date=payload.trial_date,
        cancel_reason=payload.cancel_reason
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Lid topilmadi")

    # If telegram message exists, try to update it
    if bot.bot and updated.get("telegram_message_id") and settings.TELEGRAM_GROUP_ID:
        try:
            text = bot.format_lead_message(updated)
            kb = bot.build_lead_keyboard(lead_id, updated["status"])
            await bot.bot.edit_message_text(
                chat_id=settings.TELEGRAM_GROUP_ID.strip(),
                message_id=updated["telegram_message_id"],
                text=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Telegramdagi xabarni yangilashda xatolik: {e}")

    # Broadcast status change to connected browsers
    await broadcast_event("STATUS_UPDATED", updated)

    return updated

@app.get("/api/events")
async def sse_events(request: Request):
    """Real-time Server-Sent Events (SSE) for Web CRM"""
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        subscribers.add(queue)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            subscribers.discard(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ==========================================
# FACEBOOK & INSTAGRAM WEBHOOKS
# ==========================================
@app.get("/webhook/meta")
async def meta_webhook_verification(request: Request):
    """
    Facebook Developers Webhook Verification Handshake.
    Meta 'hub.verify_token' ni tekshirish uchun ushbu GET so'rovni yuboradi.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and verify_token == settings.META_VERIFY_TOKEN:
        logger.info("Meta Webhook muvaffaqiyatli tasdiqlandi!")
        return Response(content=challenge, media_type="text/plain")
    
    logger.warning("Meta Webhook token mos kelmadi!")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhook/meta")
async def meta_webhook_event(request: Request):
    """
    Facebook / Instagram Lead Ads voqealarini qabul qilish.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info(f"Meta Webhook keldi: {body}")

    # Meta Webhook payload parsing
    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            field = change.get("field")
            if field == "leadgen":
                value = change.get("value", {})
                leadgen_id = str(value.get("leadgen_id"))
                page_id = value.get("page_id")
                form_id = value.get("form_id")
                ad_id = value.get("ad_id")

                logger.info(f"Yangi Meta Leadgen aniqlandi: leadgen_id={leadgen_id}")

                # If Access Token is present, fetch full name & phone from Graph API
                lead_data = await meta_service.fetch_leadgen_details(leadgen_id)
                if lead_data and lead_data.get("full_name") and lead_data.get("phone"):
                    lead = database.create_lead(
                        full_name=lead_data["full_name"],
                        phone=lead_data["phone"],
                        course=lead_data.get("course", "Target Ads"),
                        source="Instagram/Facebook Lead Form",
                        ad_name=f"Form #{form_id} (Ad #{ad_id})",
                        notes=f"Meta Leadgen ID: {leadgen_id}"
                    )
                    await bot.send_lead_notification(lead)
                else:
                    # Graph API access token bo'lmasa yoki mock bo'lsa
                    lead = database.create_lead(
                        full_name=f"Meta Mijoz (#{leadgen_id[-4:] if len(leadgen_id)>=4 else leadgen_id})",
                        phone="Meta Graph API Token kiritilmagan",
                        course="Target Ads",
                        source="Instagram Lead Ads",
                        ad_name=f"Form: {form_id}",
                        notes=f"Leadgen ID: {leadgen_id}. .env faylida META_PAGE_ACCESS_TOKEN ni kiriting."
                    )
                    await bot.send_lead_notification(lead)

    return {"status": "ok"}
