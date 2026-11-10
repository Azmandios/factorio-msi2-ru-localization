#!/usr/bin/env bash
# Релиз мода-перевода: bump версии, changelog, коммит, тег, сборка.
#
# Использование:
#   scripts/release.sh <patch|minor|major|X.Y.Z> "Описание изменений"
#
# Примеры:
#   scripts/release.sh patch  "Исправить термин «исследовательский пакет»"
#   scripts/release.sh minor  "Перевод под MSI2 1.1.0"
#   scripts/release.sh 0.2.3  "Явная версия"

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUMP="${1:?Укажите уровень: patch|minor|major|X.Y.Z}"
CHANGES="${2:-}"

read -r -a CUR < <(python3 -c 'import json; v=json.load(open("info.json"))["version"]; print(" ".join(v.split(".")))')

bump_semver() {
  local a=$1 b=$2 c=$3 level=$4
  case "$level" in
    major) echo "$((a+1)).0.0" ;;
    minor) echo "$a.$((b+1)).0" ;;
    patch) echo "$a.$b.$((c+1))" ;;
  esac
}

if [[ "$BUMP" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  NEW="$BUMP"
else
  NEW="$(bump_semver "${CUR[0]}" "${CUR[1]}" "${CUR[2]}" "$BUMP")"
fi

OLD="$(python3 -c 'import json; print(json.load(open("info.json"))["version"])')"
DATE="$(date +%Y-%m-%d)"

# 1. Обновить info.json
python3 - "$NEW" <<'PY'
import json, sys
v = sys.argv[1]
p = "info.json"
d = json.load(open(p))
d["version"] = v
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
open(p, "a").write("\n")
PY

# 2. Дописать блок в changelog.txt
{
  echo "---------------------------------------------------------------------------------------------------"
  echo "Version: $NEW"
  echo "Date: $DATE"
  echo "  Changes:"
  if [ -n "$CHANGES" ]; then
    echo "    - $CHANGES"
  fi
  echo "---------------------------------------------------------------------------------------------------"
} | cat - changelog.txt > changelog.txt.tmp
mv changelog.txt.tmp changelog.txt

# 3. Коммит
git add info.json changelog.txt
git commit -m "chore(release): v$NEW"

# 4. Тег
git tag -a "v$NEW" -m "Release v$NEW"

# 5. Сборка
bash scripts/build.sh

echo
echo "Релиз v$NEW готов (было $OLD)."
echo "Тег v$NEW создан, zip собран в dist/."
echo
echo "Публикация:"
echo "  git push origin main"
echo "  git push origin --tags"
echo "  make publish        # загрузить zip на Mod Portal"
