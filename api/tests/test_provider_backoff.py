from dataclasses import replace
from email.utils import formatdate
import json

import httpx
import pytest

from app.assistant import REGISTRY
from app.llm_router import LocalToolRouter
from app.provider_backoff import retry_delay


@pytest.mark.parametrize('header,failures,expected', [
    (None, 1, 60), (None, 2, 120), (None, 10000, 3600),
    ('600', 1, 600), ('999999999', 1, 3600), ('-1', 1, 60),
    ('nan', 1, 60), ('inf', 1, 60), ('bad', 1, 60),
    (formatdate(1300, usegmt=True), 1, 300),
    (formatdate(900, usegmt=True), 1, 60),
])
def test_bounded_retry_after(header, failures, expected):
    assert retry_delay(header, 1000, failures) == expected


def test_cooldown_does_not_spend_attempts_and_success_resets(settings):
    now = [1000]
    requests = []
    def transport(request):
        requests.append(request)
        if len(requests) in (1, 2, 4):
            return httpx.Response(429, headers={'retry-after': '90'})
        return httpx.Response(200, json={'message': {'content': json.dumps({
            'calls': [{'tool': 'get_kpis', 'arguments': {}}]})}})
    config = replace(settings, llm_provider_order='ollama,mock', ollama_model='test',
                     llm_global_daily_cap=10, llm_user_daily_cap=10)
    router = LocalToolRouter(config, httpx.MockTransport(transport), clock=lambda: now[0])
    router.route('demo', 'first', REGISTRY)
    assert router.usage()['provider_retry_after_seconds']['ollama'] == 90
    router.route('demo', 'blocked', REGISTRY)
    assert len(requests) == 1
    assert router.usage()['attempts'] == 1
    now[0] += 90
    router.route('demo', 'second', REGISTRY)
    assert router.usage()['provider_retry_after_seconds']['ollama'] == 120
    now[0] += 120
    assert router.route('demo', 'success', REGISTRY)[0] is not None
    router.route('demo', 'fourth', REGISTRY)
    assert router.usage()['provider_retry_after_seconds']['ollama'] == 90
    assert len(requests) == 4
