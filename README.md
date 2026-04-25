# Personal-shopping-assistant-agent

Database schema notes live in [docs/db-schema.md](/d:/Mohamed/Projects/shopify-shopping-assistant-agent/docs/db-schema.md).

## Run Migrations

1. Install dependencies:
	- `./.venv/Scripts/python.exe -m pip install -r requirements.txt`
2. Start PostgreSQL:
	- `docker compose -f docker/docker-compose.yml up -d pgvector`
3. Run migration:
	- `./.venv/Scripts/python.exe -m alembic -c src/db/migration/alembic.ini upgrade head`
4. Check current revision:
	- `./.venv/Scripts/python.exe -m alembic -c src/db/migration/alembic.ini current`

## Test API Endpoints

1. Start API:
	- `./.venv/Scripts/python.exe -m uvicorn src.api.main:app --reload`
2. Health check:
	- `curl http://127.0.0.1:8000/health`
3. Ingest products from store:
	- `curl -X POST http://127.0.0.1:8000/index -H "Content-Type: application/json" -d '{"store":"ystudios.net"}'`
