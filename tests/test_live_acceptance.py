"""CLI acceptance contracts with HTTP substitutes only; never actual Dify execution."""
import json
import sys
import httpx
import pytest
from scripts import live_e2e


@pytest.mark.parametrize('mode', ['created','handoff','wrong_readback','side_effect'])
def test_live_cli_expected_outcome_and_independent_readback(monkeypatch, capsys, mode):
    application={'id':'fixture-return','order_id':'FRESH-FIXTURE','status':'created'}
    handoff=mode in ('handoff','side_effect')
    case={'id':'fixture-case','run_id':'fixture-run','status':'handoff' if handoff else 'application_created',
          'reason':'图片模糊' if handoff else '申请已创建','application':None if handoff else application,
          'trace':[{'step':'workflow','success':True,'detail':{'run_id':'fixture-run','status':'succeeded'}}]}
    if not handoff or mode=='side_effect':
        case['trace'] += [{'step':'return_create','success':True,'detail':application},
                          {'step':'return_verify','success':True,'detail':application}]
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        if request.url.path=='/api/health':
            return httpx.Response(200,json={'public_demo':True,'execution_enabled':True,'dify_configured':True})
        if request.url.path=='/api/demo/orders':
            assert json.loads(request.content)=={'scenario':'eligible'}
            return httpx.Response(201,json={'id':'FRESH-FIXTURE'})
        if request.url.path=='/api/cases':
            assert b'FRESH-FIXTURE' in request.content
            return httpx.Response(202,json={'id':'fixture-case'})
        if request.url.path=='/api/cases/fixture-case': return httpx.Response(200,json=case)
        if request.url.path=='/api/returns/fixture-return':
            return httpx.Response(200,json={**application,'id':'WRONG'} if mode=='wrong_readback' else application)
        raise AssertionError('Unexpected HTTP request')
    real_client=httpx.Client
    monkeypatch.setattr(live_e2e.httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(handler),**kwargs))
    monkeypatch.setenv('RELAYOPS_DEMO_TOKEN','operator-fixture-not-real')
    monkeypatch.setenv('DIFY_TOOL_TOKEN','tool-fixture-not-real')
    monkeypatch.setattr(sys,'argv',['live_e2e.py','--create-order','eligible','--image','tests/fixtures/evidence.png',
                                  '--expect','handoff' if handoff else 'application_created'])
    if mode in ('wrong_readback','side_effect'):
        with pytest.raises(SystemExit,match='FAIL:'): live_e2e.main()
    else:
        live_e2e.main()
        assert 'PASS:' in capsys.readouterr().out
    assert ('/api/returns/fixture-return' in calls)==(not handoff)
