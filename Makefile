.PHONY: help up down logs ps build test

help: ## Показать список команд
	echo "Кольт Суперэкспресс — команды разработки:"
	echo "  make up    — собрать и запустить все сервисы"
	echo "  make down  — остановить контейнеры"
	echo "  make logs  — логи всех сервисов"
	echo "  make ps    — статус контейнеров"
	echo "  make build — пересобрать образы"
	echo "  make test  — тесты backend (pytest)"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

build:
	docker compose build

test:
	docker compose run --rm backend pytest