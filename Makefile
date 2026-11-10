MOD_NAME := msi2-ru-localization
MOD_VERSION := $(shell python3 -c 'import json; print(json.load(open("info.json"))["version"])')
FACTORIO_MODS ?= $(HOME)/Library/Application Support/factorio/mods
FACTORIO_BIN ?= $(HOME)/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio

.PHONY: check report build install smoke sync-source release clean

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

# Релиз: bump версии + changelog + коммит + тег + сборка.
# Пример: make release BUMP=patch CHANGES="Исправить термин"
release:
	@bash scripts/release.sh "$(BUMP)" "$(CHANGES)"

smoke:
	@FACTORIO_BIN="$(FACTORIO_BIN)" FACTORIO_MODS="$(FACTORIO_MODS)" bash scripts/smoke.sh

clean:
	rm -rf dist
