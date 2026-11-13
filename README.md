# Кольт Суперэкспресс (Colt Super Express)

Онлайн-версия настольной игры «Кольт Суперэкспресс». Бандиты грабят поезд:
перемещаются по вагонам, стреляют друг в друга и стараются не оказаться в
отцепленном вагоне. Побеждает последний выживший или самый богатый бандит.

## Стек

| Слой | Технология |
| --- | --- |
| Frontend | Vue 3 + Vite + TypeScript + Pinia + Vue Router |
| Backend | FastAPI (Python 3.12) |
| Realtime | WebSocket (Starlette) + Redis Pub/Sub |
| БД | PostgreSQL (история матчей, снапшоты) |
| Кэш/брокер | Redis (комнаты, сессии, таймеры) |

## Структура репозитория

```
.
├── backend/               # FastAPI: движок игры, комнаты, WebSocket
│   ├── app/               # исходный код приложения
│   └── tests/             # тесты
├── frontend/              # Vue 3: сцена, лобби, анимации
│   └── src/
├── docker-compose.yml     # сервисы разработки
├── Makefile               # команды разработки
├── .env.example           # образец переменных окружения
└── README.md
```

## Требования

- Docker и Docker Compose.

## Быстрый старт

1. Скопируйте образец переменных окружения:

   ```bash
   cp .env.example .env
   ```

2. Поднимите все сервисы:

   ```bash
   docker compose up -d --build
   ```

3. Откройте:
   - Frontend: http://localhost:5173
   - Backend (Swagger): http://localhost:8000/docs
   - Healthcheck: http://localhost:8000/health

## Полезные команды

```bash
docker compose up -d --build                  # запустить
docker compose down                           # остановить
docker compose logs -f                        # логи
docker compose ps                             # статус
docker compose run --rm backend pytest        # тесты backend
```

Либо через `make`: `make up`, `make down`, `make logs`, `make test`.

## Правила игры

Полные правила находятся в файле `colt_rules_rus.txt` в корне репозитория.

## Статус разработки

Разработка ведётся по пунктам плана. Назначение каталогов описано выше;
конкретные компоненты добавляются по мере прохождения пунктов.