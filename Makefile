.PHONY: up down build test seed lint format clean

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

test:
	cd backend && pytest -v

seed:
	python backend/app/seed.py

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

format:
	cd backend && ruff format .
	cd frontend && npm run format

clean:
	docker compose down -v
