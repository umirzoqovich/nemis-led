import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from config import settings

client = TestClient(app)

def test_all():
    print("1. Testing Web Dashboard (GET /)...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "O&#39;quv Markaz CRM" in res.text or "O'quv Markaz CRM" in res.text or "Target Lead CRM" in res.text
    print("   -> Web Dashboard OK!")

    print("2. Testing Meta Webhook Verification (GET /webhook/meta)...")
    verify_url = f"/webhook/meta?hub.mode=subscribe&hub.challenge=8849204&hub.verify_token={settings.META_VERIFY_TOKEN}"
    res = client.get(verify_url)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res.text == "8849204"
    print("   -> Meta Webhook Verification Handshake OK!")

    print("3. Testing Lead Creation API (POST /api/leads)...")
    payload = {
        "full_name": "Javohir Toshmatov",
        "phone": "+998 94 111 22 33",
        "course": "Arab tili",
        "source": "Instagram Target",
        "ad_name": "Kuzgi qabul 2026",
        "notes": "Hafta oxiri darslariga"
    }
    res = client.post("/api/leads", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    lead = res.json()
    assert lead["id"] is not None
    assert lead["full_name"] == "Javohir Toshmatov"
    print(f"   -> Lead Creation OK! (Lead #{lead['id']})")

    print("4. Testing Status Update API (PATCH /api/leads/{id}/status)...")
    res = client.patch(f"/api/leads/{lead['id']}/status", json={"status": "TRIAL_SCHEDULED", "assigned_to": "Operator Timur"})
    assert res.status_code == 200
    assert res.json()["status"] == "TRIAL_SCHEDULED"
    print("   -> Status Update OK!")

    print("5. Testing Excel Export (GET /export/excel)...")
    res = client.get("/export/excel")
    assert res.status_code == 200
    assert len(res.content) > 1000
    print(f"   -> Excel Export OK! ({len(res.content)} bytes generated)")

    print("6. Testing Public Lead Form (GET /form)...")
    res = client.get("/form?course=Ausbildung&ref=Instagram_Story_Test")
    assert res.status_code == 200
    assert "Nemis Tili" in res.text or "Sinov Darsi" in res.text
    print("   -> Public Lead Form OK!")

    print("7. Testing Lead Notes & Timeline (POST /api/leads/{id}/notes)...")
    res = client.post(f"/api/leads/{lead['id']}/notes", json={"note": "Mijoz bilan gaplashdik, ertaga keladi", "author": "Operator Dilnoza"})
    assert res.status_code == 200
    res_time = client.get(f"/api/leads/{lead['id']}/timeline")
    assert res_time.status_code == 200
    timeline = res_time.json()
    assert len(timeline) >= 1
    print("   -> Lead Notes & Timeline OK!")

    print("8. Testing Static Logo (GET /static/logo.jpg)...")
    res = client.get("/static/logo.jpg")
    assert res.status_code == 200
    assert len(res.content) > 10000
    print("   -> Static Logo OK!")

    print("9. Testing Settings API (GET /api/settings)...")
    res = client.get("/api/settings")
    assert res.status_code == 200
    settings_data = res.json()
    assert "bot_token" in settings_data
    assert "telegram_group_id" in settings_data
    print("   -> Settings API OK!")

    print("10. Testing Confirmed Status Update (PATCH /api/leads/{id}/status)...")
    res = client.patch(f"/api/leads/{lead['id']}/status", json={"status": "CONFIRMED", "assigned_to": "Operator Timur"})
    assert res.status_code == 200
    assert res.json()["status"] == "CONFIRMED"
    print("   -> Confirmed Status Update OK!")

    print("11. Testing Settings Save API (POST /api/settings)...")
    res = client.post("/api/settings", json={
        "bot_token": "9246988890:AAFgIkwRYMgqEX6ZCSJ3QyEG1Hfa-3ua7bc",
        "telegram_group_id": "-5359076030",
        "telegram_channel_url": "https://t.me/start_education"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    # Verify in DB
    import database
    assert database.get_setting("BOT_TOKEN") == "9246988890:AAFgIkwRYMgqEX6ZCSJ3QyEG1Hfa-3ua7bc"
    assert database.get_setting("TELEGRAM_GROUP_ID") == "-5359076030"
    print("   -> Settings Save in SQLite & Memory OK!")

    print("12. Testing Lead Deletion API (DELETE /api/leads/{id})...")
    res = client.delete(f"/api/leads/{lead['id']}")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert database.get_lead_by_id(lead['id']) is None
    print("   -> Lead Deletion OK!")

    print("\n✅ BARCHA TESTLAR MUVAFFAQIYATLI O'TDI!")

if __name__ == "__main__":
    test_all()

