"""Общие утилиты для работы с locale-файлами Factorio (.cfg)."""

import os

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(TOOLS_DIR, "source")
RU_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "locale", "ru")


def parse_cfg(text):
    """Разобрать текст .cfg в упорядоченный список (section, key, value).

    Возвращает list[tuple[str, str, str]] в порядке следования.
    Строки без '=' (кроме заголовков секций) и комментарии пропускаются.
    """
    result = []
    section = None
    for raw_line in text.split("\n"):
        line = raw_line
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith(";"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            result.append((section, key, value))
    return result


def parse_file(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return parse_cfg(f.read())


def load_source_keys():
    """Все ключи исходных модов: {(section, key): (value, mod)}."""
    out = {}
    for mod in sorted(os.listdir(SOURCE_DIR)):
        p = os.path.join(SOURCE_DIR, mod, "en.cfg")
        if not os.path.isfile(p):
            continue
        for section, key, value in parse_file(p):
            full = f"{section}.{key}"
            out[(section, key)] = (value, mod)
    return out


def load_ru_keys():
    """Все ключи нашего перевода: {(section, key): (value, file)}."""
    out = {}
    if not os.path.isdir(RU_DIR):
        return out
    for name in sorted(os.listdir(RU_DIR)):
        p = os.path.join(RU_DIR, name)
        if not os.path.isfile(p) or not name.endswith(".cfg"):
            continue
        for section, key, value in parse_file(p):
            out[(section, key)] = (value, name)
    return out
