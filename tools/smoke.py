#!/usr/bin/env python3
"""Проверка применённых строк через дамп Factorio --dump-prototype-locale.

Сверяет, что названия прототипов, которые мы переводим, реально стали русскими
в игре (а не остались английскими из-за неверного порядка модов).

Использование:
    tools/smoke.py <каталог script-output>

Код возврата: 0 — латинских остатков нет; 1 — есть остатки (или мод не загрузился).
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locale_util as lu

# Имена прототипов, которые гарантированно регистрируются на data-этапе.
# Проверяются жёстко: обязаны быть кириллическими.
MUST_BE_RUSSIAN = {
    "entity": [
        "msi_companion_droid", "msi_companion_synthetic",
        "msi_protomolecule_spawner", "msi-ore-solaz",
        "crash-site-lab-broken", "crash-site-generator", "big-ship-wreck-1",
        "maf-boss-biter", "compilatron",
    ],
    "item": [
        "msi_container", "msi_sniper_rifle", "msi_portable_technology_data",
        "railgun", "computer", "small-plane",
    ],
    "technology": [
        "msi_companion_droid_tech-1", "msi_companion_synthetic_tech-1",
        "msi_protomolecule_scan", "msi_sniper_rifle",
    ],
    "mod-setting": [
        "msi-difficulty-level", "msi-enemy-hp-multiplier",
        "msi-disable-camera-popup",
    ],
}

CYRILLIC = re.compile(r"[А-Яа-яЁё]")
# Разрешённые латинские бренды, которые могут входить в русское название.
BRAND_OK = re.compile(r"\b(MSI|David|Nauvis|HP|XP)\b")

DUMP_FILES = {
    "entity": "entity-locale.json",
    "item": "item-locale.json",
    "technology": "technology-locale.json",
    "mod-setting": "mod-setting-locale.json",
}


def is_russian(value):
    """Значение считается русским, если в нём есть кириллица,
    либо это «чистый бренд/число» без содержательного английского."""
    if CYRILLIC.search(value):
        return True
    # нет кириллицы: допускаем только короткие бренды/числа
    stripped = BRAND_OK.sub(" ", value)
    stripped = re.sub(r"[0-9.,\-:/%() ]+", " ", stripped)
    return not re.search(r"[A-Za-z]{3,}", stripped)


def main():
    dump_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if not dump_dir or not os.path.isdir(dump_dir):
        print("[smoke] ERROR не указан каталог script-output")
        sys.exit(2)

    errors = []
    warnings = []
    total_checked = 0
    total_matched = 0

    for category, fname in DUMP_FILES.items():
        path = os.path.join(dump_dir, fname)
        if not os.path.isfile(path):
            warnings.append(f"нет файла дампа {fname}")
            continue
        data = json.load(open(path, encoding="utf-8"))
        names = data.get("names", {})
        for name in MUST_BE_RUSSIAN.get(category, []):
            total_checked += 1
            if name not in names:
                warnings.append(f"{category}.{name} отсутствует в дампе (runtime-сущность?)")
                continue
            total_matched += 1
            value = names[name]
            if not is_russian(value):
                errors.append(f"{category}.{name} остался латинским: '{value}'")

    # Глобальный скан: латинские названия, которые мы переводим, но они остались.
    ru_keys = lu.load_ru_keys()
    target_names = set()
    for (section, key) in ru_keys:
        if section in ("entity-name", "item-name", "technology-name", "mod-setting-name"):
            target_names.add(key)

    for category, fname in DUMP_FILES.items():
        path = os.path.join(dump_dir, fname)
        if not os.path.isfile(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        for name, value in data.get("names", {}).items():
            base = re.sub(r"-\d+$", "", name)  # технологии с уровнями: -1, -2
            if name in target_names or base in target_names:
                if not is_russian(value):
                    errors.append(f"{category}.{name} (наш ключ) остался латинским: '{value}'")

    if total_matched == 0 and total_checked > 0:
        errors.append(
            "ни один целевой прототип не найден в дампе — мод, похоже, не загрузился "
            "(проверьте mod-list.json и зависимости)")

    for line in errors:
        print(f"[smoke] ERROR {line}")
    for line in warnings:
        print(f"[smoke] WARN {line}")
    print(f"[smoke] проверено прототипов: {total_checked}, совпало в дампе: "
          f"{total_matched}, ошибок: {len(errors)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
