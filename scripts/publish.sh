#!/usr/bin/env bash
# Публикация релиза мода на Factorio Mod Portal.
#
# Требования:
#   1. Мод должен быть СОЗДАН на mods.factorio.com через веб-интерфейс
#      (API умеет только добавлять релизы, но не создавать мод).
#   2. Токен API с правом «ModPortal: Upload Mods» — https://factorio.com/profile.
#
# Токен берётся из переменной MOD_PORTAL_TOKEN или файла .mod-portal-token
# (файл в .gitignore, права 600).
#
# Использование:
#   MOD_PORTAL_TOKEN=... scripts/publish.sh
#   # или при наличии .mod-portal-token:
#   scripts/publish.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTAL="https://mods.factorio.com"
INIT_UPLOAD="$PORTAL/api/v2/mods/releases/init_upload"

# --- токен ---
TOKEN="${MOD_PORTAL_TOKEN:-}"
if [ -z "$TOKEN" ] && [ -f .mod-portal-token ]; then
  TOKEN="$(cat .mod-portal-token)"
fi
if [ -z "$TOKEN" ]; then
  echo "ERROR: токен не найден. Задайте MOD_PORTAL_TOKEN или создайте .mod-portal-token" >&2
  exit 1
fi

NAME="$(python3 -c 'import json; print(json.load(open("info.json"))["name"])')"
VERSION="$(python3 -c 'import json; print(json.load(open("info.json"))["version"])')"
ARCHIVE="$ROOT/dist/${NAME}_${VERSION}.zip"

# --- сборка ---
bash scripts/build.sh >/dev/null

# --- 1. init_upload: получить pre-signed URL ---
echo "[publish] init_upload для '$NAME' v$VERSION..."
INIT_RESP="$(curl -sS -X POST "$INIT_UPLOAD" \
  -H "Authorization: Bearer $TOKEN" \
  -F "mod=$NAME")"

UPLOAD_URL="$(printf '%s' "$INIT_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("upload_url",""))' 2>/dev/null || true)"
if [ -z "$UPLOAD_URL" ]; then
  echo "ERROR: init_upload не удался: $INIT_RESP" >&2
  exit 1
fi

# --- 2. finish_upload: загрузить zip ---
echo "[publish] загрузка $ARCHIVE..."
UPLOAD_RESP="$(curl -sS -X POST "$UPLOAD_URL" -F "file=@$ARCHIVE")"

# --- результат ---
if printf '%s' "$UPLOAD_RESP" | grep -q '"success":true'; then
  echo "[publish] OK: $NAME v$VERSION опубликован на Mod Portal."
else
  echo "ERROR: загрузка не удалась: $UPLOAD_RESP" >&2
  exit 1
fi
