import ast
import hashlib
import json
import zipfile
from pathlib import Path
import pytest
import yaml


def workflow():
    return yaml.safe_load(Path('workflows/relayops.yml').read_text())


def code_main(ident):
    data=next(n['data'] for n in workflow()['workflow']['graph']['nodes'] if n['id']==ident)
    namespace={}
    ast.parse(data['code'])
    exec(data['code'],namespace)
    return namespace['main']


def evidence(**changes):
    return {'order_id':'DEMO-1001','damaged':True,'product_match':True,'image_quality':'clear',
            'confidence':0.95,'summary':'清晰可见裂缝 "quoted"\n你好',**changes}


def parse(data):
    return code_main('parse')(json.dumps(data,ensure_ascii=False),'DEMO-1001','case','execution-secret')


def test_workflow_model_files_headers_and_edges():
    w=workflow();graph=w['workflow']['graph'];nodes={n['id']:n['data'] for n in graph['nodes']}
    model=nodes['vision']['model']
    assert model['provider']=='langgenius/deepseek/deepseek' and model['name']=='deepseek-flash'
    assert model['completion_params']['response_format']=='json_object'
    assert model['completion_params']['thinking'] is False
    assert nodes['vision']['structured_output_enabled'] is False
    assert nodes['vision']['vision']['configs']['variable_selector']==['start','image']
    upload=w['workflow']['features']['file_upload']
    assert upload['enabled'] and upload['image']['enabled']
    assert nodes['start']['variables'][-1]['required'] and nodes['start']['variables'][-1]['type']=='file'
    for ident in ('order','policy','resolve'):
        assert nodes[ident]['ssl_verify'] is True
        assert set(nodes[ident]['timeout'])=={'connect','read','write'}
        assert '{{#env.BUSINESS_API_TOKEN#}}' in nodes[ident]['headers']
    env=w['workflow']['environment_variables']
    assert all(e['value']=='' for e in env)
    assert env[1]['value_type']=='secret'
    incoming=[e for e in graph['edges'] if e['target']=='resolve']
    assert len(incoming)==1 and incoming[0]['source']=='evidence' and incoming[0]['sourceHandle']=='eligible'
    for ident in ('config','order','policy','vision','parse','resolve','verify'):
        assert nodes[ident]['error_strategy']=='fail-branch'
        assert any(e['source']==ident and e['sourceHandle']=='fail-branch' and e['target']=='manual' for e in graph['edges'])
    assert nodes['resolve']['retry_config']['retry_enabled'] is False
    assert nodes['end']['outputs'][0]['value_selector']==['verify','result']
    for edge in graph['edges']:
        assert edge['source'] in nodes and edge['target'] in nodes
    # Every node must be reachable from Start. Success End is gated by backend verification.
    seen={'start'}
    while True:
        updated=seen|{e['target'] for e in graph['edges'] if e['source'] in seen}
        if updated==seen:break
        seen=updated
    assert seen==set(nodes)
    assert [e['sourceHandle'] for e in graph['edges'] if e['target']=='end']==['true']


def test_json_validation_serialization_and_threshold():
    result=parse(evidence())
    assert result['route']=='eligible'
    body=json.loads(result['body'])
    assert body['case_id']=='case' and body['execution_token']=='execution-secret'
    assert json.loads(body['analysis'])==evidence()
    assert parse(evidence(confidence=0.8))['route']=='eligible'


@pytest.mark.parametrize('changes,route',[
    ({'image_quality':'blurry'},'supplement'),({'image_quality':'unrelated'},'handoff'),
    ({'product_match':False},'handoff'),({'confidence':0.79},'handoff'),({'damaged':False},'handoff'),
    ({'order_id':'OTHER'},'handoff'),({'confidence':True},'handoff'),({'confidence':'0.95'},'handoff'),
    ({'confidence':float('nan')},'handoff'),({'confidence':float('inf')},'handoff'),
    ({'damaged':'true'},'handoff'),({'unexpected':'extra'},'handoff'),({'summary':'x'*1001},'handoff')])
def test_inadequate_evidence_never_produces_resolve_body(changes,route):
    result=parse(evidence(**changes))
    assert result['route']==route and result['body']==''


@pytest.mark.parametrize('text',['{}','not json','{"damaged":true,"damaged":false}','[]','x'*6001])
def test_malformed_or_duplicate_json_is_handoff(text):
    assert code_main('parse')(text,'DEMO-1001','case','token')['route']=='handoff'


def test_exact_markdown_fence_supported_but_surrounding_prose_rejected():
    valid=json.dumps(evidence())
    main=code_main('parse')
    assert main('```json\n'+valid+'\n```','DEMO-1001','case','token')['route']=='eligible'
    assert main('I recommend '+valid,'DEMO-1001','case','token')['route']=='handoff'


def test_result_checker_requires_matching_backend_readback():
    main=code_main('verify')
    application={'id':'return','order_id':'DEMO-1001','status':'created'}
    data={'id':'case','order_id':'DEMO-1001','status':'application_created','application':application,
          'trace':[{'step':'return_verify','success':1,'detail':dict(application)}]}
    assert main(json.dumps(data),200,'case','DEMO-1001')['verified']=='yes'
    for changed in ({'application':None},{'trace':[]},{'id':'wrong'},{'status':'approved'}):
        assert main(json.dumps({**data,**changed}),200,'case','DEMO-1001')['verified']=='no'
    assert main(json.dumps(data),500,'case','DEMO-1001')['verified']=='no'
    assert main('not JSON',200,'case','DEMO-1001')['verified']=='no'
    data['trace'][0]['detail']['order_id']='DIFFERENT'
    assert main(json.dumps(data),200,'case','DEMO-1001')['verified']=='no'


def test_manual_and_supplement_results_never_claim_creation():
    for ident in ('manual','supplement'):
        result=json.loads(code_main(ident)()['result'])
        assert result['status']=='handoff' and result['application'] is None


@pytest.mark.parametrize('url',['','http://localhost:8000','https://127.0.0.1','https://api.example.invalid','https://10.0.0.1','https://user:secret@api.example.com'])
def test_config_guard_blocks_unconfigured_or_private_addresses(url):
    assert code_main('config')(url)['ready']=='no'


def test_cloud_package_manifest_and_payload():
    with zipfile.ZipFile('workflows/relayops.ifpkg') as package:
        assert package.testzip() is None
        assert set(package.namelist())=={'manifest.yaml','app.yaml'}
        manifest=yaml.safe_load(package.read('manifest.yaml'))
        assert manifest['format']=='dify.app' and manifest['format_version']==1
        resource=manifest['apps'][0];payload=package.read(resource['path'])
        assert resource['size']==len(payload) and resource['sha256']==hashlib.sha256(payload).hexdigest()
        assert payload==Path('workflows/relayops.yml').read_bytes()
