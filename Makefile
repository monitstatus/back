run:
	TZ="Europe/Madrid" uvicorn app.main:app --reload

test:
	ENVIRONMENT="test" pytest -vv

up:
	docker compose up -d

rebuild-db:
	docker compose down && rm -rf postgres_data && docker compose run --rm web alembic upgrade head
