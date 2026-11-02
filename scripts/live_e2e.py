"""Opt-in REAL Dify acceptance. No mocks. Requires running configured API."""
import argparse
import json
import os
from urllib.parse import urlsplit
import time
from pathlib import Path
import httpx

def acceptance_headers(api, environ):
    parsed = urlsplit(api)
    local = parsed.hostname in ('127.0.0.1', 'localhost', '::1')
    if (parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/')
            or parsed.scheme not in ('http','https') or not parsed.hostname
            or (parsed.scheme == 'http' and not local)):
        raise ValueError('Acceptance API must be an HTTPS origin or local loopback origin')
    operator = {'Authorization':'Bearer '+environ['RELAYOPS_DEMO_TOKEN']} if environ.get('RELAYOPS_DEMO_TOKEN') else {}
    tool = {'Authorization':'Bearer '+environ['DIFY_TOOL_TOKEN']} if environ.get('DIFY_TOOL_TOKEN') else {}
    return operator, tool, not local


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api', default='http://127.0.0.1:8000')
    parser.add_argument('--image', required=True, help='Real clear photo of the damaged synthetic order product')
    parser.add_argument('--order',default='DEMO-1001')
    parser.add_argument('--description',default='白色陶瓷杯损坏，请根据照片核查')
    args=parser.parse_args()
    operator, tool, trust_env = acceptance_headers(args.api, os.environ)
    with httpx.Client(base_url=args.api, timeout=30, trust_env=trust_env, headers=operator) as client:
        health=client.get('/api/health');health.raise_for_status()
        if health.json().get('public_demo') and (not operator or not tool or not health.json().get('execution_enabled')):
            raise SystemExit('BLOCKED: public acceptance requires protected operator/tool credentials and explicit execution approval')
        if not health.json()['dify_configured']: raise SystemExit('BLOCKED: Dify server configuration missing; no live test executed')
        with Path(args.image).open('rb') as image:
            response=client.post('/api/cases',data={'order_id':args.order,'description':args.description},files={'image':(Path(args.image).name,image)})
        response.raise_for_status();ident=response.json()['id']
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            response=client.get('/api/cases/'+ident);response.raise_for_status();case=response.json()
            # Callback may finish the case before Dify returns run_id/workflow status.
            workflow_finished=any(e['step']=='workflow' for e in case['trace'])
            if case['status'] not in ('queued','running') and (workflow_finished or case['status']=='needs_information'): break
            time.sleep(2)
        else: raise SystemExit(f'FAIL: case {ident} did not finish')
        print(json.dumps({'case_id':ident,'status':case['status'],'reason':case['reason'],'run_id':case['run_id'],'application':case['application']},ensure_ascii=False,indent=2))
        if case['status']!='application_created' or not case['run_id'] or not case['application']:
            raise SystemExit('FAIL: live happy path not verified; review trace and Dify run logs')
        application=client.get('/api/returns/'+case['application']['id'], headers=tool);application.raise_for_status()
        assert application.json()['status']=='created'
        assert application.json()['order_id']==args.order
        assert any(e['step']=='return_verify' and e['success'] for e in case['trace'])
        assert any(e['step']=='workflow' and e['success'] for e in case['trace'])
        print('PASS: real Dify run + tool execution + independent API readback (not approved/refunded)')


if __name__=='__main__':
    main()
