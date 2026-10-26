from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select, func
from app.db import schema as db
from app.db.store import Store
from app.llm_budget import DatabaseBudget
from app.llm_router import LocalToolRouter
from app.assistant import REGISTRY
from dataclasses import replace
import httpx


def test_persistent_caps_rollback_and_new_day(tmp_path):
    url = 'sqlite:///' + str(tmp_path/'quota.db')
    store = Store(url)
    db.metadata.create_all(store.engine)
    budget = DatabaseBudget(store)
    assert budget.reserve('a', 1, 3, 1)
    assert not budget.reserve('a', 1, 3, 1)
    assert budget.total(1) == 1  # denied user reservation rolled back global increment
    restarted = DatabaseBudget(Store(url))
    assert not restarted.reserve('a', 1, 3, 1)
    assert restarted.reserve('b', 1, 3, 1)
    assert restarted.reserve('c', 1, 3, 1)
    assert not restarted.reserve('d', 1, 3, 1)
    assert restarted.reserve('a', 2, 3, 1)
    with store.transaction() as connection:
        assert 'a' not in connection.scalars(select(db.llm_daily_usage.c.subject)).all()


def test_shared_cap_across_independent_connections(tmp_path):
    url = 'sqlite:///' + str(tmp_path/'shared.db')
    store = Store(url)
    db.metadata.create_all(store.engine)
    with store.transaction() as connection:
        connection.execute(db.llm_daily_usage.insert().values(day=1,subject='global',attempts=0))
    def reserve(index):
        instance = Store(url)
        try:
            return DatabaseBudget(instance).reserve(str(index),1,4,1)
        finally:
            instance.engine.dispose()
    with ThreadPoolExecutor(max_workers=4) as executor:
        allowed = list(executor.map(reserve,range(12)))
    assert sum(allowed) == 4
    assert DatabaseBudget(store).total(1) == 4


def test_missing_quota_storage_falls_back_without_model_call(settings):
    def forbidden(request):
        raise AssertionError('Model must not be called when quotas cannot be checked')
    settings = replace(settings,llm_provider_order='ollama,mock',ollama_model='test',
        llm_global_daily_cap=10,llm_user_daily_cap=2)
    router = LocalToolRouter(settings,httpx.MockTransport(forbidden),store=Store('sqlite://'))
    calls, notice = router.route('a','KPIs',REGISTRY)
    assert calls is None
    assert 'quota storage unavailable' in notice
