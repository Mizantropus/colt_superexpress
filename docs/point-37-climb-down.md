# Пункт 37 — спуск (climbing down)

Отложенная доработка.

Сейчас спрайт `climbing_*.png` визуализирует ТОЛЬКО залезание наверх
(inside -> roof). Пункт 37 обрабатывает только этот случай.

## Что нужно позже

1. Появится спрайт спуска (roof -> inside).
2. Встроить его в `changed_level`-анимацию в `frontend/src/stores/game.ts`:
   - сейчас ветка `isClimbingUp === false` — заглушка (плавная смена уровня,
     класс `staying_right`);
   - заменить на реальный класс спуска (например, `climbing_down`) со своим
     таймингом/позой.

## Затрагивает

- `frontend/src/stores/game.ts` — анимация `changed_level` (шаг 4).
- `frontend/src/styles/game.scss` — добавить класс/спрайт спуска.
- `frontend/src/game/constants.ts` — возможно, имя класса спуска.