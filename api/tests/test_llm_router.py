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


def test_openai_compatible_local_protocol_and_limits(settings):
    enabled = replace(configured(settings), llm_provider_order='openai-local,mock')
    def compatible(request):
        assert str(request.url) == 'http://127.0.0.1:11434/v1/chat/completions'
        body = json.loads(request.content)
        assert body['response_format'] == {'type': 'json_object'}
        assert body['max_tokens'] == 1024
        assert body['stream'] is False
        assert 'authorization' not in request.headers
        return httpx.Response(200, json={'choices':[{'message':{'content':json.dumps({'calls':[{'tool':'get_kpis','arguments':{}}]})}}]})
    router = LocalToolRouter(enabled,httpx.MockTransport(compatible))
    assert router.route('a','KPIs',REGISTRY)[0] == [('get_kpis',{'scope':'all','period':None})]
    assert router.usage()['provider'] == 'openai-local'
    assert router.usage()['external_calls'] == 0
    assert router.usage()['native_tool_calling'] is False


@pytest.mark.parametrize('envelope', [{'choices':[]},{'choices':[{'message':{'content':None}}]},
    {'choices':[{'message':{'content':'{"calls":[{"tool":"generate_review_pack","arguments":{}}]}'}}]}])
def test_openai_compatible_unusable_capability_falls_back(settings,envelope):
    enabled = replace(configured(settings), llm_provider_order='openai-local,mock')
    router = LocalToolRouter(enabled,httpx.MockTransport(lambda request:httpx.Response(200,json=envelope)))
    assert router.route('a','KPIs',REGISTRY)[0] is None
    assert 'cooling' in router.route('a','other',REGISTRY)[1]


def gemini_settings(settings):
    return replace(settings,llm_provider_order='gemini,mock',gemini_model='gemini-test-flash',
        gemini_api_key='test-key-not-real',gemini_free_tier_confirmed=True,
        llm_global_daily_cap=3,llm_user_daily_cap=2)


def test_gemini_sends_only_public_prompt_and_key_in_header(settings):
    enabled=gemini_settings(settings)
    assert enabled.gemini_api_key not in repr(enabled)
    def reply(request):
        assert request.url.host == 'generativelanguage.googleapis.com'
        assert not request.url.query
        assert request.headers['x-goog-api-key'] == enabled.gemini_api_key
        body=json.loads(request.content)
        assert body['generationConfig']['maxOutputTokens'] == 1024
        text=json.loads(body['contents'][0]['parts'][0]['text'])
        assert text['question_data'] == 'Show inventory KPIs'
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"calls":[{"tool":"get_kpis","arguments":{}}]}'}]}}]})
    router=LocalToolRouter(enabled,httpx.MockTransport(reply))
    assert router.route('private-username',' SHOW KPIS ',REGISTRY)[0][0][0] == 'get_kpis'
    assert router.usage()['external_calls'] == 1
    assert router.usage()['provider'] == 'gemini'


def test_gemini_private_inputs_do_not_leave_machine(settings):
    def forbidden(request):
        raise AssertionError('Private input sent externally')
    router=LocalToolRouter(gemini_settings(settings),httpx.MockTransport(forbidden))
    assert router.route('a','show kpis secret customer document',REGISTRY)[0] is None
    assert router.usage()['attempts'] == 0
    assert router.usage()['external_calls'] == 0


@pytest.mark.parametrize('change',[{'gemini_api_key':''},{'gemini_free_tier_confirmed':False},{'uploads_enabled':True},{'gemini_model':'../other'}])
def test_gemini_requires_explicit_safe_configuration(settings,change):
    with pytest.raises(ValueError):
        replace(gemini_settings(settings),**change)


@pytest.mark.parametrize('payload',[{}, {'candidates':[]}, {'candidates':[{'finishReason':'SAFETY'}]},
    {'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'{}'}]}}]}])
def test_gemini_blocked_or_incomplete_responses_fall_back(settings,payload):
    router=LocalToolRouter(gemini_settings(settings),httpx.MockTransport(lambda request:httpx.Response(200,json=payload)))
    assert router.route('a','show kpis',REGISTRY)[0] is None


def chained(settings, **changes):
    return replace(gemini_settings(settings), llm_provider_order='gemini,openai-local,ollama,mock',
                   ollama_model='local-test', **changes)


def test_chain_cooldowns_capability_and_successful_provider(settings):
    requests=[]
    def reply(request):
        requests.append(str(request.url))
        if request.url.host != '127.0.0.1':
            return httpx.Response(429)
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"calls":[{"tool":"get_kpis","arguments":{}}]}'}}]})
    router=LocalToolRouter(chained(settings),httpx.MockTransport(reply))
    assert set(router.usage()['provider_capabilities'].values()) == {'unprobed'}
    calls,notice=router.route('a','show kpis',REGISTRY)
    assert calls is not None and router.selected_provider() == 'openai-local'
    assert 'gemini:' in notice and 'openai-local:' in notice
    assert len(requests)==2 and router.usage()['attempts']==2
    assert router.usage()['provider_capabilities']['gemini']=='unavailable_or_invalid_output'
    assert router.usage()['provider_capabilities']['openai-local']=='validated_json_plan'
    assert router.route('a','show kpis',REGISTRY)[0] == calls
    assert len(requests)==2  # First provider cools down; successful provider cache survives.


def test_chain_preserves_private_input_guard_and_combined_budget(settings):
    requests=[]
    def fail(request):
        assert request.url.host=='127.0.0.1'
        requests.append(request)
        return httpx.Response(500)
    router=LocalToolRouter(chained(settings,llm_global_daily_cap=1),httpx.MockTransport(fail))
    assert router.route('a','private customer question',REGISTRY)[0] is None
    assert len(requests)==1
    assert router.selected_provider()=='mock'
    assert router.usage()['attempts']==1 and router.usage()['external_calls']==0


def test_chain_reaches_last_local_provider(settings):
    def reply(request):
        if request.url.path == '/api/chat':
            return response(request)
        return httpx.Response(503)
    router=LocalToolRouter(chained(settings,llm_user_daily_cap=3),httpx.MockTransport(reply))
    assert router.route('a','show kpis',REGISTRY)[0] is not None
    assert router.selected_provider()=='ollama-local'
    assert router.usage()['attempts']==3


@pytest.mark.parametrize('order',['mock,ollama','ollama,ollama,mock','gemini,unknown,mock','gemini',''])
def test_invalid_chains_rejected(settings,order):
    with pytest.raises(ValueError):
        replace(gemini_settings(settings),llm_provider_order=order,ollama_model='local-test')
