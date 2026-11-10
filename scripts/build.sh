#!/usr/bin/env bash
# Собирает zip мода-перевода для Mod Portal: dist/<name>_<version>.zip
# Внутри zip лежит папка <name>_<version>, как ожидает Factorio.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

NAME="$(python3 -c 'import json; print(json.load(open("info.json"))["name"])')"
VERSION="$(python3 -c 'import json; print(json.load(open("info.json"))["version"])')"

DIST="$ROOT/dist"
STAGE="$DIST/${NAME}_${VERSION}"
ARCHIVE="$DIST/${NAME}_${VERSION}.zip"

rm -rf "$STAGE" "$ARCHIVE"
mkdir -p "$STAGE"

for entry in info.json changelog.txt locale README.md; do
  if [ ! -e "$ROOT/$entry" ]; then
    echo "Не найден обязательный элемент: $entry" >&2
    exit 1
  fi
  cp -R "$ROOT/$entry" "$STAGE/"
done

(cd "$DIST" && zip -qr "$(basename "$ARCHIVE")" "$(basename "$STAGE")")

echo "Собрано: $ARCHIVE"
