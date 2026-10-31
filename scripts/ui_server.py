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
    uvicorn.run('backend.app:app', host='127.0.0.1', port=8001)
