.PHONY: help up down logs test migrate shell-api shell-db clean

help:
	@echo "Available commands:"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - Show logs"
	@echo "  make test      - Run tests"
	@echo "  make migrate   - Run database migrations"
	@echo "  make shell-api - Open shell in API container"
	@echo "  make shell-db  - Open PostgreSQL shell"
	@echo "  make clean     - Clean up containers and volumes"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	docker-compose exec api pytest tests/ -v --cov=app

migrate:
	docker-compose exec api alembic upgrade head

shell-api:
	docker-compose exec api /bin/bash

shell-db:
	docker-compose exec postgres psql -U $(DB_USER) -d $(DB_NAME)

clean:
	docker-compose down -v
	docker system prune -f