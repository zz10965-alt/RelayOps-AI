"""Representative real HTTP smoke test against running local demo; no model stub."""
import httpx

with httpx.Client(base_url='http://127.0.0.1:8000',trust_env=False,timeout=20) as client:
    health=client.get('/api/health');health.raise_for_status();assert health.json()['status']=='ok'
    page=client.get('/');page.raise_for_status();assert 'RelayOps AI' in page.text
    order=client.get('/api/orders/DEMO-1001');order.raise_for_status();assert order.json()['product']=='白色陶瓷杯'
    policy=client.get('/api/policy');policy.raise_for_status();assert policy.json()['return_window_days']==30
    response=client.post('/api/cases',data={'order_id':'DEMO-1001'});assert response.status_code==202
    ident=response.json()['id']
    detail=client.get('/api/cases/'+ident);detail.raise_for_status()
    assert detail.json()['status']=='needs_information' and detail.json()['application'] is None
    metrics=client.get('/api/metrics');metrics.raise_for_status();assert metrics.json()['total_cases']>=1
    print('HTTP smoke PASS: health + static UI + order + policy + persisted missing-evidence case + metrics; no Dify/model claim')
