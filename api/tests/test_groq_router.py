from dataclasses import replace
import json
import httpx
import pytest
from app.assistant import REGISTRY
from app.llm_router import LocalToolRouter


def enabled(settings, **kwargs):
    return replace(settings, llm_provider_order='groq,mock', groq_api_key='test-private-key',
                   groq_model='test-model', groq_free_tier_confirmed=True,
                   llm_global_daily_cap=3, llm_user_daily_cap=3, **kwargs)


def test_groq_requires_explicit_free_confirmation(settings):
    with pytest.raises(ValueError, match='verified free-tier'):
        replace(settings, llm_provider_order='groq,mock', groq_api_key='test', groq_model='model')
    assert 'test-private-key' not in repr(enabled(settings))


@pytest.mark.parametrize('native', [False, True])
def test_groq_validated_route_and_usage(settings, native):
    def respond(request):
        assert str(request.url) == 'https://api.groq.com/openai/v1/chat/completions'
        assert request.headers['authorization'] == 'Bearer test-private-key'
        body = json.loads(request.content)
        assert body['model'] == 'test-model'
        assert ('tools' in body) == native
        message = ({'tool_calls': [{'function': {'name': 'get_kpis', 'arguments': '{}'}}]}
                   if native else {'content': json.dumps({'calls':[{'tool':'get_kpis','arguments':{}}]})})
        return httpx.Response(200, json={'choices':[{'message':message}], 'usage':{'completion_tokens':12}})
    router = LocalToolRouter(enabled(settings, llm_native_tools=native), httpx.MockTransport(respond))
    assert router.route('a', 'show kpis', REGISTRY)[0][0][0] == 'get_kpis'
    assert router.usage()['external_calls'] == 1
    assert router.usage()['native_tool_calling'] == native
    assert router.usage()['token_usage']['groq']['fields']['output_tokens']['reported_sum'] == 12


def test_groq_private_prompt_never_leaves_process(settings):
    def forbidden(request):
        raise AssertionError('Private data must not leave process')
    router = LocalToolRouter(enabled(settings), httpx.MockTransport(forbidden))
    assert router.route('a', 'customer private order 123', REGISTRY)[0] is None
    assert router.usage()['external_calls'] == 0
    assert router.usage()['attempts'] == 0


@pytest.mark.parametrize('status', [302, 429, 503])
def test_groq_errors_fall_back_without_retry(settings, status):
    router = LocalToolRouter(enabled(settings), httpx.MockTransport(lambda r:httpx.Response(status)))
    assert router.route('a', 'show kpis', REGISTRY)[0] is None
    assert router.route('a', 'show data quality', REGISTRY)[0] is None
    assert router.usage()['external_calls'] == 1
