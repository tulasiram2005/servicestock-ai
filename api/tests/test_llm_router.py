from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import json
import httpx
import pytest

from app.assistant import REGISTRY
from app.llm_router import LocalToolRouter


def configured(settings, **changes):
    return replace(settings, llm_provider_order='ollama,mock', ollama_model='local-test',
                   llm_global_daily_cap=4, llm_user_daily_cap=2, **changes)


def response(request):
    assert request.url.host == '127.0.0.1'
    return httpx.Response(200, json={'message': {'content': json.dumps({'calls': [
        {'tool': 'get_kpis', 'arguments': {}}]})}})


def test_default_and_zero_caps_make_no_requests(settings):
    def forbidden(request):
        raise AssertionError('Network must be disabled')
    transport = httpx.MockTransport(forbidden)
    assert LocalToolRouter(settings, transport).route('a', 'KPIs', REGISTRY)[0] is None
    enabled = replace(configured(settings), llm_global_daily_cap=0)
    assert LocalToolRouter(enabled, transport).route('a', 'KPIs', REGISTRY)[0] is None


def test_cache_user_isolation_and_daily_reset(settings):
    clock = [0]
    router = LocalToolRouter(configured(settings), httpx.MockTransport(response), clock=lambda:clock[0])
    assert router.route('a','one',REGISTRY)[0][0][0] == 'get_kpis'
    assert 'cached' in router.route('a','one',REGISTRY)[1]
    router.route('a','two',REGISTRY)
    assert router.route('a','three',REGISTRY)[0] is None
    assert router.route('b','one',REGISTRY)[0] is not None
    assert router.usage()['attempts'] == 3
    clock[0] = 86400
    assert router.route('a','three',REGISTRY)[0] is not None
    assert router.usage()['attempts'] == 1


@pytest.mark.parametrize('content', ['not json', '{"calls":[]}',
    '{"calls":[{"tool":"generate_review_pack","arguments":{}}]}',
    '{"calls":[{"tool":"get_kpis","arguments":{"sql":"secret"}}]}'])
def test_invalid_output_falls_back_and_cools_down(settings, content):
    router = LocalToolRouter(configured(settings), httpx.MockTransport(lambda request:
        httpx.Response(200,json={'message':{'content':content}})))
    assert router.route('a','one',REGISTRY)[0] is None
    assert 'cooling' in router.route('a','two',REGISTRY)[1]
    assert router.usage()['attempts'] == 1


@pytest.mark.parametrize('status', [429, 500, 302])
def test_provider_failure_uses_deterministic_fallback(settings, status):
    router = LocalToolRouter(configured(settings), httpx.MockTransport(lambda request:httpx.Response(status)))
    assert router.route('a','one',REGISTRY)[0] is None


def test_parallel_requests_cannot_exceed_global_cap(settings):
    router = LocalToolRouter(configured(settings), httpx.MockTransport(response))
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda i:router.route(str(i),str(i),REGISTRY),range(20)))
    assert router.usage()['attempts'] == 4


def test_cloud_models_rejected(settings):
    with pytest.raises(ValueError, match='local model'):
        replace(configured(settings),ollama_model='example-cloud')
