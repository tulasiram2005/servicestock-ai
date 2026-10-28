"""Full seeded application smoke; configured target MUST be a disposable empty database."""
import os
from pathlib import Path
import pytest
from sqlalchemy import select, func, inspect
from fastapi.testclient import TestClient
from app.db.store import Store
from app.db import schema as db
from app.ingest.seed import seed
from app.ingest.staging import generate_and_transform
from app.services import publish
from app.main import create_app


@pytest.mark.parametrize('backend',['sqlite','configured'])
def test_seeded_application_and_staging(settings,backend):
    url=os.getenv('TEST_APP_DATABASE_URL') if backend=='configured' else 'sqlite://'
    if not url:
        pytest.skip('Disposable application database not configured')
    store=Store(url)
    try:
        db.metadata.create_all(store.engine)
        # Never overwrite an existing app dataset, even if an operator passes its URL.
        with store.transaction() as connection:
            assert connection.scalar(select(func.count()).select_from(db.parts))==0, 'Use an empty disposable database'
            assert connection.scalar(select(func.count()).select_from(db.roles))==0, 'Use an empty disposable database'
        seed(store)
        first=generate_and_transform(store)
        assert generate_and_transform(store)==first
        assert first['extract_rows']==1258
        with store.transaction() as connection:
            assert all(connection.scalar(select(func.count()).select_from(table))>0 for table in db.sap_staging.values())
            if store.engine.dialect.name!='sqlite':
                assert len(inspect(connection).get_table_names(schema='staging'))==10
        publish(store,Path(__file__).resolve().parents[2]/'results')
        with TestClient(create_app(settings,store_override=store)) as client:
            tokens={}
            for user,password in [('demo',settings.demo_password),('admin',settings.admin_password)]:
                result=client.post('/api/auth/login',json={'username':user,'password':password})
                assert result.status_code==200
                tokens[user]={'Authorization':'Bearer '+result.json()['access_token']}
            for endpoint in ['/api/kpis','/api/parts?limit=2','/api/dq','/api/configurations','/api/results']:
                assert client.get(endpoint).status_code==401
                assert client.get(endpoint,headers=tokens['demo']).status_code==200,endpoint
            assert client.get('/api/admin/usage',headers=tokens['demo']).status_code==403
            assert client.get('/api/admin/usage',headers=tokens['admin']).status_code==200
            impact=client.post('/api/configurations/impact',headers=tokens['demo'],json={'model_id':'MODEL-1','before_options':['AC'],'options':['AC','SENSOR']})
            assert impact.status_code==200 and impact.json()['cost_change_usd']==59
            body={'idempotency_key':'application-database-probe','service_level':0.95}
            assert client.post('/api/whatif',headers=tokens['demo'],json=body).status_code==403
            job=client.post('/api/whatif',headers=tokens['admin'],json=body)
            assert job.status_code==200
            identifier=job.json()['job_id']
            assert client.get('/api/jobs/'+identifier,headers=tokens['demo']).status_code==404
            assert client.get('/api/jobs/'+identifier,headers=tokens['admin']).status_code==200
            # Leave no pending job for subsequent exclusivity tests.
            from app.jobs import JobQueue
            queue=JobQueue(store,settings)
            claimed=queue.claim()
            assert claimed['id']==identifier
            assert queue.finish(claimed,{'status':'application probe'})
    finally:
        store.engine.dispose()
