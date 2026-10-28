from dataclasses import replace
import pytest


def production(settings, query='sslmode=require', origins=('https://demo.example',)):
    return replace(settings,environment='production',
        database_url='postgresql+psycopg://user:private@demo-pooler.example/db?'+query,
        allowed_origins=origins)

@pytest.mark.parametrize('query',['sslmode=require','sslmode=verify-full','connect_timeout=5&sslmode=require'])
def test_explicit_tls_accepted(settings,query):
    assert production(settings,query).environment=='production'

@pytest.mark.parametrize('query',['','sslmode=require-fake','note=sslmode=require','sslmode=require&sslmode=disable','sslmode=','sslmode=disable'])
def test_misleading_tls_rejected(settings,query):
    with pytest.raises(ValueError,match='TLS'):
        production(settings,query)

@pytest.mark.parametrize('origins',[(),('https://',),('http://demo.example',),('https://user:pass@demo.example',),('https://demo.example/path',),('https://demo.example?foo=1',),('https://demo.example#fragment',)])
def test_invalid_production_origins_rejected(settings,origins):
    with pytest.raises(ValueError,match='origins'):
        production(settings,origins=origins)
