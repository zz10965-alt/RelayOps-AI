"""Dify contract tests with explicit HTTP substitutes, not real model tests."""
import asyncio
import json
import httpx
import pytest
from backend import app as module
from tests.test_api import analysis, client, photo


@pytest.fixture
def configured(client, monkeypatch):
    monkeypatch.setenv('DIFY_BASE_URL', 'https://dify.example/v1')
    monkeypatch.setenv('DIFY_API_KEY', 'app-test-only-secret')
    return client


def transport(monkeypatch, handler):
    real_client = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, 'AsyncClient', lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))


def submit(client):
    response = client.post('/api/cases', data={'order_id':'DEMO-1001', 'description':'白色陶瓷杯破损'}, files={'image':('evidence.png',photo(),'image/png')})
    assert response.status_code == 202
    return client.get('/api/cases/'+response.json()['id']).json()


def test_upload_workflow_callback_and_verified_result(configured, monkeypatch):
    seen=[]
    async def handler(request):
        seen.append(request.url.path)
        assert request.headers['authorization']=='Bearer app-test-only-secret'
        if request.url.path.endswith('files/upload'):
            assert b'image/png' in request.content
            return httpx.Response(201,json={'id':'uploaded-file-id'})
        payload=json.loads(request.content)
        inputs=payload['inputs']
        assert inputs['image']['upload_file_id']=='uploaded-file-id'
        result=module.resolve(module.Resolve(case_id=inputs['case_id'],execution_token=inputs['execution_token'],analysis=json.dumps(analysis())), authorization='Bearer test-tool-secret')
        assert result['status']=='application_created'
        return httpx.Response(200,json={'workflow_run_id':'contract-run-1','data':{'status':'succeeded','metadata':{'total_price':'0.001','currency':'USD'}}})
    transport(monkeypatch,handler)
    result=submit(configured)
    assert result['status']=='application_created' and result['run_id']=='contract-run-1'
    assert result['cost']==0.001 and seen==['/v1/files/upload','/v1/workflows/run']
    assert 'execution-secret' not in json.dumps(result)
    with module.db() as con:
        assert con.execute('SELECT execution_token FROM cases WHERE id=?',(result['id'],)).fetchone()[0] is None
    metrics=configured.get('/api/metrics').json()
    assert metrics['average_api_cost']==0.001 and metrics['currency']=='USD'


@pytest.mark.parametrize('mode',['timeout','http500','http401','malformed','no_callback','workflow_failed','upload_bad','data_list','metadata_list'])
def test_remote_failures_never_claim_creation(configured,monkeypatch,mode):
    calls=[]
    async def handler(request):
        calls.append(request.url.path)
        if mode=='timeout': raise httpx.ReadTimeout('test timeout',request=request)
        if mode.startswith('http'): return httpx.Response(int(mode[4:]),json={'error':'test'})
        if request.url.path.endswith('files/upload'): return httpx.Response(201,json=[] if mode=='upload_bad' else {'id':'file'})
        if mode=='data_list': return httpx.Response(200,json={'data':[]})
        if mode=='metadata_list': return httpx.Response(200,json={'data':{'status':'succeeded','metadata':['bad']}})
        if mode=='malformed': return httpx.Response(200,json={})
        return httpx.Response(200,json={'data':{'status':'failed' if mode=='workflow_failed' else 'succeeded'}})
    transport(monkeypatch,handler)
    result=submit(configured)
    assert result['status']=='handoff' and result['application'] is None
    assert len(calls)==(1 if mode in ('http401','upload_bad') else 2)
    assert any(not e['success'] for e in result['trace'])


def test_retry_recovers_and_side_effect_is_idempotent(configured,monkeypatch):
    runs=0
    async def handler(request):
        nonlocal runs
        if request.url.path.endswith('files/upload'): return httpx.Response(201,json={'id':'file'})
        runs+=1
        inputs=json.loads(request.content)['inputs']
        result=module.resolve(module.Resolve(case_id=inputs['case_id'],execution_token=inputs['execution_token'],analysis=json.dumps(analysis())), authorization='Bearer test-tool-secret')
        assert result['status']=='application_created'
        if runs==1: raise httpx.ReadTimeout('lost response after commit',request=request)
        return httpx.Response(200,json={'data':{'status':'succeeded'},'workflow_run_id':'retry-run'})
    transport(monkeypatch,handler)
    result=submit(configured)
    assert result['status']=='application_created' and runs==2
    metrics=configured.get('/api/metrics').json()
    assert metrics['retried_cases']==1 and metrics['recovered_cases']==1
    with module.db() as con: assert con.execute('SELECT count(*) FROM returns').fetchone()[0]==1
