import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('gemini_check',Path(__file__).resolve().parents[2]/'scripts/check_gemini.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CONFIG={'GEMINI_API_KEY':'private-test-value','GEMINI_MODEL':'gemini-test-flash','GEMINI_FREE_TIER_CONFIRMED':'true'}


def test_preflight_never_constructs_network_router():
    def forbidden(settings):
        raise AssertionError('Preflight must not make a network request')
    result,code=module.check(CONFIG,router_factory=forbidden)
    assert code==0
    assert result['requests_attempted']==0
    assert CONFIG['GEMINI_API_KEY'] not in json.dumps(result)
    result,code=module.check({},live=True,router_factory=forbidden)
    assert code==2
    assert result['requests_attempted']==0


def test_config_file_is_data_not_shell(tmp_path):
    path=tmp_path/'private.env'
    path.write_text('GEMINI_API_KEY="$(do-not-execute)"\nIGNORED=secret\nGEMINI_MODEL=gemini-test-flash\n')
    assert module.read_config(path)=={'GEMINI_API_KEY':'$(do-not-execute)','GEMINI_MODEL':'gemini-test-flash'}


def test_live_failure_never_prints_exception_secrets():
    class Router:
        def __init__(self,settings): pass
        def route(self,*args): raise RuntimeError('private-test-value')
    result,code=module.check(CONFIG,live=True,router_factory=Router)
    assert code==1
    assert 'private-test-value' not in json.dumps(result)


def test_live_success_is_bounded_public_prompt():
    class Router:
        def __init__(self,settings):
            assert settings.llm_global_daily_cap==settings.llm_user_daily_cap==1
            assert not settings.uploads_enabled
        def route(self,user,question,registry):
            assert question=='Show inventory KPIs'
            return [('get_kpis',{})], 'model route'
        def usage(self): return {'external_calls':1}
    result,code=module.check(CONFIG,live=True,router_factory=Router)
    assert code==0
    assert result['requests_attempted']==1
