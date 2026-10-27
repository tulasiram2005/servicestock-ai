"""Explicit one-request Gemini comparison on built-in synthetic comments only.
No file uploads, user text, training examples or expected answers are transmitted.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import httpx
from sklearn.metrics import f1_score, classification_report
from app.analytics.extensions import synthetic_comments, nlp
from check_gemini import read_config, check

LABELS = ['late_delivery', 'wrong_part', 'quality_defect', 'damaged_in_transit']
ROOT = Path(__file__).resolve().parents[1]


def evaluate(values, transport=None):
    _, _, testing, expected = synthetic_comments()
    baseline = nlp()
    prompt = {'task': 'Classify each synthetic comment into exactly one category. Return JSON with a predictions array of {id, category}, one per input. No explanation.',
              'categories': LABELS, 'comments': [{'id': i, 'text': text} for i, text in enumerate(testing)]}
    started = time.monotonic()
    with httpx.Client(timeout=45, trust_env=False, follow_redirects=False, transport=transport) as client:
        with client.stream('POST', 'https://generativelanguage.googleapis.com/v1beta/models/'+values['GEMINI_MODEL']+':generateContent',
            headers={'x-goog-api-key': values['GEMINI_API_KEY']},
            json={'contents':[{'role':'user','parts':[{'text':json.dumps(prompt)}]}],
                  'generationConfig':{'responseMimeType':'application/json','temperature':0,'maxOutputTokens':8192}}) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content)>131072 or time.monotonic()-started>60:
                    raise ValueError('Response limit')
    candidate = json.loads(content)['candidates'][0]
    if candidate.get('finishReason') != 'STOP':
        raise ValueError('Incomplete response')
    answer = json.loads(''.join(part['text'] for part in candidate['content']['parts'] if not part.get('thought',False)))
    rows = answer['predictions']
    predictions = {}
    for row in rows:
        index = row['id']
        if type(index) is not int or index in predictions or index not in range(len(testing)) or row['category'] not in LABELS:
            raise ValueError('Invalid classification')
        predictions[index] = row['category']
    if len(predictions) != len(testing):
        raise ValueError('Missing classification')
    predicted = [predictions[i] for i in range(len(testing))]
    return {'status':'measured','measured_at':datetime.now(timezone.utc).isoformat(),
        'model':values['GEMINI_MODEL'],'provider':'gemini','requests_attempted':1,
        'synthetic_comments_and_labels':True,'test_rows':len(testing),'unique_heldout_templates':4,
        'dataset_sha256':hashlib.sha256(json.dumps(testing).encode()).hexdigest(),
        'baseline_macro_f1':baseline['macro_f1'],
        'zero_shot_macro_f1':float(f1_score(expected,predicted,labels=LABELS,average='macro',zero_division=0)),
        'classification_report':classification_report(expected,predicted,labels=LABELS,output_dict=True,zero_division=0),
        'predictions':[{'id':i,'expected':expected[i],'predicted':predicted[i]} for i in range(len(testing))],
        'elapsed_seconds':round(time.monotonic()-started,3),
        'limitations':['Four held-out phrase templates repeated with synthetic order/depot suffixes; 48 rows are not 48 independent language examples.',
            'Zero-shot prompt includes categories but no labeled examples. One batch, one model, no tuning; not production accuracy.',
            'Risk flags continue to use the offline TF-IDF baseline. HTTP phase timeouts are not a hard process deadline.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',default='.env.gemini')
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    try:
        values=read_config(args.env_file)
        result, code=check(values)
        if code or not args.live:
            print(json.dumps(result));return code
        result=evaluate(values)
        (ROOT/'results/nlp_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({key:result[key] for key in ('status','test_rows','baseline_macro_f1','zero_shot_macro_f1','requests_attempted')}))
        return 0
    except Exception:
        print(json.dumps({'status':'comparison_failed','detail':'No provider error text or credentials logged; prior artifacts unchanged.'}))
        return 1

if __name__=='__main__':
    raise SystemExit(main())
