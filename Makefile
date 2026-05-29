SHELL := /bin/bash

PROJECT_ROOT := $(CURDIR)
FRONTEND_DIR := $(PROJECT_ROOT)/agendamiento-saas-frontend
MOBILE_DIR   := $(PROJECT_ROOT)/agendamiento-saas-mobile
CONDA_ENV    := agendamiento-saas

# Activa el env de conda en cualquier shell no-interactiva
CONDA_RUN := source "$$(conda info --base)/etc/profile.d/conda.sh" && conda activate $(CONDA_ENV)

.PHONY: help dev backend celery beat marketing public admin platform mobile stop install

help:
	@echo "Targets:"
	@echo "  make dev         arranca backend + celery + beat + 4 frontends en paralelo (Ctrl+C detiene todo)"
	@echo "  make backend     Daphne ASGI en :8000"
	@echo "  make celery      Celery worker"
	@echo "  make beat        Celery beat"
	@echo "  make marketing   Nuxt :3000"
	@echo "  make public      Nuxt :3001"
	@echo "  make admin       Nuxt :3002"
	@echo "  make platform    Nuxt :3004"
	@echo "  make mobile      Expo iOS simulador (solo iOS)"
	@echo "  make install     pnpm install en el monorepo frontend"
	@echo "  make stop        mata procesos en los puertos 8000/3000/3001/3002/3004"

backend:
	$(CONDA_RUN) && daphne -b 0.0.0.0 -p 8000 core.asgi:application

celery:
	$(CONDA_RUN) && celery -A core worker -l info

beat:
	$(CONDA_RUN) && celery -A core beat -l info

marketing:
	cd $(FRONTEND_DIR) && pnpm dev:marketing

public:
	cd $(FRONTEND_DIR) && pnpm dev:public

admin:
	cd $(FRONTEND_DIR) && pnpm dev:admin

platform:
	cd $(FRONTEND_DIR) && pnpm dev:platform

mobile:
	cd $(MOBILE_DIR) && npm run ios

install:
	cd $(FRONTEND_DIR) && pnpm install

dev:
	@echo "Arrancando backend + celery + beat + 4 frontends. Ctrl+C para detener todo."
	@trap 'echo; echo "Deteniendo..."; kill 0' INT TERM EXIT; \
	( $(MAKE) --no-print-directory backend  2>&1 | sed -l -e 's/^/[backend]   /' ) & \
	( $(MAKE) --no-print-directory celery   2>&1 | sed -l -e 's/^/[celery]    /' ) & \
	( $(MAKE) --no-print-directory beat     2>&1 | sed -l -e 's/^/[beat]      /' ) & \
	( $(MAKE) --no-print-directory marketing 2>&1 | sed -l -e 's/^/[marketing] /' ) & \
	( $(MAKE) --no-print-directory public   2>&1 | sed -l -e 's/^/[public]    /' ) & \
	( $(MAKE) --no-print-directory admin    2>&1 | sed -l -e 's/^/[admin]     /' ) & \
	( $(MAKE) --no-print-directory platform 2>&1 | sed -l -e 's/^/[platform]  /' ) & \
	wait

stop:
	@for port in 8000 3000 3001 3002 3004; do \
		pid=$$(lsof -ti :$$port 2>/dev/null) ; \
		if [ -n "$$pid" ]; then \
			echo "Matando puerto $$port (pid $$pid)" ; \
			kill -9 $$pid 2>/dev/null || true ; \
		else \
			echo "Puerto $$port libre" ; \
		fi ; \
	done
