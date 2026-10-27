import importlib.util
import json
from pathlib import Path
import sys
import httpx
import pytest

SCRIPTS=Path(__file__).resolve().parents[2]/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('nlp_comparison',SCRIPTS/'compare_nlp.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
VALUES={'GEMINI_API_KEY':'test-secret','GEMINI_MODEL':'gemini-test-flash'}


def response(rows):
    return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps({'predictions':rows})}]}}]})


def test_synthetic_only_payload_and_measured_scores():
    _,_,texts,expected=module.synthetic_comments()
    requests=[]
    def handler(request):
        requests.append(request)
        prompt=json.loads(json.loads(request.content)['contents'][0]['parts'][0]['text'])
        assert [row['text'] for row in prompt['comments']]==texts
        assert 'expected' not in json.dumps(prompt)
        assert 'test-secret' not in request.content.decode()
        return response([{'id':i,'category':label} for i,label in enumerate(expected)])
    result=module.evaluate(VALUES,httpx.MockTransport(handler))
    assert len(requests)==1
    assert result['zero_shot_macro_f1']==1
    assert result['unique_heldout_templates']==4
    assert 'test-secret' not in json.dumps(result)


@pytest.mark.parametrize('rows', [[],[{'id':0,'category':'late_delivery'}]*48,[{'id':0,'category':'invalid'}]])
def test_missing_duplicate_or_invalid_labels_fail(rows):
    with pytest.raises(ValueError):
        module.evaluate(VALUES,httpx.MockTransport(lambda _:response(rows)))
