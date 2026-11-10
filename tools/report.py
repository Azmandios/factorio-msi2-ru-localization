#!/usr/bin/env python3
"""Отчёт о покрытии перевода.

По каждому источнику и секции: всего ключей, переведено, процент.
С флагом --missing печатает только отсутствующие ключи.

Использование:
    tools/report.py [--missing]
"""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locale_util as lu


def main():
    missing_only = "--missing" in sys.argv
    source = lu.load_source_keys()
    ru = lu.load_ru_keys()

    # группировка: mod -> section -> (total, done)
    by_mod = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for (section, key), (_, mod) in source.items():
        by_mod[mod][section][0] += 1
        if (section, key) in ru:
            by_mod[mod][section][1] += 1

    total_all = 0
    done_all = 0
    for mod in sorted(by_mod):
        if missing_only:
            # в режиме --missing выводим только отсутствующие ключи этого мода
            for (section, key) in sorted(source):
                if source[(section, key)][1] == mod and (section, key) not in ru:
                    print(f"[report] MISSING {mod}: {section}.{key}")
            continue
        print(f"\n{mod}:")
        for section in sorted(by_mod[mod]):
            total, done = by_mod[mod][section]
            total_all += total
            done_all += done
            pct = 100 * done / total if total else 0
            bar = "=" * round(done / total * 20) if total else ""
            print(f"  [{section:<28}] {done:>3}/{total:<3} {pct:5.1f}% {bar}")

    if not missing_only:
        print(f"\n[report] {done_all}/{total_all} "
              f"({100*done_all/total_all:.1f}%)")

    # отсутствующие ключи списком, если просят или если есть
    missing = [(s, k) for (s, k), (_, m) in source.items() if (s, k) not in ru]
    if missing_only:
        print(f"\n[report] всего отсутствует: {len(missing)}")
    elif missing:
        print(f"\n[report] отсутствует {len(missing)} ключей:")
        for s, k in sorted(missing):
            print(f"  MISSING {s}.{k} ({source[(s, k)][1]})")


if __name__ == "__main__":
    main()
