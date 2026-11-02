from datetime import date
from fastapi.testclient import TestClient
from backend import app as module
from tests.test_api import client, pending, resolve, analysis


def test_fresh_orders_repeat_and_policy(client):
    a = client.post('/api/demo/orders', json={'scenario':'eligible'}).json()
    b = client.post('/api/demo/orders', json={'scenario':'eligible'}).json()
    assert a['id'] != b['id']
    assert (date.today()-date.fromisoformat(a['delivered_on'])).days == 3
    for order in (a,b):
        result = resolve(client, pending(client, order['id']), analysis(order_id=order['id'])).json()
        assert result['application']['status'] == 'created'
        assert [s['status'] for s in result['stages']] == ['succeeded','succeeded','recorded','succeeded','succeeded']
    expired = client.post('/api/demo/orders', json={'scenario':'expired'}).json()
    result = resolve(client, pending(client, expired['id']), analysis(order_id=expired['id'])).json()
    assert result['status'] == 'handoff' and result['application'] is None
    assert result['stages'][2]['status'] == 'handoff'
    assert result['stages'][3]['status'] == 'not_observed'


def test_unexecuted_timeline(client):
    ident = client.post('/api/cases', data={'order_id':'DEMO-1001'}).json()['id']
    assert all(s['status'] == 'not_observed' for s in client.get('/api/cases/'+ident).json()['stages'])


def test_public_guards(client, monkeypatch):
    monkeypatch.setenv('RELAYOPS_PUBLIC_DEMO','1')
    monkeypatch.setenv('RELAYOPS_DEMO_TOKEN','x'*32)
    module.submission_times.clear()
    assert client.get('/api/cases').status_code == 401
    assert client.get('/api/health').status_code == 200
    auth={'Authorization':'Bearer '+'x'*32}
    assert client.get('/api/cases',headers=auth).status_code == 200
    assert client.get('/api/orders/DEMO-1001',headers=auth).status_code == 401
    assert client.get('/api/orders/DEMO-1001',headers={'Authorization':'Bearer test-tool-secret'}).status_code == 200
    assert client.post('/api/cases',headers=auth).status_code == 403
    monkeypatch.setenv('RELAYOPS_ALLOW_MODEL_EXECUTION','1')
    assert client.post('/api/cases',headers={**auth,'Content-Length':str(6*1024*1024)}).status_code == 413
    for _ in range(10):
        assert client.post('/api/demo/orders',json={},headers=auth).status_code == 201
    assert client.post('/api/demo/orders',json={},headers=auth).status_code == 429
    module.submission_times.clear()


def test_public_startup_fails_closed(monkeypatch):
    monkeypatch.setenv('RELAYOPS_PUBLIC_DEMO','1')
    monkeypatch.delenv('RELAYOPS_DEMO_TOKEN',raising=False)
    import pytest
    with pytest.raises(RuntimeError, match='operator token'):
        with TestClient(module.app):
            pass


def test_public_concurrency_limit(client, monkeypatch):
    monkeypatch.setenv('RELAYOPS_PUBLIC_DEMO','1')
    monkeypatch.setenv('RELAYOPS_DEMO_TOKEN','x'*32)
    monkeypatch.setenv('RELAYOPS_ALLOW_MODEL_EXECUTION','1')
    with module.db() as con:
        for ident in ('active-a','active-b'):
            con.execute("INSERT INTO cases(id,order_id,description,status,created) VALUES(?,?,?,'running',0)", (ident,'DEMO-1001','test fixture'))
    response=client.post('/api/cases',data={'order_id':'DEMO-1001'},headers={'Authorization':'Bearer '+'x'*32})
    assert response.status_code==429
    with module.db() as con:
        assert con.execute('SELECT count(*) FROM cases').fetchone()[0]==2
    module.submission_times.clear()
