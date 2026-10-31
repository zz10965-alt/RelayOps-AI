import ast
import json
from pathlib import Path
import yaml


def test_workflow_graph_and_json_escaping():
    workflow = yaml.safe_load(Path('workflows/relayops.yml').read_text())
    graph = workflow['workflow']['graph']
    nodes = {n['id']: n['data'] for n in graph['nodes']}
    assert nodes['vision']['vision']['enabled']
    assert nodes['start']['variables'][-1]['type'] == 'file'
    assert [(e['source'],e['target']) for e in graph['edges']] == [('start','order'),('order','policy'),('policy','vision'),('vision','serialize'),('serialize','resolve'),('resolve','end')]
    namespace = {}
    code = nodes['serialize']['code']
    ast.parse(code)
    exec(code, namespace)
    analysis = {'order_id':'DEMO-1001','damaged':True,'product_match':True,'image_quality':'clear','confidence':0.95,'summary':'quoted " text\n你好'}
    serialized = namespace['main'](analysis, 'case"\n', 'token\\quoted')['body']
    body = nodes['resolve']['body']['data'][0]['value'].replace('{{#serialize.body#}}', serialized)
    parsed=json.loads(body)
    assert json.loads(parsed['analysis']) == analysis
    assert parsed['case_id']=='case"\n' and parsed['execution_token']=='token\\quoted'
    assert nodes['vision']['structured_output_enabled']
    schema=nodes['vision']['structured_output']['schema']
    assert schema==json.loads(Path('workflows/analysis.schema.json').read_text())
    assert set(schema['required'])==set(analysis)
    assert schema['additionalProperties'] is False
    assert nodes['vision']['model']['provider']=='langgenius/openai/openai'
    assert nodes['vision']['model']['name']=='gpt-4.1-mini'
    assert nodes['serialize']['variables'][0]['value_selector']==['vision','structured_output']
    for ident in ('order','policy','resolve'):
        assert nodes[ident]['ssl_verify'] is True
        assert set(nodes[ident]['timeout'])=={'connect','read','write'}
        assert '{{#env.BUSINESS_API_TOKEN#}}' in nodes[ident]['headers']
    assert workflow['workflow']['environment_variables'][0]['value'].startswith('https://')
    assert workflow['workflow']['environment_variables'][1]['value'] == ''


def test_cloud_package_manifest_and_payload():
    import hashlib
    import zipfile
    with zipfile.ZipFile('workflows/relayops.ifpkg') as package:
        assert set(package.namelist())=={'manifest.yaml','app.yaml'}
        manifest=yaml.safe_load(package.read('manifest.yaml'))
        assert manifest['format']=='dify.app' and manifest['format_version']==1
        resource=manifest['apps'][0]
        payload=package.read(resource['path'])
        assert resource['size']==len(payload)
        assert resource['sha256']==hashlib.sha256(payload).hexdigest()
        assert payload==Path('workflows/relayops.yml').read_bytes()
