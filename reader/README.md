# Чтение: «זמן הדרקון»

Серия глав на иврите с заданиями в формате экзамена ульпана (уровень ג).
Содержание — на иврите (`story/bible.md`, `texts/`), чтобы не раскрывать сюжет по-русски.

- `coverage.py chNN.txt` — покрытие знакомыми словами (≥97%): ранги колоды ≤1000 + изученные (`progress.json`) + формы (FORMS/PRES/PARADIGMS/мн. ч./`pealim_forms.json`) + `loanwords.txt`.
- `build_page.py N` — страница `site/chNN.html` из `texts/chNN.txt` + `chNN_questions.json` (шаблон `page_template.html`).
- Публикация: артефакт claude.ai (capability `sample` — Claude проверяет открытые ответы).
  Глава 1: https://claude.ai/artifact/Hou2EWJqhUAp1mFabMdnHV

Цикл главы: автор (агент, промт на иврите) → проверка покрытия → экзаменатор → редактор → сборка → публикация.
`progress.json` обновлять из свежего `.colpkg` пользователя.
