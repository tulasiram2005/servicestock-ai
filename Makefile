PYTHON ?= python3
.PHONY: up down test results benchmark export
up:
	$(PYTHON) scripts/local_env.py
	docker compose up --build -d --wait
down:
	docker compose down
test:
	cd api && $(PYTHON) -m pytest -q
	cd web && npm test && npm run build
benchmark:
	cd api && $(PYTHON) -m app.analytics.benchmark
results:
	$(PYTHON) scripts/results.py
export:
	cd api && $(PYTHON) -m app.export
