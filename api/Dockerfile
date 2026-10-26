FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY api/app ./app
COPY api/migrations ./migrations
COPY api/alembic.ini .
COPY api/data ./data
COPY api/entrypoint.sh .
COPY results ./results
USER appuser
CMD ["sh", "entrypoint.sh"]
