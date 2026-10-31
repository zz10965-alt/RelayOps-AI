import io
import json
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend import app as module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'DB', str(tmp_path/'test.sqlite3'))
    monkeypatch.delenv('DIFY_BASE_URL', raising=False)
    monkeypatch.delenv('DIFY_API_KEY', raising=False)
    monkeypatch.setenv('DIFY_TOOL_TOKEN', 'test-tool-secret')
    with TestClient(module.app) as client:
        yield client


def photo():
    buffer = io.BytesIO()
    Image.new('RGB', (20,20), 'white').save(buffer, format='PNG')
    return buffer.getvalue()


def pending(client, order='DEMO-1001'):
    ident = client.post('/api/cases', data={'order_id': order, 'description': '杯子破损'}, files={'image': ('test.png', photo(), 'image/png')}).json()['id']
    # Test-only fixture emulates a running Dify invocation, never enabled in app.
    with module.db() as con:
        con.execute("UPDATE cases SET status='running',finished=NULL,execution_token='execution-secret' WHERE id=?", (ident,))
    return ident


def analysis(**changes):
    return {'order_id':'DEMO-1001', 'damaged':True, 'product_match':True,
            'image_quality':'clear', 'confidence':0.95, 'summary':'测试替身：可见裂缝', **changes}


def resolve(client, ident, data=None, token='execution-secret', auth='test-tool-secret'):
    return client.post('/api/tools/resolve', headers={'Authorization':'Bearer '+auth}, json={
        'case_id':ident, 'execution_token':token, 'analysis':json.dumps(data if data is not None else analysis())})


def test_create_readback_idempotency_and_persistence(client):
    ident = pending(client)
    result = resolve(client, ident).json()
    assert result['status'] == 'application_created'
    assert result['application']['status'] == 'created'
    assert 'execution_token' not in result
    application_id = result['application']['id']
    assert client.get('/api/returns/'+application_id).json()['order_id'] == 'DEMO-1001'
    assert resolve(client, ident).json()['application']['id'] == application_id
    second = pending(client)
    assert resolve(client, second).json()['application']['id'] == application_id
    with module.db() as con:
        assert con.execute('SELECT count(*) FROM returns').fetchone()[0] == 1
    assert client.get('/api/metrics').json()['created_applications'] == 1
    assert client.get('/api/metrics').json()['completed_cases'] == 2
    assert [e['step'] for e in result['trace']][-3:] == ['return_create','return_verify','resolve']
    assert client.get('/api/cases/'+ident).json()['application']['id'] == application_id


@pytest.mark.parametrize('changes,reason', [
    ({'image_quality':'blurry'}, '图片'), ({'image_quality':'unrelated'}, '图片'),
    ({'product_match':False}, '证据'), ({'damaged':False}, '证据'),
    ({'confidence':0.2}, '证据'), ({'order_id':'CONFLICT'}, '冲突'),
])
def test_model_evidence_handoff(client, changes, reason):
    result = resolve(client, pending(client), analysis(**changes)).json()
    assert result['status'] == 'handoff' and reason in result['reason']
    assert result['application'] is None


@pytest.mark.parametrize('order,reason', [('MISSING','不存在'), ('DEMO-1002','30天'), ('DEMO-1003','未签收')])
def test_policy_and_order_failures(client, order, reason):
    result = resolve(client, pending(client, order), analysis(order_id=order)).json()
    assert result['status'] == 'handoff' and reason in result['reason']


@pytest.mark.parametrize('data', [{}, {'confidence':4}, {'damaged':'true'}, {'extra':'injection'}, {'confidence':float('nan')}])
def test_invalid_model_structure(client, data):
    result = resolve(client, pending(client), {**analysis(), **data} if data else {}).json()
    assert result['status'] == 'handoff'
    assert result['trace'][-1]['valid'] == 0


def test_missing_fields_and_unconfigured_dify(client):
    ident = client.post('/api/cases', data={'order_id':'DEMO-1001'}).json()['id']
    result = client.get('/api/cases/'+ident).json()
    assert result['status'] == 'needs_information' and '照片' in result['reason']
    response = client.post('/api/cases', data={'order_id':'DEMO-1001','description':'损坏'}, files={'image':('x.png',photo(),'image/png')})
    assert client.get('/api/cases/'+response.json()['id']).json()['reason'] == 'Dify 未配置，未执行视觉分析'
    assert client.get('/api/health').json()['dify_configured'] is False


def test_invalid_upload_and_input(client):
    assert client.post('/api/cases', data={'order_id':'  '}).status_code == 422
    assert client.post('/api/cases', data={'order_id':'x','description':'x'}, files={'image':('x.png',b'not an image','image/png')}).status_code == 422
    assert client.post('/api/cases', data={'order_id':'x'}, files={'image':('x.png',b'x'*(module.MAX_IMAGE+1),'image/png')}).status_code == 413
    assert client.get('/api/orders/none').status_code == 404
    assert client.get('/api/returns/none').status_code == 404
    assert client.get('/api/cases/none').status_code == 404


def test_auth_and_cross_case_token(client):
    ident = pending(client)
    assert resolve(client, ident, auth='wrong').status_code == 401
    assert resolve(client, ident, token='wrong').status_code == 401
    with module.db() as con:
        con.execute("UPDATE cases SET execution_token='different-token' WHERE id=?", (ident,))
    assert resolve(client, ident).status_code == 401


def test_business_failure_requires_manual_check(client, monkeypatch):
    ident = pending(client)
    monkeypatch.setattr(module, 'application', lambda _: (_ for _ in ()).throw(sqlite3.OperationalError('simulated readback failure')))
    result = resolve(client, ident).json()
    assert result['status'] == 'handoff'
    assert any(e['step']=='return_create' for e in result['trace'])
    assert not any(e['step']=='return_verify' for e in result['trace'])


def test_restart_recovery(client):
    ident = pending(client)
    module.init_db()
    result = client.get('/api/cases/'+ident).json()
    assert result['status'] == 'handoff' and '重启' in result['reason']
    assert resolve(client, ident).status_code == 401


def test_metrics_are_derived_and_unknown_cost_is_null(client):
    empty = client.get('/api/metrics').json()
    assert empty['completion_rate'] is None and empty['average_api_cost'] is None
    resolve(client, pending(client))
    missing = client.post('/api/cases',data={'order_id':'x'}).json()['id']
    result = client.get('/api/metrics').json()
    assert result['total_cases']==2 and result['created_applications']==1
    assert result['completion_rate']==0.5 and result['tool_success_rate']==1
    assert result['parameter_accuracy']==1 and result['priced_cases']==0
    assert client.get('/api/cases/'+missing).json()['status']=='needs_information'


def test_corrupt_png_checksum_is_validation_error(client):
    import base64
    corrupt=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==')
    response=client.post('/api/cases',data={'order_id':'x'},files={'image':('bad.png',corrupt,'image/png')})
    assert response.status_code==422


def test_product_lookup_and_non_returnable(client):
    assert client.get('/api/products/CUP-WHITE').json()['sku']=='CUP-W-001'
    assert client.get('/api/products/unknown').status_code==404
    assert client.get('/api/orders/DEMO-1001').json()['product_info']['returnable']==1
    ident=pending(client)
    with module.db() as con:
        con.execute("UPDATE products SET returnable=0 WHERE id='CUP-WHITE'")
    result=resolve(client,ident).json()
    assert result['status']=='handoff' and '不支持' in result['reason']
