.PHONY: up down logs

up:
	cd deploy && docker compose up -d --build

down:
	cd deploy && docker compose down

logs:
	cd deploy && docker compose logs -f --tail=200
