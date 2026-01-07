.PHONY: help install dev test lint format clean docker-build docker-up docker-down docker-logs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server with hot reload
	uvicorn src.main:app --reload --port 8000

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term tests/

lint: ## Run linting checks
	mypy src/
	# flake8 src/ tests/

format: ## Format code with black
	# black src/ tests/

clean: ## Clean up cache and build files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start all services with Docker Compose
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-down-v: ## Stop all services and remove volumes
	docker-compose down -v

docker-logs: ## Follow logs for all services
	docker-compose logs -f

docker-logs-app: ## Follow logs for slack-citizen only
	docker-compose logs -f slack-citizen

docker-restart: ## Restart slack-citizen service
	docker-compose restart slack-citizen

docker-shell: ## Open shell in slack-citizen container
	docker-compose exec slack-citizen /bin/bash

kafka-topics: ## List Kafka topics
	docker-compose exec kafka kafka-topics --bootstrap-server localhost:9093 --list

kafka-consume: ## Consume messages from Slack message topic
	docker-compose exec kafka kafka-console-consumer \
		--bootstrap-server localhost:9093 \
		--topic project-manager.slack.message.received \
		--from-beginning

health: ## Check service health
	curl http://localhost:8000/health

ready: ## Check service readiness
	curl http://localhost:8000/ready

metrics: ## View Prometheus metrics
	curl http://localhost:9090/metrics
