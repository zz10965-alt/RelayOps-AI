"""Offline deployment checks; does not claim deployment or model readiness."""
import argparse
import json
from html.parser import HTMLParser
import yaml
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
simulation = (root/'web/src/simulation.ts').read_text()
assert 'fetch(' not in simulation and 'XMLHttpRequest' not in simulation
for path in ('web/src/data.ts','web/src/main.tsx'):
    source = (root/path).read_text()
    assert 'localStorage' not in source and 'sessionStorage' not in source
print('Deployment static checks PASS; static simulation and memory-only connection checks passed; no server secret identifiers/test tokens in frontend bundle. Actual secret values and cloud deployment not verified.')


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pages', action='store_true', help='Also verify the separate Pages build and manual-only publication contract')
args = parser.parse_args()
if args.pages:
    directory = root/'web/dist-pages'
    class Assets(HTMLParser):
        def __init__(self):
            super().__init__()
            self.urls = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'script' and attrs.get('src'):
                self.urls.append(attrs['src'])
            if tag == 'link' and attrs.get('rel') in ('stylesheet', 'modulepreload'):
                self.urls.append(attrs['href'])
    html = Assets()
    html.feed((directory/'index.html').read_text())
    assert html.urls, 'Pages index must reference built assets'
    for url in html.urls:
        assert url.startswith('/RelayOps-AI/assets/'), url
        asset = directory/url.removeprefix('/RelayOps-AI/')
        assert asset.is_file(), 'Broken Pages asset: '+url
    for path in directory.rglob('*'):
        assert not path.is_symlink()
        if path.is_file():
            assert path.suffix in ('.html', '.js', '.css', '.png'), path.name
            if path.suffix == '.png':
                assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), path.name
                continue
            text = path.read_text()
            assert not any(key in text for key in ('DIFY_API_KEY','DIFY_TOOL_TOKEN','RELAYOPS_DEMO_TOKEN','operator-test-fixture','test-tool-secret')), path.name
    workflow = yaml.load((root/'.github/workflows/pages.yml').read_text(), Loader=yaml.BaseLoader)
    assert set(workflow['on']) == {'workflow_dispatch'}, 'Publishing must require explicit manual action'
    assert workflow['jobs']['build']['if'] == "github.ref == 'refs/heads/main'"
    assert workflow['jobs']['build']['permissions']['pages'] == 'read'
    assert workflow['jobs']['deploy']['needs'] == 'build'
    assert workflow['jobs']['deploy']['permissions'] == {'pages':'write','id-token':'write'}
    assert workflow['jobs']['deploy']['environment']['name'] == 'github-pages'
    uploads = [s for s in workflow['jobs']['build']['steps'] if s.get('uses','').startswith('actions/upload-pages-artifact@')]
    assert len(uploads) == 1 and uploads[0]['with']['path'] == 'web/dist-pages'
    print('GitHub Pages checks PASS: subpath asset files, clean static artifact, manual-only main-branch deployment and scoped permissions.')
