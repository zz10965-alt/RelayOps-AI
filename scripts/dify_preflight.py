"""Non-secret Dify Cloud configuration audit; no network calls unless requested."""
import argparse
import ipaddress
import os
from urllib.parse import urlsplit
import httpx


def checks(environ):
    result = {}
    for name in ('DIFY_BASE_URL', 'DIFY_API_KEY', 'DIFY_TOOL_TOKEN'):
        result[name] = 'present' if environ.get(name) else 'missing'
    base = urlsplit(environ.get('DIFY_BASE_URL', ''))
    result['cloud_base_url'] = 'valid' if (base.scheme == 'https' and base.hostname == 'api.dify.ai' and base.path.rstrip('/') == '/v1' and not base.username and not base.password and not base.query and not base.fragment and base.port in (None,443)) else 'invalid_or_missing'
    raw = environ.get('BUSINESS_API_URL')
    if not raw:
        result['BUSINESS_API_URL'] = 'not_in_backend_env; set in Dify Workflow environment (cannot inspect remotely)'
    else:
        callback = urlsplit(raw)
        host = (callback.hostname or '').lower().rstrip('.')
        try:
            local_host = not ipaddress.ip_address(host).is_global
        except ValueError:
            local_host = host == 'localhost' or host.endswith(('.localhost','.local','.internal','.invalid'))
        result['BUSINESS_API_URL'] = 'candidate_https; public reachability unverified' if (callback.scheme == 'https' and callback.hostname and not local_host and not callback.username and not callback.password and not callback.query and not callback.fragment) else 'invalid_callback'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-api', action='store_true', help='Read-only /info and /parameters calls using existing server credentials')
    args=parser.parse_args()
    try:
        result=checks(os.environ)
    except ValueError:
        print('BLOCKED: malformed URL configuration (values not printed)')
        return 2
    for key,status in result.items(): print(key+': '+status)
    missing=any(result[k]=='missing' for k in ('DIFY_BASE_URL','DIFY_API_KEY','DIFY_TOOL_TOKEN'))
    if missing or result['cloud_base_url']!='valid' or result['BUSINESS_API_URL']=='invalid_callback':
        print('BLOCKED: configure environment securely; no live Dify request executed')
        return 2
    if not args.check_api:
        print('CONFIG ONLY: keys present; model, import, callback and E2E remain unverified')
        return 0
    try:
        with httpx.Client(base_url=os.environ['DIFY_BASE_URL'].rstrip('/')+'/', headers={'Authorization':'Bearer '+os.environ['DIFY_API_KEY']},timeout=20,follow_redirects=False) as client:
            info=client.get('info');info.raise_for_status()
            parameters=client.get('parameters');parameters.raise_for_status()
            data=parameters.json()
            if not isinstance(data,dict): raise ValueError('unexpected parameters')
            fields={key for entry in data.get('user_input_form',[]) for value in entry.values() if isinstance(value,dict) for key in [value.get('variable')]}
            if not {'case_id','execution_token','order_id','description','image'} <= fields:
                print('FAIL: published application inputs do not match this Workflow')
                return 1
        print('READ-ONLY API PASS: app key and published input names; no model invocation or E2E verified')
        return 0
    except (httpx.HTTPError,ValueError,TypeError,AttributeError):
        print('FAIL: read-only Dify API check failed; inspect credentials, published app and network policy. No response/secret printed.')
        return 1


if __name__=='__main__': raise SystemExit(main())
