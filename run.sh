#!/bin/bash
# Serverda 1-bosishda ishga tushirish skripti
echo "=================================================="
echo "🇩🇪 DeutschZentrum Nemis Tili CRM (Linux Server)"
echo "=================================================="

if [ ! -d ".venv" ]; then
    echo "Virtual muhit yaratilmoqda..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

python3 run.py
