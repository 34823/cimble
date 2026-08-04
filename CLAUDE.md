# CLAUDE.md

`cimble` — open-source Python-тулкит: прогрессивная, самодробящаяся память проекта для
Claude Code. Методология описана в `docs/methodology.md` и `README.md` — не дублирую здесь.

## Запуск

```bash
# из корня cimble/ (venv уже настроен в .venv)
cimble init <project>                        # стартовый CLAUDE.md
cimble init <project> --topic <slug>         # вынести раздел в memory/<slug>.md
cimble init <project> --index                # вынести раздел-индекс в memory/index.md
cimble check <project>                       # что превысило порог (раздел/файл/backlink)
cimble check <project> --strict              # то же, но exit non-zero (для CI)
cimble check <project> --check-wikilinks
```

Тесты: `pytest` из корня (`tests/`, покрывает `check`, `init`, wikilinks).

## Структура

- `cimble/` — сам пакет (`cli.py`, `init.py`, `check.py`, `config.py`, `templates/`).
- `hooks/` — `check_memory_hook.py` + `hooks.json`, PostToolUse-хук на Edit/Write.
- `skills/cimble/` — скилл для Claude Code (`/cimble`).
- `examples/` — вымышленные иллюстрации стадий 1–3, без реальных данных.
- `docs/methodology.md` — полное описание для внешних читателей.

## Что нельзя

- Не класть в `examples/` реальные данные из других проектов (`alpha-search`, `gemgymbot`) —
  только вымышленные структуры, это публичный репозиторий.
- Не хардкодить пороги 120/40 в код — они настраиваются через CLI-флаг /
  `CIMBLE_*` env / `cimble.toml`, дефолты только запасной вариант.

## Публикация

Репозиторий — github.com/34823/cimble, публичный. Проверять дифф на секреты/личные данные
перед пушем строже обычного.
