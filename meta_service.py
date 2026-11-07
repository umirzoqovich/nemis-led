import logging
import httpx
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

async def fetch_leadgen_details(leadgen_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches lead details directly from Facebook Graph API if META_PAGE_ACCESS_TOKEN is provided.
    """
    if not settings.META_PAGE_ACCESS_TOKEN:
        logger.warning("META_PAGE_ACCESS_TOKEN sozlanmagan. Leadgen ma'lumotlarini Meta API dan olib bo'lmaydi.")
        return None

    url = f"https://graph.facebook.com/v21.0/{leadgen_id}"
    params = {"access_token": settings.META_PAGE_ACCESS_TOKEN}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                # Parse field_data array
                # e.g.: [{"name": "full_name", "values": ["Ali Valiyev"]}, {"name": "phone_number", "values": ["+998901234567"]}]
                extracted = {
                    "full_name": "",
                    "phone": "",
                    "course": "Target Ads",
                    "ad_name": f"Meta Leadgen #{leadgen_id}"
                }
                for item in data.get("field_data", []):
                    field_name = item.get("name", "").lower()
                    values = item.get("values", [])
                    val = values[0] if values else ""
                    if "name" in field_name:
                        extracted["full_name"] = val
                    elif "phone" in field_name:
                        extracted["phone"] = val
                    elif "course" in field_name or "kurs" in field_name or "fan" in field_name:
                        extracted["course"] = val

                return extracted
            else:
                logger.error(f"Meta Graph API xatoligi: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            logger.error(f"Meta Graph API ga so'rov yuborishda xatolik: {e}")
            return None

