MOD_NAME := msi2-ru-localization
MOD_VERSION := $(shell python3 -c 'import json; print(json.load(open("info.json"))["version"])')
FACTORIO_MODS ?= $(HOME)/Library/Application Support/factorio/mods
FACTORIO_BIN ?= $(HOME)/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio

.PHONY: check report build install smoke sync-source clean

check:
	@python3 tools/check.py

report:
	@python3 tools/report.py

build:
	@bash scripts/build.sh

install: build
	rm -rf "$(FACTORIO_MODS)/$(MOD_NAME)_$(MOD_VERSION)"
	unzip -qo "dist/$(MOD_NAME)_$(MOD_VERSION).zip" -d "$(FACTORIO_MODS)"
	@echo "Установлено в $(FACTORIO_MODS)/$(MOD_NAME)_$(MOD_VERSION)"

sync-source:
	@python3 tools/sync-source.py --from "$(FACTORIO_MODS)"

smoke: build
	@bash -c 'set -euo pipefail; \
	T=$$(mktemp -d "$(TMPDIR:-/tmp)}/msi2-smoke.XXXXXX"); \
	mkdir -p "$$T/mods" "$$T/write"; \
	for p in "$(FACTORIO_MODS)"/*; do ln -s "$$p" "$$T/mods/$$(basename "$$p")"; done; \
	unzip -qo "dist/$(MOD_NAME)_$(MOD_VERSION).zip" -d "$$T/mods"; \
	rm -f "$$T/mods/mod-list.json"; \
	TOOLS_DIR="$$(pwd)/tools"; \
	SMOKE_TMP="$$T" FACTORIO_BIN="$(FACTORIO_BIN)" FACTORIO_MODS="$(FACTORIO_MODS)" \
		python3 - "$$T" <<"PYEOF"
import json, os, sys, subprocess, shutil
T = sys.argv[1]
mods_dir = os.path.join(T, "mods")
# mod-list: копия пользовательского + наш мод включён
src = os.path.expanduser(os.path.join(os.environ["FACTORIO_MODS"], "mod-list.json"))
data = json.load(open(src))
names = {m["name"] for m in data["mods"]}
if os.environ["MOD_NAME"] not in names:
    data["mods"].append({"name": os.environ["MOD_NAME"], "enabled": True})
json.dump(data, open(os.path.join(mods_dir, "mod-list.json"), "w"), indent=2)
# config: write-data в temp, locale=ru
cfg_src = os.path.expanduser("~/Library/Application Support/factorio/config/config.ini")
lines = []
for line in open(cfg_src):
    if line.startswith("write-data="):
        line = f"write-data={T}/write\n"
    if line.startswith("locale="):
        line = "locale=ru\n"
    lines.append(line)
open(os.path.join(T, "config.ini"), "w").writelines(lines)
print("[smoke] подготовлен каталог", T)
PYEOF
	"$(FACTORIO_BIN)" --config "$$T/config.ini" --mod-directory "$$T/mods" \
		--dump-prototype-locale --no-log-rotation >/dev/null 2>&1; \
	python3 tools/smoke.py "$$T/write/script-output"; \
	RC=$$?; \
	echo "smoke-отчёт: $$T/write/script-output"; \
	rm -rf "$$T"; \
	exit $$RC'

clean:
	rm -rf dist
