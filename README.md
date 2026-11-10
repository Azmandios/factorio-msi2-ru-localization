# MSI2 — русская локализация

Русский перевод мода **Mining Space Industries II** (MSI2) и его обязательных зависимостей,
которые поставляются только на английском:

- `Mining-Space-Industries-II` — основной мод (миссии, Informatron, дроны, протомолекула);
- `factorio-crash-site` — обломки корабля и предметы из них;
- `mferrari_lib` — общие сущности автора (боссы, зомби, киборги);
- `Rocket-Silo-Construction` — строительство ракетной шахты.

Мод не изменяет оригинальные файлы: он добавляет только `locale/ru/*.cfg`, а за счёт
зависимостей грузится позже оригинала и перекрывает английские строки русскими.

## Требования

- Factorio 2.1+.
- Оригинальный мод `Mining-Space-Industries-II` (зависимость, ставится автоматически).

## Установка

Собрать zip:

```bash
make build
```

Установить в локальную папку модов:

```bash
make install
```

По умолчанию используется `~/Library/Application Support/factorio/mods`.
Другой путь можно передать так:

```bash
make install FACTORIO_MODS="/path/to/factorio/mods"
```

После установки включите мод в списке модов Factorio и перезапустите игру.

## Проверка перевода

- `make check` — паритет ключей, сохранность тегов/плейсхолдеров, остатки английского.
- `make report` — покрытие перевода по секциям и источникам.
- `make smoke` — headless-прогон Factorio и проверка, что названия прототипов реально стали русскими.

Подробнее об обновлении после выхода новой версии MSI2 — в `docs/updating.md`.
Модель релиза, версионирование (semver) и теги — в `docs/release.md`.

## Структура

```
info.json                     манифест мода-перевода
changelog.txt                 история версий
locale/ru/*.cfg               русские строки (по областям и зависимостям)
tools/sync-source.py          снимок английских исходников с хэшем
tools/check.py                валидатор перевода
tools/report.py               отчёт о покрытии
tools/smoke.py                проверка применённых строк через --dump-prototype-locale
scripts/build.sh              сборка zip
docs/glossary.md              словарь терминов
docs/style.md                 правила стиля перевода
docs/updating.md              как обновлять после апдейта MSI2
Makefile                      check / report / build / install / smoke / clean
```

## Лицензия

Наши файлы (инструменты, документация, русские строки) распространяются под
[лицензией MIT](LICENSE). Русские строки — это перевод текстов оригинальных модов,
которые остаются собственностью их авторов:

- Mining Space Industries II — автор MFerrari;
- factorio-crash-site, mferrari_lib, Rocket-Silo-Construction — их авторы.

## English

Russian localization for **Mining Space Industries II** and its required
English-only dependencies: `factorio-crash-site`, `mferrari_lib`,
`Rocket-Silo-Construction`. The mod adds only `locale/ru/*.cfg` overrides and loads
after the original mods, replacing English strings with Russian. Requires Factorio
2.1+ and Mining Space Industries II (auto-installed as a dependency).

Published on the [Mod Portal](https://mods.factorio.com/mod/msi2-ru-localization).
Source: https://github.com/Azmandios/factorio-msi2-ru-localization
