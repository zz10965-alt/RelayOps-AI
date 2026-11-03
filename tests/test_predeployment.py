"""Predeployment regressions. No live model calls or production data."""
import pytest
from fastapi.testclient import TestClient
from backend import app as module
from tests.test_api import client


@pytest.mark.parametrize('origin', ['https://example.com?x=1','https://example.com#x',
    'https://user:pass@example.com','https://*.example.com','https://example.com:bad','https://example.com/'])
def test_invalid_origin(origin):
    assert not module.valid_https_origin(origin)


def test_valid_origin():
    assert module.valid_https_origin('https://demo.example.com')


def test_streamed_oversize_body(client):
    def chunks():
        for _ in range(6):
            yield b'x' * 1024 * 1024
    assert client.post('/api/demo/orders',content=chunks(),headers={'Content-Type':'application/json'}).status_code==413


def test_negative_content_length(client):
    assert client.post('/api/demo/orders',content=b'{}',headers={'Content-Length':'-1'}).status_code==400


def test_nonascii_execution_token(client):
    from tests.test_api import pending, resolve
    response=resolve(client,pending(client),token='无效凭据')
    assert response.status_code==401


def test_database_escape_rejected(monkeypatch):
    monkeypatch.setenv('RELAYOPS_PUBLIC_DEMO','1')
    monkeypatch.setenv('RELAYOPS_DEMO_TOKEN','x'*32)
    monkeypatch.setattr(module,'DB','/data/../tmp/escape.sqlite3')
    with pytest.raises(RuntimeError,match='under /data'):
        with TestClient(module.app):
            pass



@pytest.mark.parametrize('url', ['http://remote.example','https://user:pass@example.com','https://example.com?token=x','https://example.com/api'])
def test_live_acceptance_rejects_unsafe_origin(url):
    from scripts.live_e2e import acceptance_headers
    with pytest.raises(ValueError):
        acceptance_headers(url,{})


def test_live_acceptance_separates_credentials():
    from scripts.live_e2e import acceptance_headers
    operator,tool,proxy=acceptance_headers('https://api.example.com',{'RELAYOPS_DEMO_TOKEN':'operator-fixture','DIFY_TOOL_TOKEN':'tool-fixture'})
    assert operator=={'Authorization':'Bearer operator-fixture'}
    assert tool=={'Authorization':'Bearer tool-fixture'} and proxy
    assert acceptance_headers('http://127.0.0.1:8000',{})==({},{},False)


def test_local_live_still_requires_authentication(monkeypatch,tmp_path):
    monkeypatch.setenv('RELAYOPS_LOCAL_LIVE','1')
    monkeypatch.setenv('RELAYOPS_PUBLIC_DEMO','0')
    monkeypatch.setattr(module,'DB',str(tmp_path/'local.sqlite3'))
    with pytest.raises(RuntimeError,match='requires authenticated'):
        with TestClient(module.app): pass


def test_protected_local_storage_and_cors(monkeypatch,tmp_path):
    monkeypatch.setenv('RELAYOPS_LOCAL_LIVE','1')
    monkeypatch.setenv('RELAYOPS_PUBLIC_DEMO','1')
    monkeypatch.setenv('RELAYOPS_DEMO_TOKEN','operator-fixture-'+'x'*32)
    monkeypatch.setenv('RELAYOPS_CORS_ORIGINS','https://portfolio.example')
    monkeypatch.setenv('RELAYOPS_ALLOW_MODEL_EXECUTION','0')
    for name in ('DIFY_BASE_URL','DIFY_API_KEY','DIFY_TOOL_TOKEN'):monkeypatch.delenv(name,raising=False)
    monkeypatch.setattr(module,'DB',str(tmp_path/'windows-local.sqlite3'))
    with TestClient(module.app) as client:
        assert client.get('/api/cases').status_code==401
        assert client.get('/api/health').json()['execution_enabled'] is False
        assert client.post('/api/cases',headers={'Authorization':'Bearer '+module.os.environ['RELAYOPS_DEMO_TOKEN']}).status_code==403
    assert module.valid_local_origin('http://127.0.0.1:8003')
    assert not module.valid_local_origin('http://remote.example')
    assert not module.valid_local_origin('http://user@localhost:8003')
