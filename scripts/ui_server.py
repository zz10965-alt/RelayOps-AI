"""Isolated real backend for browser tests; intentionally no Dify credentials."""
import os
import sys
import tempfile
from pathlib import Path
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for key in ('DIFY_BASE_URL','DIFY_API_KEY','DIFY_TOOL_TOKEN'):
    os.environ.pop(key, None)
with tempfile.TemporaryDirectory(prefix='relayops-ui-') as directory:
    os.environ['RELAYOPS_DB'] = directory+'/ui.sqlite3'
    os.environ['RELAYOPS_LOCAL_LIVE'] = '1'
    os.environ['RELAYOPS_PUBLIC_DEMO'] = '1'
    os.environ['RELAYOPS_DEMO_TOKEN'] = 'operator-test-fixture-32-characters-only'
    os.environ['RELAYOPS_CORS_ORIGINS'] = 'http://127.0.0.1:8001,http://127.0.0.1:8003'
    os.environ['RELAYOPS_ALLOW_MODEL_EXECUTION'] = '1' # Test backend has no Dify credentials; no model can be called.
    uvicorn.run('backend.app:app', host='127.0.0.1', port=8001)
