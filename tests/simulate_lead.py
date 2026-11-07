"""
Target reklamalaridan keladigan lidlarni sinab ko'rish skripti
"""
import sys
import os
import asyncio
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from models import LeadCreate

def simulate():
    print("=== O'QUV MARKAZ CRM TEST BOSHLANDI ===")
    database.init_db()

    # 1. Sinov uchun bir nechta haqiqiy target lidlarini yaratamiz
    sample_leads = [
        {
            "full_name": "Azizbek Yusupov",
            "phone": "+998 90 123 45 67",
            "course": "IELTS 7.5+ Intesiv",
            "source": "Instagram Story Target",
            "ad_name": "Target_IELTS_Kuz_Kampaniya_01",
            "notes": "Ertalabki guruh bo'lsa darsga qatnasha oladi"
        },
        {
            "full_name": "Madina Karimova",
            "phone": "+998 93 987 65 43",
            "course": "General English (Elementary)",
            "source": "Instagram Reels Ads",
            "ad_name": "Reels_Ingliz_Tili_Chegirma",
            "notes": "Farzandi uchun so'radi, dushanba kuni keladi"
        },
        {
            "full_name": "Shohruh Mirzayev",
            "phone": "+998 97 555 44 33",
            "course": "IT Dasturlash (Python Backend)",
            "source": "Facebook Lead Form",
            "ad_name": "FB_IT_Kasblar_Kuz",
            "notes": "Noldan boshlamoqchi"
        },
        {
            "full_name": "Nigora Alimova",
            "phone": "+998 91 222 33 11",
            "course": "Pre-IELTS",
            "source": "Instagram Direct",
            "ad_name": "Instagram_Feed_Target",
            "notes": "Do'sti tavsiya qilgan"
        }
    ]

    created_ids = []
    for item in sample_leads:
        lead = database.create_lead(
            full_name=item["full_name"],
            phone=item["phone"],
            course=item["course"],
            source=item["source"],
            ad_name=item["ad_name"],
            notes=item["notes"]
        )
        print(f"✅ Lid yaratildi: ID #{lead['id']} - {lead['full_name']} ({lead['course']})")
        created_ids.append(lead["id"])

    # 2. Statuslarini o'zgartirishni sinab ko'ramiz
    if len(created_ids) >= 3:
        database.update_lead_status(created_ids[1], "CONTACTED", changed_by="Admin Anvar", note="Telefon qildik, javob berdi")
        database.update_lead_status(created_ids[2], "TRIAL_SCHEDULED", changed_by="Admin Malika", note="Ertaga 16:00 ga yozildi")
        database.update_lead_status(created_ids[3], "PAID", changed_by="Admin Anvar", note="1 oylik to'lov amalga oshirildi")

    # 3. Statistikani tekshiramiz
    stats = database.get_lead_stats()
    print("\n--- CRM STATISTIKASI ---")
    print(f"Jami lidlar: {stats['total']}")
    print(f"Bugun kelgan: {stats['today']}")
    print(f"Yangi: {stats['new']}")
    print(f"Bog'lanildi: {stats['contacted']}")
    print(f"Sinov darsi: {stats['trial']}")
    print(f"To'lov qildi: {stats['paid']}")
    print(f"Konversiya: {stats['conversion']}%")
    print("=======================================")

if __name__ == "__main__":
    simulate()

