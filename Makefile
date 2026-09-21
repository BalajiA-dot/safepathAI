.PHONY: up down seed test
up:
	docker compose up --build
down:
	docker compose down
seed:
	docker compose exec backend python scripts/seed_demo.py
test:
	docker compose exec backend pytest
