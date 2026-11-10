#!/usr/bin/env bash
# Smoke-проверка: собирает мод, ставит во временный каталог модов вместе с
# оригинальными модами и прогоняет Factorio --dump-prototype-locale, после чего
# проверяет, что переведённые названия прототипов реально стали русскими.
#
# Переменные окружения:
#   FACTORIO_BIN    путь к бинарнику Factorio
#   FACTORIO_MODS   каталог модов Factorio (источник оригинальных zip и config.ini)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FACTORIO_MODS="${FACTORIO_MODS:-$HOME/Library/Application Support/factorio/mods}"
FACTORIO_BIN="${FACTORIO_BIN:-$HOME/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio}"

if [ ! -x "$FACTORIO_BIN" ] && [ ! -f "$FACTORIO_BIN" ]; then
  echo "[smoke] WARN бинарник Factorio не найден: $FACTORIO_BIN" >&2
  echo "[smoke] WARN задайте FACTORIO_BIN или пропустите проверку" >&2
  exit 0
fi

cd "$ROOT"
bash scripts/build.sh >/dev/null

NAME="$(python3 -c 'import json; print(json.load(open("info.json"))["name"])')"
VERSION="$(python3 -c 'import json; print(json.load(open("info.json"))["version"])')"
ARCHIVE="$ROOT/dist/${NAME}_${VERSION}.zip"

T="$(mktemp -d "${TMPDIR:-/tmp}/msi2-smoke.XXXXXX")"
trap 'rm -rf "$T"' EXIT

mkdir -p "$T/mods" "$T/write"

for p in "$FACTORIO_MODS"/*; do
  ln -s "$p" "$T/mods/$(basename "$p")"
done
rm -f "$T/mods/mod-list.json"
unzip -qo "$ARCHIVE" -d "$T/mods"

python3 - "$T" "$FACTORIO_MODS" "$NAME" <<'PY'
import json, os, sys
T, mods_dir, mod_name = sys.argv[1], sys.argv[2], sys.argv[3]
# mod-list.json: копия пользовательского + наш мод включён
src = os.path.join(mods_dir, "mod-list.json")
data = json.load(open(src))
names = {m["name"] for m in data["mods"]}
if mod_name not in names:
    data["mods"].append({"name": mod_name, "enabled": True})
json.dump(data, open(os.path.join(T, "mods", "mod-list.json"), "w"), indent=2)
# config.ini: write-data во временный каталог, locale=ru
cfg_src = os.path.join(os.path.expanduser("~"), "Library", "Application Support",
                       "factorio", "config", "config.ini")
lines = []
for line in open(cfg_src):
    if line.startswith("write-data="):
        line = f"write-data={T}/write\n"
    if line.startswith("locale="):
        line = "locale=ru\n"
    lines.append(line)
open(os.path.join(T, "config.ini"), "w").writelines(lines)
PY

"$FACTORIO_BIN" --config "$T/config.ini" --mod-directory "$T/mods" \
  --dump-prototype-locale --no-log-rotation >/dev/null 2>&1

python3 "$ROOT/tools/smoke.py" "$T/write/script-output"
echo "[smoke] дамп: $T/write/script-output (каталог удалён по завершении)"
