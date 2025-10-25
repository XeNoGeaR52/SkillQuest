.PHONY: help build up down logs shell migrate seed test lint clean demo

help:
	@echo "SkillQuest - Available Commands"
	@echo "================================"
	@echo "build      - Build Docker images"
	@echo "up         - Start all services"
	@echo "down       - Stop all services"
	@echo "logs       - View logs from all services"
	@echo "shell      - Open shell in web container"
	@echo "migrate    - Run database migrations"
	@echo "seed       - Seed database with sample data"
	@echo "test       - Run tests"
	@echo "lint       - Run linter"
	@echo "clean      - Remove containers and volumes"
	@echo "demo       - Run complete demo setup"
	@echo "worker-logs - View worker logs"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@echo "Services are ready!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

worker-logs:
	docker-compose logs -f worker

shell:
	docker-compose exec web bash

migrate:
	docker-compose exec web alembic upgrade head
	@echo "Migrations complete!"

seed:
	docker-compose exec web python -m scripts.seed_data
	@echo "Database seeded!"

test:
	docker-compose exec web pytest app/tests/ -v

lint:
	docker-compose exec web ruff check app/ --select E,F,W,I

clean:
	docker-compose down -v
	@echo "All containers and volumes removed!"

demo: build up
	@echo "Starting demo setup..."
	@sleep 8
	@echo "Running migrations..."
	@docker-compose exec web alembic upgrade head
	@echo "Seeding database..."
	@docker-compose exec web python -m scripts.seed_data
	@echo ""
	@echo "================================"
	@echo "Demo setup complete!"
	@echo "================================"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Sample credentials:"
	@echo "  Username: alice | Password: password123"
	@echo ""
	@echo "Run './demo_script.sh' for a complete workflow demo"
