# Atajos de desarrollo local. Las pruebas de integración requieren un proyecto Compose aislado.
COMPOSE ?= docker compose
MAILHOG_COMPOSE ?= $(COMPOSE) -f docker-compose.mailhog.yml
PYTHON ?= ../.venv/bin/python
NPM ?= npm

.PHONY: help up down stop restart ps logs migrate mailhog-up mailhog-down mailhog-restart mailhog-status mailhog-logs test test-backend test-frontend build-frontend

## Entorno
help: ## Muestra los comandos agrupados por propósito.
	@awk 'BEGIN {FS = ":.*## "} /^## / { section = substr($$0, 4); printf "\n%s\n", section; next } /^[a-zA-Z_-]+:.*## / { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

## Ciclo de vida de la aplicación
up: ## Construye e inicia la aplicación y la base de datos, esperando el estado saludable.
	$(COMPOSE) up -d --build --wait

down: ## Elimina los contenedores y la red de la aplicación; conserva los volúmenes con nombre.
	$(COMPOSE) down

stop: ## Detiene los contenedores de la aplicación sin eliminarlos.
	$(COMPOSE) stop

restart: ## Reinicia los contenedores de la aplicación.
	$(COMPOSE) restart

ps: ## Muestra el estado de los servicios de la aplicación.
	$(COMPOSE) ps

logs: ## Muestra los registros de los servicios de la aplicación en tiempo real.
	$(COMPOSE) logs -f

## Captura de correo (solo desarrollo)

mailhog-up: ## Inicia primero la aplicación y la red; después, MailHog en la red compartida.
	$(COMPOSE) up -d --build --wait
	$(MAILHOG_COMPOSE) up -d

mailhog-down: ## Detiene y elimina MailHog; los mensajes en memoria se descartan.
	$(MAILHOG_COMPOSE) down

mailhog-restart: ## Reinicia MailHog sin modificar los volúmenes de la aplicación o la base de datos.
	$(MAILHOG_COMPOSE) restart

mailhog-status: ## Muestra el estado de MailHog.
	$(MAILHOG_COMPOSE) ps

mailhog-logs: ## Muestra los registros de MailHog en tiempo real.
	$(MAILHOG_COMPOSE) logs -f

## Tareas de base de datos y aplicación
migrate: ## Aplica las migraciones pendientes en el contenedor activo del backend.
	$(COMPOSE) exec -T backend python -m alembic upgrade head

## Validación
test: test-backend test-frontend ## Ejecuta las pruebas unitarias locales del backend y frontend.

test-backend: ## Ejecuta pytest desde backend/.
	cd backend && $(PYTHON) -m pytest -q --ignore=tests/test_database_integration.py

test-frontend: ## Ejecuta Vitest desde frontend/.
	cd frontend && $(NPM) test

build-frontend: ## Comprueba los tipos y genera el paquete de producción del frontend.
	cd frontend && $(NPM) run build

## Proxy público y certificados
proxy-up: ## Inicia el proxy HTTP bootstrap; backend y PostgreSQL permanecen internos.
	$(COMPOSE) up -d --build --force-recreate proxy

proxy-status: ## Muestra el estado del proxy y servicios Compose.
	$(COMPOSE) ps

cert-status: ## Muestra los certificados conocidos por Certbot.
	$(COMPOSE) --profile certbot run --rm certbot certificates

cert-issue: ## Solicita certificado HTTP-01 para gonzalodeniz.com (DNS y puerto 80 deben llegar a este host).
	$(COMPOSE) --profile certbot run --rm certbot certonly --webroot -w /var/www/certbot -d gonzalodeniz.com --agree-tos --register-unsafely-without-email --non-interactive

cert-enable-tls: ## Activa TLS tras confirmar que cert-issue obtuvo el certificado.
	$(COMPOSE) restart proxy
	$(COMPOSE) exec -T proxy sh -c "grep -q 'listen 443 ssl' /etc/nginx/conf.d/default.conf && nginx -t && nginx -s reload"

cert-renew: ## Renueva certificados por HTTP-01; después recarga el proxy.
	$(COMPOSE) --profile certbot run --rm certbot renew --webroot -w /var/www/certbot
	$(COMPOSE) exec -T proxy nginx -t
	$(COMPOSE) exec -T proxy nginx -s reload
