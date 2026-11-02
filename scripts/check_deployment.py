"""Offline deployment checks; does not claim deployment or model readiness."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
docker = (root/'Dockerfile').read_text()
assert '${PORT:-8000}' in docker and '--workers 1' in docker
assert 'RELAYOPS_PUBLIC_DEMO=1' in docker and '/data/relayops.sqlite3' in docker
assert json.loads((root/'railway.json').read_text())['deploy']['healthcheckPath']=='/api/health'
assert json.loads((root/'web/vercel.json').read_text())['outputDirectory']=='dist'
assets = list((root/'web/dist/assets').glob('*.js'))
assert assets, 'Build the frontend first'
for path in assets:
    text=path.read_text()
    for forbidden in ('DIFY_API_KEY','DIFY_TOOL_TOKEN','RELAYOPS_DEMO_TOKEN','app-test-only-secret','test-tool-secret'):
        assert forbidden not in text, f'Server-side marker found in {path.name}'
print('Deployment static checks PASS; no server secret identifiers/test tokens in frontend bundle. Actual secret values and cloud deployment not verified.')
