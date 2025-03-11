.PHONY: setup install run test clean docker-build docker-run

setup:
	@poetry run python setup.py

install:
	@poetry install

run:
	@DEBUG=1 poetry run flask run --debug --reload --extra-files "templates/:static/"

initdb:
	@poetry run flask initdb

clean:
	@rm -f wood_planner.db
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

docker-build:
	@docker-compose build

docker-run:
	@docker-compose up -d

docker-stop:
	@docker-compose down

# Development tools
lint:
	@poetry run flake8 .

format:
	@poetry run black .
	@poetry run isort .

run-debug:
	@DEBUG=1 poetry run flask run --debug --reload --extra-files "templates/:static/"

migrate:
	@poetry run python run_migrations.py

help:
	@echo "Available commands:"
	@echo "  setup         - Set up the project (install dependencies, initialize database)"
	@echo "  run           - Run the Flask application with auto-reload on file changes"
	@echo "  run-debug     - Run the Flask application with DEBUG=1 for verbose logging"
	@echo "  initdb        - Initialize or reset the database"
	@echo "  migrate       - Run database migrations"
	@echo "  clean         - Remove database and cache files"
	@echo "  docker-build  - Build the Docker container"
	@echo "  docker-run    - Run the application in Docker"
	@echo "  docker-stop   - Stop the Docker container"
	@echo "  lint          - Run code linter"
	@echo "  format        - Format code using Black and isort"