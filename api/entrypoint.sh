set -eu
if [ "${APP_ENV:-local}" = "local" ]; then
  alembic upgrade head
  python -m app.ingest.seed > /dev/null
fi
exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --no-access-log
