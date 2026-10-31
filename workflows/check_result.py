"""Dify Code node: only report success from a matching backend readback result."""
import json


def main(body: str, status_code: int, case_id: str, order_id: str) -> dict:
    failed = {'verified': 'no', 'result': json.dumps({'status': 'handoff', 'reason': '业务HTTP返回或回读证据不符合协议；未确认执行成功'}, ensure_ascii=False)}
    try:
        if status_code != 200:
            return failed
        data = json.loads(body)
        if not isinstance(data, dict) or data.get('id') != case_id or data.get('order_id') != order_id:
            return failed
        status = data.get('status')
        if status == 'handoff':
            return {'verified': 'yes', 'result': json.dumps(data, ensure_ascii=False)}
        application = data.get('application')
        if status != 'application_created' or not isinstance(application, dict):
            return failed
        if not application.get('id') or application.get('order_id') != order_id or application.get('status') != 'created':
            return failed
        if not any(isinstance(e, dict) and e.get('step') == 'return_verify' and e.get('success') == 1
                   and isinstance(e.get('detail'), dict) and e['detail'].get('id') == application['id']
                   and e['detail'].get('status') == 'created' for e in data.get('trace', [])):
            return failed
        return {'verified': 'yes', 'result': json.dumps(data, ensure_ascii=False)}
    except (ValueError, TypeError, AttributeError):
        return failed
