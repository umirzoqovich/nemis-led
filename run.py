import uvicorn
from config import settings

if __name__ == "__main__":
    print(f"🚀 CRM Tizimi ishga tushmoqda...")
    print(f"🌐 Web CRM Dashboard: http://localhost:{settings.PORT}")
    print(f"📡 API Hujjatlari (Swagger): http://localhost:{settings.PORT}/docs")
    print(f"🤖 Telegram Bot sozlamalarini .env faylida ko'rsatishingiz mumkin.\n")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

