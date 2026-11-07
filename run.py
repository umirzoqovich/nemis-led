import uvicorn
import webbrowser
import threading
import time
from config import settings

def open_browser():
    time.sleep(1.5)
    try:
        webbrowser.open(f"http://localhost:{settings.PORT}")
    except Exception:
        pass

if __name__ == "__main__":
    print(f"==================================================")
    print(f"🇩🇪 DEUTSCHZENTRUM — TARGET LEAD CRM")
    print(f"==================================================")
    print(f"🌐 Web CRM Dashboard: http://localhost:{settings.PORT}")
    print(f"🎯 Target Formasi:    http://localhost:{settings.PORT}/form")
    print(f"📡 API Hujjatlari:    http://localhost:{settings.PORT}/docs")
    print(f"==================================================\n")
    
    # Brauzerda CRM panelini avtomatik ochish
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)


