#!/bin/bash
# Serverda barcha o'zgarishlarni 1-bosishda yangilash skripti
echo "=================================================="
echo "🔄 DeutschZentrum CRM Yangilanmoqda..."
echo "=================================================="

# 1. GitHub dan eng so'nggi kodlarni olish
git pull origin main

# 2. Agar yangi kutubxonalar qo'shilgan bo'lsa o'rnatish
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt --quiet
fi

echo "=================================================="
echo "✅ Kodlar muvaffaqiyatli yangilandi!"
echo "=================================================="

# 3. Agar Docker ishlatayotgan bo'lsangiz:
if command -v docker &> /dev/null && docker compose ps &> /dev/null; then
    echo "Docker konteyneri yangilanmoqda..."
    docker compose up -d --build
    echo "✅ Docker qayta ishga tushdi!"
fi
