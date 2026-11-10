#!/usr/bin/env python3
"""Валидатор русского перевода против исходных английских строк.

Проверяет:
  1) паритет ключей (каждый исходный ключ переведён, лишних ключей нет);
  2) мультимножество плейсхолдеров (__N__, __CONTROL__x__) и тегов
     ([img=…], [item=…], [entity=…], [technology=…], [color=…], [font=…],
     [virtual-signal=…], [fluid=…], [recipe=…]) совпадает с оригиналом;
  3) число переносов строк (\n) в переводе не меньше, чем в оригинале;
  4) UTF-8 без BOM, LF, без пробелов вокруг '=', без хвостовых пробелов;
  5) не осталось английских слов (вне белого списка);
  6) термины глоссария (docs/glossary.json): непереведённые английские термины
     и запрещённые русские варианты.

Использование:
    tools/check.py [--strict]

Код возврата: 0 — ошибок нет; 1 — есть ошибки (или предупреждения при --strict).
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locale_util as lu

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
GLOSSARY_PATH = os.path.join(os.path.dirname(TOOLS_DIR), "docs", "glossary.json")

# Белый список латинских токенов, которые разрешено оставлять в русском тексте.
WHITELIST = {
    "MSI", "HP", "XP", "David", "Nauvis", "N/A", "Factorion", "Compilatron",
    "CTRL", "LV", "Lv", "Sniper", "RPG", "ID", "MSI2", "alt",
    # Названия брендов/модов, оставляемые латиницей
    "Space", "Exploration", "Mining", "Industries",
}

TAG_RE = re.compile(r"\[/?[a-z-]+(?:=[^\]]+)?\]")
PLACEHOLDER_RE = re.compile(r"__[A-Za-z0-9_]+__")
LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z']+")


def find_latin(value):
    """Латинские слова, оставшиеся после вырезания тегов и плейсхолдеров."""
    cleaned = TAG_RE.sub(" ", value)
    cleaned = PLACEHOLDER_RE.sub(" ", cleaned)
    words = []
    for w in LATIN_WORD_RE.findall(cleaned):
        if w in WHITELIST:
            continue
        words.append(w)
    return words


def tokens(value):
    """Мультимножество плейсхолдеров и тегов в значении."""
    t = sorted(PLACEHOLDER_RE.findall(value)) + sorted(TAG_RE.findall(value))
    return t


def check_encoding_and_spacing(name, path, errors, warnings):
    raw = open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{name}: файл содержит BOM — уберите его")
    text = raw.decode("utf-8-sig")
    if "\r\n" in text or "\r" in text:
        errors.append(f"{name}: найден CRLF/CR — используйте LF")
    for i, line in enumerate(text.split("\n"), 1):
        if line != line.rstrip():
            errors.append(f"{name}:{i}: хвостовые пробелы")
        if line.lstrip().startswith(("#", ";", "[")):
            continue
        if "=" in line:
            k, _ = line.split("=", 1)
            if k != k.strip():
                errors.append(f"{name}:{i}: пробел перед '=' в ключе '{k}'")


def load_glossary():
    if not os.path.isfile(GLOSSARY_PATH):
        return None
    import json
    with open(GLOSSARY_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    strict = "--strict" in sys.argv
    errors = []
    warnings = []

    source = lu.load_source_keys()
    ru = lu.load_ru_keys()

    # --- ключи: паритет ---
    src_keys = set(source)
    ru_keys = set(ru)
    missing = src_keys - ru_keys
    extra = ru_keys - src_keys
    for k in sorted(missing):
        errors.append(f"нет перевода: {k[0]}.{k[1]} (источник: {source[k][1]})")
    for k in sorted(extra):
        errors.append(f"лишний ключ (нет в исходниках): {k[0]}.{k[1]} (файл: {ru[k][1]})")

    # --- кодировка/пробелы ---
    if os.path.isdir(lu.RU_DIR):
        for name in sorted(os.listdir(lu.RU_DIR)):
            p = os.path.join(lu.RU_DIR, name)
            if name.endswith(".cfg"):
                check_encoding_and_spacing(name, p, errors, warnings)

    # --- содержимое по совпадающим ключам ---
    for k in sorted(src_keys & ru_keys):
        full = f"{k[0]}.{k[1]}"
        en, mod = source[k]
        ru_val, ru_file = ru[k]

        # пустой перевод
        if not ru_val.strip():
            errors.append(f"пустое значение: {full} ({ru_file})")
            continue

        # токены
        if tokens(ru_val) != tokens(en):
            errors.append(f"теги/плейсхолдеры не совпадают: {full} ({ru_file})")
            continue

        # переносы строк
        en_nl = en.count("\n")
        ru_nl = ru_val.count("\n")
        if ru_nl < en_nl:
            errors.append(f"число \\n уменьшилось ({ru_nl} < {en_nl}): {full} ({ru_file})")

        # оставшаяся латиница
        latin = find_latin(ru_val)
        if latin:
            errors.append(f"английские слова в переводе {sorted(set(latin))}: {full} ({ru_file})")

        # совпадение с оригиналом (не переведено вообще); числовые значения — исключение
        if ru_val.strip() == en.strip() and re.search(r"[A-Za-zА-Яа-яЁё]", ru_val):
            warnings.append(f"перевод совпадает с оригиналом: {full} ({ru_file})")

        # длина: сильное расхождение — индикатор потерянного/лишнего абзаца
        if en and len(en) > 40:
            ratio = len(ru_val) / len(en)
            if ratio < 0.55 or ratio > 1.8:
                warnings.append(
                    f"длина сильно отличается ({ratio:.2f}x): {full} ({ru_file})")

    # --- глоссарий ---
    glossary = load_glossary()
    if glossary is None:
        warnings.append("docs/glossary.json не найден — проверка глоссария пропущена")
    else:
        terms = glossary.get("terms", [])
        for k in sorted(src_keys & ru_keys):
            ru_val = ru[k][0]
            for term in terms:
                en_term = term.get("en")
                if en_term and re.search(r"\b" + re.escape(en_term) + r"\b", ru_val):
                    errors.append(
                        f"непереведённый термин '{en_term}': {k[0]}.{k[1]}")
                for bad in term.get("forbidden", []):
                    if re.search(re.escape(bad), ru_val):
                        errors.append(
                            f"запрещённый вариант '{bad}' (нужно '{term.get('ru')}'): "
                            f"{k[0]}.{k[1]}")

    # --- вывод ---
    n_err = len(errors)
    n_warn = len(warnings)
    for line in errors:
        print(f"[check] ERROR {line}")
    for line in warnings:
        print(f"[check] WARN {line}")

    total = len(source)
    done = len(src_keys & ru_keys)
    print(f"[check] coverage={done}/{total} ({100*done/total:.1f}%) "
          f"errors={n_err} warnings={n_warn}")

    if strict and n_warn:
        print("[check] --strict: предупреждения считаются ошибками")
        sys.exit(1)
    if n_err:
        sys.exit(1)
    print("[check] OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
