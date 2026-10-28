from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Event
import json
import httpx
import pytest
from app.assistant import REGISTRY
from app.llm_router import LocalToolRouter


def test_busy_chain_falls_back_without_spending_quota(settings):
    entered, release = Event(), Event()
    def respond(request):
        entered.set()
        assert release.wait(5)
        return httpx.Response(200, json={'message': {'content': json.dumps(
            {'calls': [{'tool': 'get_kpis', 'arguments': {}}]})}})
    router = LocalToolRouter(replace(settings, llm_provider_order='ollama,mock',
        ollama_model='test', llm_global_daily_cap=5, llm_user_daily_cap=5),
        httpx.MockTransport(respond))
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(router.route, 'a', 'one', REGISTRY)
        try:
            assert entered.wait(5)
            calls, reason = router.route('b', 'two', REGISTRY)
            assert calls is None and 'concurrency limit' in reason
            assert router.selected_provider() == 'mock'
            assert router.usage()['attempts'] == 1
            assert router.usage()['busy_fallbacks'] == 1
        finally:
            release.set()
        assert first.result()[0] == [('get_kpis', {'scope': 'all', 'period': None})]
    assert router.route('b', 'two', REGISTRY)[0] is not None
    assert router.usage()['attempts'] == 2


def test_slot_released_on_unexpected_exception(settings, monkeypatch):
    router = LocalToolRouter(settings)
    def fail(*args):
        raise RuntimeError('test failure')
    monkeypatch.setattr(router, '_route_chain', fail)
    with pytest.raises(RuntimeError):
        router.route('a', 'one', REGISTRY)
    monkeypatch.setattr(router, '_route_chain', lambda *args: (None, 'offline default'))
    assert router.route('a', 'two', REGISTRY) == (None, 'offline default')


@pytest.mark.parametrize('value', [0, -1, 5, True, 1.5])
def test_invalid_concurrency_rejected(settings, value):
    with pytest.raises(ValueError, match='LLM_MAX_CONCURRENT'):
        replace(settings, llm_max_concurrent=value)


def test_concurrency_environment_setting(settings, monkeypatch):
    monkeypatch.setenv('JWT_SECRET', settings.jwt_secret)
    monkeypatch.setenv('DEMO_PASSWORD', settings.demo_password)
    monkeypatch.setenv('ADMIN_PASSWORD', settings.admin_password)
    monkeypatch.setenv('LLM_MAX_CONCURRENT', '2')
    assert type(settings).from_env().llm_max_concurrent == 2
