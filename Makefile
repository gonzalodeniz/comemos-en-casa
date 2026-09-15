.DEFAULT_GOAL := help

COMPOSE := docker compose
PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
NPM := npm --prefix frontend

.PHONY: help deploy up down restart build logs ps backend frontend test test-backend test-frontend install frontend-install db-shell

help: ## Mostrar esta ayuda
	@printf 'Comandos disponibles:\n\n'
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Levantar PostgreSQL, backend y frontend en segundo plano
	$(COMPOSE) up -d --build

deploy: up ## Alias de up para desplegar la aplicación

down: ## Parar y eliminar los contenedores, conservando los volúmenes
	$(COMPOSE) down

restart: ## Reiniciar todos los servicios
	$(COMPOSE) restart

build: ## Construir las imágenes sin iniciar los servicios
	$(COMPOSE) build

logs: ## Seguir los logs de todos los servicios
	$(COMPOSE) logs -f

ps: ## Mostrar el estado de los servicios
	$(COMPOSE) ps

backend: ## Mostrar los logs del backend
	$(COMPOSE) logs -f backend

frontend: ## Mostrar los logs del frontend
	$(COMPOSE) logs -f frontend

install: ## Instalar dependencias Python y frontend
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(NPM) install

frontend-install: ## Instalar dependencias del frontend
	$(NPM) install

test: test-backend test-frontend ## Ejecutar todas las comprobaciones del proyecto

test-backend: ## Ejecutar la suite Python
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src $(PYTEST) -q

test-frontend: ## Ejecutar typecheck y build del frontend
	$(NPM) run typecheck
	$(NPM) run build

db-shell: ## Abrir una consola PostgreSQL dentro del contenedor
	$(COMPOSE) exec postgres psql -U comemos -d comemos_en_casa
