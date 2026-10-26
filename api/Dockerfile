FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY data ./data
COPY entrypoint.sh .
USER appuser
CMD ["sh", "entrypoint.sh"]
