import json
import httpx
import pytest
from dataclasses import replace
from app.token_usage import reported_tokens
from app.llm_router import LocalToolRouter
from app.assistant import REGISTRY

@pytest.mark.parametrize('provider,envelope,expected',[
 ('gemini',{'usageMetadata':{'promptTokenCount':10,'candidatesTokenCount':2,'thoughtsTokenCount':3,'totalTokenCount':15}}, {'input_tokens':10,'output_tokens':2,'thinking_tokens':3,'total_tokens':15}),
 ('openai-local',{'usage':{'prompt_tokens':4,'completion_tokens':0,'total_tokens':4}},{'input_tokens':4,'output_tokens':0,'total_tokens':4}),
 ('ollama',{'prompt_eval_count':4,'eval_count':2},{'input_tokens':4,'output_tokens':2}),
 ('gemini',{'usageMetadata':None},{}),
])
def test_provider_metadata(provider,envelope,expected):
    assert reported_tokens(provider,envelope)==expected

@pytest.mark.parametrize('value',[None,True,-1,1.5,'4',10**20])
def test_unusable_counts_are_not_zero(value):
    assert reported_tokens('ollama',{'eval_count':value})=={}


def test_cache_does_not_double_count_and_invalid_plan_still_records_usage(settings):
    enabled=replace(settings,llm_provider_order='ollama,mock',ollama_model='local-test',llm_global_daily_cap=4,llm_user_daily_cap=4)
    responses=iter([
        {'message':{'content':json.dumps({'calls':[{'tool':'get_kpis','arguments':{}}]})},'eval_count':5},
        {'message':{'content':'invalid'},'eval_count':7},
    ])
    router=LocalToolRouter(enabled,httpx.MockTransport(lambda _:httpx.Response(200,json=next(responses))))
    assert router.route('a','one',REGISTRY)[0]
    assert router.route('a','one',REGISTRY)[0]
    assert router.route('a','two',REGISTRY)[0] is None
    usage=router.usage()
    assert usage['token_usage']['ollama']=={'responses':2,'fields':{'output_tokens':{'reported_sum':12,'responses_with_value':2}}}
    assert usage['cost_usd'] is None
    usage['token_usage']['ollama']['responses']=999
    assert router.usage()['token_usage']['ollama']['responses']==2
