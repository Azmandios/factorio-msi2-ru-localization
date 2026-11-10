#!/usr/bin/env python3
"""Снимок английских строк исходных модов.

Читает установленные zip из каталога модов Factorio, извлекает locale/en/*.cfg
в tools/source/<mod>/en.cfg и пишет tools/source/manifest.json с версией и sha256.

Использование:
    tools/sync-source.py [--from <каталог модов>] [--mods A,B,C]

Путь по умолчанию: ~/Library/Application Support/factorio/mods.
"""

import argparse
import hashlib
import json
import os
import sys
import zipfile

DEFAULT_MODS = [
    "Mining-Space-Industries-II",
    "factorio-crash-site",
    "mferrari_lib",
    "Rocket-Silo-Construction",
]

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(TOOLS_DIR, "source")
MANIFEST_PATH = os.path.join(SOURCE_DIR, "manifest.json")


def log(level, msg):
    print(f"[sync-source] {level} {msg}", file=sys.stderr)


def find_zip(mods_dir, mod_name):
    """Найти zip мода по имени (учитывая суффикс _версия)."""
    if not os.path.isdir(mods_dir):
        return None
    candidates = []
    for entry in os.listdir(mods_dir):
        if entry == f"{mod_name}.zip":
            return os.path.join(mods_dir, entry)
        if entry.startswith(f"{mod_name}_") and entry.endswith(".zip"):
            candidates.append(os.path.join(mods_dir, entry))
    if candidates:
        # последняя версия — наибольший номер; берём последний по лексике как разумную эвристику
        return sorted(candidates)[-1]
    return None


def extract_en_cfg(zip_path, mod_name):
    """Извлечь содержимое всех locale/en/*.cfg в один текст."""
    with zipfile.ZipFile(zip_path) as zf:
        names = []
        for n in zf.namelist():
            # ищем <...>/locale/en/*.cfg (без учёта регистра пути)
            parts = n.split("/")
            if "locale" in parts and "en" in parts and n.endswith(".cfg"):
                # только en, не en-* локали
                idx = parts.index("locale")
                if idx + 1 < len(parts) and parts[idx + 1] == "en":
                    names.append(n)
        if not names:
            return None, None
        chunks = []
        for n in sorted(names):
            data = zf.read(n).decode("utf-8-sig", errors="replace")
            chunks.append(data)
        text = "\n".join(chunks)
        # нормализуем переносы строк в LF
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not text.endswith("\n"):
            text += "\n"
        return text, names


def main():
    ap = argparse.ArgumentParser(description="Снимок английских строк исходных модов")
    ap.add_argument("--from", dest="mods_dir", default=None,
                    help="Каталог модов Factorio (по умолчанию ~/Library/Application Support/factorio/mods)")
    ap.add_argument("--mods", default=",".join(DEFAULT_MODS),
                    help="Список модов через запятую")
    args = ap.parse_args()

    mods_dir = args.mods_dir or os.path.expanduser(
        "~/Library/Application Support/factorio/mods")
    mods = [m.strip() for m in args.mods.split(",") if m.strip()]

    os.makedirs(SOURCE_DIR, exist_ok=True)
    manifest = {"mods": {}, "generated_at": None, "source_dir": mods_dir}

    import datetime
    manifest["generated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    errors = 0
    for mod in mods:
        zip_path = find_zip(mods_dir, mod)
        if zip_path is None:
            log("ERROR", f"zip мода '{mod}' не найден в {mods_dir}")
            errors += 1
            continue

        text, files = extract_en_cfg(zip_path, mod)
        if text is None:
            log("ERROR", f"в '{mod}' нет locale/en/*.cfg")
            errors += 1
            continue

        version = "unknown"
        m = os.path.basename(zip_path)
        if m.startswith(f"{mod}_") and m.endswith(".zip"):
            version = m[len(mod) + 1:-len(".zip")]

        out_path = os.path.join(SOURCE_DIR, mod, "en.cfg")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        key_count = sum(1 for line in text.splitlines() if "=" in line and not line.lstrip().startswith(("#", ";")))

        manifest["mods"][mod] = {
            "version": version,
            "sha256": sha,
            "source_zip": m,
            "locale_files": files,
            "key_count": key_count,
        }
        if key_count == 0:
            log("WARN", f"в '{mod}' не найдено ключей (key_count=0)")
        log("INFO", f"{mod} {version}: sha256={sha[:12]}… keys={key_count} ({', '.join(files)})")

    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    if errors:
        log("ERROR", f"завершено с ошибками: {errors}")
        sys.exit(1)
    log("INFO", f"готово: {len(mods)} модов, манифест {MANIFEST_PATH}")
    sys.exit(0)


if __name__ == "__main__":
    main()
