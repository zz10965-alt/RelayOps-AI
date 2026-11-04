import sqlite3
import pytest
from scripts.dify_preflight import checks
from scripts.verify_case_db import verify
from tests.test_api import client, pending, resolve
from backend import app as module


def test_preflight_reports_presence_without_secret_values():
    config={'DIFY_BASE_URL':'https://api.dify.ai/v1','DIFY_API_KEY':'not-a-real-secret','DIFY_TOOL_TOKEN':'another-secret','BUSINESS_API_URL':'https://callback.example.com'}
    result=checks(config)
    assert result['cloud_base_url']=='valid'
    assert 'not-a-real-secret' not in str(result) and 'another-secret' not in str(result)
    assert result['BUSINESS_API_URL'].startswith('candidate_https')
    assert checks({})['DIFY_API_KEY']=='missing'


@pytest.mark.parametrize('url',['http://localhost:8000','https://host.docker.internal','https://relayops-api.example.invalid','https://user:secret@callback.example.com','https://127.0.0.2','https://10.0.0.1','https://[::1]'])
def test_preflight_rejects_unsafe_callback_candidates(url):
    assert checks({'BUSINESS_API_URL':url})['BUSINESS_API_URL']=='invalid_callback'


def test_independent_db_verifier_requires_workflow_evidence(client):
    ident=pending(client)
    result=resolve(client,ident).json()
    assert result['status']=='application_created'
    with pytest.raises(ValueError): verify(module.DB,ident)
    # Explicit synthetic fixture: this is NOT a real Dify run.
    with module.db() as con: con.execute("UPDATE cases SET run_id='synthetic-test-run' WHERE id=?",(ident,))
    module.event(ident,'workflow',True,{'test_fixture':True,'run_id':'synthetic-test-run','status':'succeeded'})
    assert verify(module.DB,ident)['id']==result['application']['id']
    with module.db() as con: con.execute("UPDATE returns SET status='approved' WHERE id=?",(result['application']['id'],))
    with pytest.raises(ValueError): verify(module.DB,ident)


@pytest.mark.parametrize('step', ['return_create','return_verify','workflow'])
def test_db_verifier_rejects_unrelated_success_events(client, step):
    ident=pending(client)
    result=resolve(client,ident).json()
    with module.db() as con:
        con.execute("UPDATE cases SET run_id='synthetic-test-run' WHERE id=?",(ident,))
    module.event(ident,'workflow',True,{'run_id':'synthetic-test-run','status':'succeeded'})
    assert verify(module.DB,ident)['id']==result['application']['id']
    with module.db() as con:
        con.execute("UPDATE events SET detail='{}' WHERE case_id=? AND step=?",(ident,step))
    with pytest.raises(ValueError, match='matching'):
        verify(module.DB,ident)
