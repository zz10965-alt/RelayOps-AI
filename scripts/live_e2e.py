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
    parser.add_argument('--create-order', choices=['eligible','expired','shipping'], help='Create a fresh synthetic business order before the explicitly approved model test')
    parser.add_argument('--expect', choices=['application_created','handoff'], default='application_created')
    parser.add_argument('--reason-contains', help='Require a specific business reason on a negative acceptance run')
    parser.add_argument('--description',default='白色陶瓷杯损坏，请根据照片核查')
    args=parser.parse_args()
    operator, tool, trust_env = acceptance_headers(args.api, os.environ)
    with httpx.Client(base_url=args.api, timeout=30, trust_env=trust_env, headers=operator) as client:
        health=client.get('/api/health');health.raise_for_status()
        if health.json().get('public_demo') and (not operator or not tool or not health.json().get('execution_enabled')):
            raise SystemExit('BLOCKED: public acceptance requires protected operator/tool credentials and explicit execution approval')
        if not health.json()['dify_configured']: raise SystemExit('BLOCKED: Dify server configuration missing; no live test executed')
        if args.create_order:
            response=client.post('/api/demo/orders',json={'scenario':args.create_order})
            response.raise_for_status()
            args.order=response.json()['id']
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
        if case['status']!=args.expect or not case['run_id']:
            raise SystemExit('FAIL: expected real Dify outcome not verified; review trace and Dify run logs')
        if args.reason_contains and args.reason_contains not in (case['reason'] or ''):
            raise SystemExit('FAIL: expected business reason missing')
        if not any(e['step']=='workflow' and e['success'] for e in case['trace']):
            raise SystemExit('FAIL: Dify workflow did not finish successfully')
        if args.expect=='handoff':
            if case['application'] or any(e['step'] in ('return_create','return_verify') and e['success'] for e in case['trace']):
                raise SystemExit('FAIL: handoff contains a business side effect; inspect database before retrying')
            print('PASS: real Dify handoff; no successful business action observed (not a happy-path success)')
            return
        if not case['application']:
            raise SystemExit('FAIL: missing persisted application')
        application=client.get('/api/returns/'+case['application']['id'], headers=tool);application.raise_for_status()
        record=application.json()
        if (record.get('id')!=case['application']['id'] or record.get('status')!='created'
                or record.get('order_id')!=args.order):
            raise SystemExit('FAIL: independent application readback does not match')
        if not any(e['step']=='return_verify' and e['success'] and
                   all(e['detail'].get(k)==record[k] for k in ('id','order_id','status')) for e in case['trace']):
            raise SystemExit('FAIL: missing matching successful return verification')
        print('PASS: real Dify run + tool execution + independent API readback (not approved/refunded)')


if __name__=='__main__':
    main()
