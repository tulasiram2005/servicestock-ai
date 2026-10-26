"""Run via: docker compose exec -T api python < scripts/check_llm_budget_postgres.py"""
import json
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from sqlalchemy import delete
from app.db.store import Store
from app.db.schema import llm_daily_usage
from app.llm_budget import DatabaseBudget

store = Store(os.environ['DATABASE_URL'])
assert store.engine.dialect.name == 'postgresql'
day = -1000000000 - secrets.randbelow(100000000)
try:
    def reserve(index):
        return DatabaseBudget(store).reserve('probe-'+str(index),day,5,1)
    with ThreadPoolExecutor(max_workers=8) as executor:
        accepted = sum(executor.map(reserve, range(24)))
    assert accepted == 5
    assert DatabaseBudget(store).total(day) == 5
    assert not DatabaseBudget(store).reserve('extra',day,5,1)
    print(json.dumps({'measured_at':datetime.now(timezone.utc).isoformat(),
        'environment':'local Docker PostgreSQL', 'concurrent_workers':8,
        'reservation_attempts':24,'configured_global_cap':5,'accepted':accepted,
        'new_budget_instance_reads_persisted_total':True,'status':'passed'}))
finally:
    with store.transaction() as connection:
        connection.execute(delete(llm_daily_usage).where(llm_daily_usage.c.day == day))
    store.engine.dispose()
