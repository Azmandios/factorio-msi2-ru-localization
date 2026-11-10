# AGENTS.md

> Карта проекта для AI-агентов. Обновляйте при значительных изменениях структуры.

## Обзор проекта

Мод-перевод на русский язык для Factorio: локализует `Mining-Space-Industries-II`
и его обязательные зависимости, у которых нет русской локали
(`factorio-crash-site`, `mferrari_lib`, `Rocket-Silo-Construction`).

Мод не изменяет оригиналы: содержит только `locale/ru/*.cfg`. За счёт зависимости
на MSI2 грузится позже оригинала и перекрывает английские строки русскими
(строки локали загружаются в порядке зависимостей, последняя побеждает).

## Технологический стек

- **Язык:** локализация Factorio (`.cfg`), инструменты на Python 3.
- **Платформа:** Factorio 2.1+.
- **Проверка:** headless-прогон `factorio --dump-prototype-locale`.

## Структура проекта

```
info.json                     манифест мода-перевода
changelog.txt                 история версий
locale/ru/                    русские строки (разбиты по областям)
  msi-labels.cfg              [labels] — GUI и сообщения
  msi-entities.cfg            [entity-*] — сущности MSI2
  msi-items.cfg               [item-*] — предметы MSI2
  msi-tech.cfg                [technology-*] — технологии MSI2
  msi-settings.cfg            [mod-setting-*], [controls] — настройки MSI2
  msi-informatron-menu.cfg    [Mining-Space-Industries-II] menu_*/title_*
  msi-informatron-pages.cfg   интерфейсные страницы Informatron
  msi-informatron-missions.cfg  тексты миссий (MI_*, M_*, боссы)
  deps-crash-site.cfg         перевод factorio-crash-site
  deps-mferrari-lib.cfg       перевод mferrari_lib
  deps-rocket-silo.cfg        перевод Rocket-Silo-Construction
tools/
  sync-source.py              снимок английских исходников с sha256
  locale_util.py              общий парсер locale-файлов
  check.py                    валидатор перевода
  report.py                   отчёт о покрытии
  smoke.py                    проверка применённых строк по дампу
scripts/
  build.sh                    сборка zip
  smoke.sh                    оркестрация smoke-проверки
docs/
  glossary.md / glossary.json словарь терминов (+ автопроверка)
  style.md                    правила стиля
  updating.md                 как обновлять после апдейта MSI2
  qa/                         отчёты проверок и чек-лист ручного QA
Makefile                      check / report / build / install / smoke / sync-source / clean
```

## Ключевые точки входа

| Файл | Назначение |
|------|------------|
| `info.json` | Имя, версия, зависимости (MSI2 обязательная, остальные `?`) |
| `locale/ru/*.cfg` | Единственный артефакт, попадающий в игру |
| `tools/check.py` | Главный контроль качества перевода |
| `tools/sync-source.py` | Переснятие исходников при обновлении модов |

## Правила для агента

- Источник истины английских строк — `tools/source/<мод>/en.cfg` (не править руками).
- Один ключ переводится ровно один раз; дубли между модами (например
  `maf-boss-biter` в MSI2 и mferrari_lib) переводятся одной строкой.
- Термины — только из `docs/glossary.md`, стиль — из `docs/style.md`.
- Теги `[img=…]`, `[item=…]`, плейсхолдеры `__1__`, `__CONTROL__x__` и `\n`
  переносить без изменений.
- Перед коммитом — `make check` (0 ошибок, 100% покрытие) и `make smoke`.
- Не переводить: `MSI`, `David`, `Nauvis` (в тексте транслитерируется как «Наувис»),
  коды миссий и идентификаторы внутри тегов.
- После обновления оригинальных модов — `make sync-source` и `make report --missing`.
