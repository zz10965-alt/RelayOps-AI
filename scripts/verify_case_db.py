"""Read-only independent SQLite verification after a real run; never mutates DB."""
import argparse
import json
import sqlite3
from pathlib import Path


def verify(path,case_id):
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True) as con:
        con.row_factory=sqlite3.Row
        case=con.execute('SELECT id,order_id,status,return_id,run_id FROM cases WHERE id=?',(case_id,)).fetchone()
        if not case or case['status']!='application_created' or not case['run_id']:
            raise ValueError('Missing verified created case or real workflow run id')
        row=con.execute('SELECT id,order_id,status FROM returns WHERE id=?',(case['return_id'],)).fetchone()
        if not row or row['order_id']!=case['order_id'] or row['status']!='created':
            raise ValueError('Application database state does not match')
        events=con.execute('SELECT step,success,detail FROM events WHERE case_id=?',(case_id,)).fetchall()
        for step in ('return_create','return_verify','workflow'):
            matches = [json.loads(e['detail']) for e in events if e['step']==step and e['success']]
            if step == 'workflow':
                valid = any(e.get('run_id') == case['run_id'] and e.get('status') == 'succeeded' for e in matches)
            else:
                valid = any(e.get('id') == row['id'] and e.get('order_id') == case['order_id'] and e.get('status') == 'created' for e in matches)
            if not valid: raise ValueError('Missing matching successful '+step)
        return dict(row)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',default='.data/relayops.sqlite3')
    parser.add_argument('--case',required=True)
    args=parser.parse_args()
    try: result=verify(args.db,args.case)
    except (sqlite3.Error,ValueError) as exc: raise SystemExit('FAIL: '+str(exc))
    print(json.dumps({'verification':'SQLite read-only PASS','application':result,'note':'created only; not approved or refunded'},ensure_ascii=False))
