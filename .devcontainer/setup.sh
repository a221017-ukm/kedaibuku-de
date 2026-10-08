#!/usr/bin/env bash
# Runs once when the codespace is created (about 5-8 minutes).
set -e
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU-only build, avoids a 2 GB GPU download
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
mkdir -p data/lake/bronze data/lake/silver data/lake/gold
echo "Setup complete. Run: python --version && docker --version"
