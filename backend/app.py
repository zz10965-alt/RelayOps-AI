"""RelayOps synthetic business API; no model simulation in runtime paths."""
import asyncio
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import time
from collections import deque
from contextlib import asynccontextmanager, contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import httpx
from fastapi import BackgroundTasks, FastAPI, File, Form, Header, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

POLICY = {"id": "damage-30-v1", "return_window_days": 30, "min_confidence": 0.8,
          "text": "签收后30天内，商品匹配且清晰照片显示损坏，可创建退货申请；不代表批准或退款。"}
DB = os.getenv("RELAYOPS_DB", ".data/relayops.sqlite3")
MAX_IMAGE = 5 * 1024 * 1024


@contextmanager
def db():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    with db() as con:
        con.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, product TEXT NOT NULL,
          status TEXT NOT NULL, delivered_on TEXT);
        CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
          sku TEXT NOT NULL, returnable INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, order_id TEXT NOT NULL,
          description TEXT NOT NULL, status TEXT NOT NULL, reason TEXT, analysis TEXT,
          return_id TEXT, created REAL NOT NULL, finished REAL, execution_token TEXT,
          run_id TEXT, cost REAL, currency TEXT);
        CREATE TABLE IF NOT EXISTS returns(id TEXT PRIMARY KEY, order_id TEXT NOT NULL UNIQUE,
          status TEXT NOT NULL CHECK(status IN ('created','approved','completed')), created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, case_id TEXT NOT NULL,
          step TEXT NOT NULL, success INTEGER NOT NULL, valid INTEGER, detail TEXT NOT NULL,
          duration_ms REAL NOT NULL, created REAL NOT NULL);
        ''')
        con.executemany('INSERT OR IGNORE INTO products VALUES(?,?,?,?)', [('CUP-WHITE','白色陶瓷杯','CUP-W-001',1), ('VASE-BLUE','蓝色玻璃花瓶','VASE-B-001',1)])
        for ident, product, status, days in [
            ('DEMO-1001', '白色陶瓷杯', 'delivered', 3),
            ('DEMO-1002', '蓝色玻璃花瓶', 'delivered', 45),
            ('DEMO-1003', '白色陶瓷杯', 'shipping', None),
        ]:
            con.execute('INSERT OR IGNORE INTO orders VALUES (?,?,?,?)',
                        (ident, product, status, (date.today()-timedelta(days=days)).isoformat() if days is not None else None))
        con.execute("UPDATE cases SET status='handoff',reason='服务重启：上次执行中断，请人工核查',finished=?,execution_token=NULL WHERE status IN ('queued','running')", (time.time(),))


def valid_https_origin(value):
    try:
        parsed = urlsplit(value)
        return bool(parsed.scheme == 'https' and parsed.hostname and parsed.port != 0
                    and not parsed.username and not parsed.password and not parsed.query
                    and not parsed.fragment and parsed.path == '' and '*' not in value)
    except ValueError:
        return False


@asynccontextmanager
async def lifespan(app):
    if os.getenv('RELAYOPS_PUBLIC_DEMO') == '1':
        if not os.getenv('RELAYOPS_DEMO_TOKEN') or len(os.environ['RELAYOPS_DEMO_TOKEN']) < 32:
            raise RuntimeError('Public demo requires a private operator token of at least 32 characters')
        if not Path(DB).is_absolute() or not Path(DB).resolve().is_relative_to(Path('/data').resolve()):
            raise RuntimeError('Public demo requires RELAYOPS_DB under /data/')
        configured_origins = os.getenv('RELAYOPS_CORS_ORIGINS', '').split(',')
        if not all(valid_https_origin(x.strip()) for x in configured_origins):
            raise RuntimeError('Public demo requires explicit HTTPS frontend origins')
    if os.getenv('RELAYOPS_PUBLIC_DEMO') == '1' and os.getenv('DIFY_TOOL_TOKEN'):
        if len(os.environ['DIFY_TOOL_TOKEN']) < 32 or os.environ['DIFY_TOOL_TOKEN'] == os.environ['RELAYOPS_DEMO_TOKEN']:
            raise RuntimeError('Public demo requires a distinct tool token of at least 32 characters')
    if os.getenv('DIFY_BASE_URL'):
        base = urlsplit(os.environ['DIFY_BASE_URL'])
        if base.scheme != 'https' or not base.hostname or base.username or base.query or base.fragment:
            raise RuntimeError('DIFY_BASE_URL must be an HTTPS API URL without credentials or query')
        if not os.getenv('DIFY_API_KEY') or not os.getenv('DIFY_TOOL_TOKEN'):
            raise RuntimeError('Dify configuration incomplete')
    init_db()
    yield


app = FastAPI(title="RelayOps AI — Synthetic Operations API", lifespan=lifespan)


origins = [x.strip() for x in os.getenv('RELAYOPS_CORS_ORIGINS', '').split(',') if x.strip()]
submission_times = deque()


@app.middleware('http')
async def demo_guard(request: Request, call_next):
    path = request.url.path
    if os.getenv('RELAYOPS_PUBLIC_DEMO') == '1' and path != '/api/health' and request.method != 'OPTIONS':
        expected = os.getenv('DIFY_TOOL_TOKEN', '') if path.startswith('/api/tools/') or path.startswith('/api/orders/') or path.startswith('/api/products/') or path == '/api/policy' or path.startswith('/api/returns/') else os.getenv('RELAYOPS_DEMO_TOKEN', '')
        if not expected or not hmac.compare_digest(request.headers.get('authorization', '').encode(), ('Bearer ' + expected).encode()):
            return JSONResponse({'detail': 'Operator authentication required'}, status_code=401)
    if os.getenv('RELAYOPS_PUBLIC_DEMO') == '1' and path == '/api/cases' and request.method == 'POST' and os.getenv('RELAYOPS_ALLOW_MODEL_EXECUTION') != '1':
        return JSONResponse({'detail': 'Public case execution disabled; owner approval required'}, status_code=403)
    if request.method == 'POST' and path in ('/api/cases', '/api/demo/orders'):
        now = time.monotonic()
        while submission_times and submission_times[0] < now - 60:
            submission_times.popleft()
        if os.getenv('RELAYOPS_PUBLIC_DEMO') == '1':
            if len(submission_times) >= 10:
                return JSONResponse({'detail': 'Demo request limit; retry after one minute'}, status_code=429)
            submission_times.append(now)
    return await call_next(request)


class BodyLimitMiddleware:
    """Bound both declared and streamed bodies before multipart/JSON parsing."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or not scope['path'].startswith('/api/'):
            return await self.app(scope, receive, send)
        headers = dict(scope['headers'])
        try:
            length = int(headers.get(b'content-length', b'0'))
            if length < 0:
                raise ValueError()
        except ValueError:
            return await JSONResponse({'detail': 'Invalid request length'}, status_code=400)(scope, receive, send)
        limit = MAX_IMAGE + 65536
        if length > limit:
            return await JSONResponse({'detail': 'Request too large'}, status_code=413)(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            body = message.get('body', b'')
            size += len(body)
            if size > limit:
                return await JSONResponse({'detail': 'Request too large'}, status_code=413)(scope, receive, send)
            chunks.append(body)
            if not message.get('more_body', False):
                break
        sent = False
        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {'type': 'http.request', 'body': b''.join(chunks), 'more_body': False}
            return await receive()
        await self.app(scope, replay, send)


app.add_middleware(BodyLimitMiddleware)
# CORS must wrap guards so browser clients can read 401/403/413/429 errors.
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST'],
                   allow_headers=['Authorization', 'Content-Type'])


class DemoOrder(BaseModel):
    scenario: Literal['eligible', 'expired', 'shipping'] = 'eligible'


@app.post('/api/demo/orders', status_code=201)
def fresh_order(body: DemoOrder):
    ident = 'DEMO-' + secrets.token_hex(8).upper()
    days = 45 if body.scenario == 'expired' else 3
    with db() as con:
        con.execute('INSERT INTO orders VALUES(?,?,?,?)',
                    (ident, '白色陶瓷杯', 'shipping' if body.scenario == 'shipping' else 'delivered',
                     None if body.scenario == 'shipping' else (date.today()-timedelta(days=days)).isoformat()))
    return order(ident)


def execution_stages(trace):
    groups = [('Understand', ('analysis',)), ('Retrieve', ('order_lookup', 'policy_lookup')),
              ('Decide', ('resolve',)), ('Act', ('return_create',)), ('Verify', ('return_verify',))]
    stages = []
    for name, steps in groups:
        events = [e for e in trace if e['step'] in steps]
        status = 'not_observed'
        if events:
            status = 'recorded' if name == 'Decide' else 'succeeded'
            if name == 'Retrieve' and not all(any(e['step'] == step for e in events) for step in steps):
                status = 'partial'
            if any(not e['success'] for e in events):
                status = 'failed'
            elif name == 'Decide' and any(e['detail'].get('decision') == 'handoff' for e in events):
                status = 'handoff'
        descriptions = [str(e['detail'].get('reason') or e['detail'].get('summary') or e['detail'].get('error') or e['detail'].get('product') or e['detail'].get('status') or e['detail'].get('return_id') or e['step']) for e in events]
        stages.append({'name': name, 'status': status, 'summary': ' · '.join(descriptions), 'events': events})
    return stages


def event(case_id, step, success, detail, duration_ms=0, valid=None):
    with db() as con:
        con.execute('INSERT INTO events(case_id,step,success,valid,detail,duration_ms,created) VALUES(?,?,?,?,?,?,?)',
                    (case_id, step, int(success), None if valid is None else int(valid), json.dumps(detail, ensure_ascii=False), duration_ms, time.time()))


def finish(case_id, status, reason):
    with db() as con:
        con.execute("UPDATE cases SET status=?,reason=?,finished=? WHERE id=? AND status IN ('queued','running')",
                    (status, reason, time.time(), case_id))


def get_case(case_id):
    with db() as con:
        row = con.execute('SELECT * FROM cases WHERE id=?', (case_id,)).fetchone()
        if not row:
            raise HTTPException(404, '案件不存在')
        result = dict(row)
        result.pop('execution_token', None)
        result['analysis'] = json.loads(result['analysis']) if result['analysis'] else None
        result['order'] = dict(r) if (r := con.execute('SELECT * FROM orders WHERE id=?', (row['order_id'],)).fetchone()) else None
        result['application'] = dict(r) if row['return_id'] and (r := con.execute('SELECT * FROM returns WHERE id=?', (row['return_id'],)).fetchone()) else None
        result['trace'] = [dict(r) for r in con.execute('SELECT * FROM events WHERE case_id=? ORDER BY id', (case_id,))]
        for item in result['trace']:
            item['detail'] = json.loads(item['detail'])
        result['stages'] = execution_stages(result['trace'])
        result['policy'] = POLICY
        return result


class Analysis(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    order_id: str = Field(min_length=1, max_length=80)
    damaged: bool
    product_match: bool
    image_quality: Literal['clear', 'blurry', 'unrelated']
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=1000)


class Resolve(BaseModel):
    model_config = ConfigDict(extra='forbid')
    case_id: str = Field(max_length=80)
    execution_token: str = Field(max_length=128)
    analysis: str = Field(max_length=6000)


@app.get('/api/health')
def health():
    with db() as con:
        con.execute('SELECT 1').fetchone()
    return {'status': 'ok', 'synthetic': True,
            'public_demo': os.getenv('RELAYOPS_PUBLIC_DEMO') == '1',
            'execution_enabled': os.getenv('RELAYOPS_PUBLIC_DEMO') != '1' or os.getenv('RELAYOPS_ALLOW_MODEL_EXECUTION') == '1',
            'dify_configured': bool(os.getenv('DIFY_BASE_URL') and os.getenv('DIFY_API_KEY') and os.getenv('DIFY_TOOL_TOKEN'))}


@app.get('/api/policy')
def policy():
    return POLICY


@app.get('/api/orders/{order_id}')
def order(order_id: str):
    with db() as con:
        row = con.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
    if not row:
        raise HTTPException(404, '订单不存在')
    result = dict(row)
    with db() as con:
        product = con.execute('SELECT * FROM products WHERE name=?', (row['product'],)).fetchone()
    result['product_info'] = dict(product) if product else None
    return result


@app.get('/api/products/{product_id}')
def product(product_id: str):
    with db() as con:
        row = con.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
    if not row:
        raise HTTPException(404, '商品不存在')
    return dict(row)


@app.get('/api/returns/{return_id}')
def application(return_id: str):
    with db() as con:
        row = con.execute('SELECT * FROM returns WHERE id=?', (return_id,)).fetchone()
    if not row:
        raise HTTPException(404, '申请不存在')
    return dict(row)


@app.get('/api/cases')
def cases():
    with db() as con:
        return [dict(r) for r in con.execute('SELECT id,order_id,status,reason,created,finished FROM cases ORDER BY created DESC LIMIT 200')]


@app.get('/api/cases/{case_id}')
def case(case_id: str):
    return get_case(case_id)


# Single-process demo: serialize short synchronous callback transactions; no await inside resolve.
@app.post('/api/tools/resolve')
async def resolve_endpoint(body: Resolve, authorization: str | None = Header(default=None)):
    return resolve(body, authorization)


def resolve(body: Resolve, authorization: str | None = Header(default=None)):
    tool_token = os.getenv('DIFY_TOOL_TOKEN', '')
    if not tool_token or not hmac.compare_digest((authorization or '').encode(), ('Bearer ' + tool_token).encode()):
        raise HTTPException(401, '工具鉴权失败')
    with db() as con:
        row = con.execute('SELECT * FROM cases WHERE id=?', (body.case_id,)).fetchone()
    if not row:
        raise HTTPException(404, '案件不存在')
    if not row['execution_token'] or not hmac.compare_digest(row['execution_token'].encode(), body.execution_token.encode()):
        raise HTTPException(401, '案件执行凭据无效')
    if row['status'] not in ('running', 'application_created', 'handoff'):
        raise HTTPException(409, '案件未处于可执行状态')
    if row['status'] != 'running':
        return get_case(body.case_id)
    started = time.monotonic()
    try:
        analysis = Analysis.model_validate_json(body.analysis)
    except ValidationError:
        event(body.case_id, 'resolve', False, {'error': '模型输出不符合结构要求'}, valid=False)
        finish(body.case_id, 'handoff', '模型结构化输出无效')
        return get_case(body.case_id)
    with db() as con:
        con.execute('UPDATE cases SET analysis=? WHERE id=?', (analysis.model_dump_json(), body.case_id))
    event(body.case_id, 'analysis', True, analysis.model_dump())
    try:
        facts = order(row['order_id'])
    except HTTPException:
        event(body.case_id, 'order_lookup', False, {'order_id': row['order_id'], 'error': '订单不存在'})
        event(body.case_id, 'resolve', False, {'outcome': 'order_missing'}, valid=True)
        finish(body.case_id, 'handoff', '订单不存在')
        return get_case(body.case_id)
    event(body.case_id, 'order_lookup', True, facts)
    event(body.case_id, 'policy_lookup', True, POLICY)
    reason = None
    if analysis.order_id != row['order_id']:
        reason = '提取订单号与提交订单号冲突'
    elif analysis.image_quality != 'clear':
        reason = '图片模糊或无关，请人工检查并补充清晰商品照片'
    elif not analysis.product_match or not analysis.damaged or analysis.confidence < POLICY['min_confidence']:
        reason = '商品不匹配、损坏证据不足或模型置信度不足'
    elif not facts['product_info'] or not facts['product_info']['returnable']:
        reason = '商品不支持自动退货，需人工处理'
    elif facts['status'] != 'delivered' or not facts['delivered_on']:
        reason = '订单未签收，需人工处理'
    elif not 0 <= (date.today()-date.fromisoformat(facts['delivered_on'])).days <= POLICY['return_window_days']:
        reason = '不符合30天售后政策'
    if reason:
        event(body.case_id, 'resolve', True, {'decision': 'handoff', 'reason': reason}, valid=True)
        finish(body.case_id, 'handoff', reason)
        return get_case(body.case_id)
    try:
        with db() as con:
            # Unique order_id prevents duplicate side effects across cases and retries.
            con.execute('INSERT OR IGNORE INTO returns VALUES(?,?,?,?)',
                        (secrets.token_hex(12), row['order_id'], 'created', time.time()))
            created = dict(con.execute('SELECT * FROM returns WHERE order_id=?', (row['order_id'],)).fetchone())
        event(body.case_id, 'return_create', True, created)
        verified = application(created['id'])  # Independent DB connection/read after commit.
        if verified['order_id'] != row['order_id'] or verified['status'] != 'created':
            raise RuntimeError('业务状态无法验证')
        event(body.case_id, 'return_verify', True, verified)
        with db() as con:
            con.execute("UPDATE cases SET status='application_created',return_id=?,reason=?,finished=? WHERE id=? AND status='running'",
                        (verified['id'], '申请已创建并回读验证；尚未批准或完成退款/退货', time.time(), body.case_id))
        event(body.case_id, 'resolve', True, {'return_id': verified['id']}, (time.monotonic()-started)*1000, valid=True)
    except (sqlite3.Error, RuntimeError, HTTPException):
        event(body.case_id, 'resolve', False, {'error': '业务写入或回读失败，需人工核查'}, valid=True)
        finish(body.case_id, 'handoff', '业务 API 失败，需核查是否已创建申请')
    return get_case(body.case_id)


async def dify_request(client, case_id, path, **kwargs):
    # Only retry read-like workflow execution at HTTP transport/status boundaries;
    # business side effects remain idempotent via order uniqueness + case state.
    for attempt in range(2):
        start = time.monotonic()
        try:
            response = await client.post(path, **kwargs)
            response.raise_for_status()
            event(case_id, path, True, {'attempt': attempt + 1, 'http_status': response.status_code}, (time.monotonic()-start)*1000)
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            event(case_id, path, False, {'attempt': attempt + 1, 'error_type': type(exc).__name__, 'http_status': exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None}, (time.monotonic()-start)*1000)
            retryable = isinstance(exc, httpx.TransportError) or (isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500)
            if attempt or not retryable:
                raise
            await asyncio.sleep(0.1)


async def run_workflow(case_id, image, filename, mime):
    if not health()['dify_configured']:
        event(case_id, 'configuration', False, {'error': 'Dify 未配置；未运行模型'})
        finish(case_id, 'handoff', 'Dify 未配置，未执行视觉分析')
        return
    token = secrets.token_urlsafe(32)
    with db() as con:
        con.execute("UPDATE cases SET status='running',execution_token=? WHERE id=? AND status='queued'", (token, case_id))
    row = get_case(case_id)
    try:
        async with httpx.AsyncClient(base_url=os.environ['DIFY_BASE_URL'].rstrip('/')+'/',
                                     headers={'Authorization': 'Bearer '+os.environ['DIFY_API_KEY']},
                                     timeout=httpx.Timeout(90, connect=10), follow_redirects=False) as client:
            uploaded = await dify_request(client, case_id, 'files/upload',
                                         data={'user': case_id}, files={'file': (filename, image, mime)})
            if not isinstance(uploaded, dict) or not isinstance(uploaded.get('id'), str) or not uploaded['id']:
                raise ValueError('Dify 上传响应缺少有效文件ID')
            result = await dify_request(client, case_id, 'workflows/run', json={
                'inputs': {'case_id': case_id, 'execution_token': token, 'order_id': row['order_id'],
                           'description': row['description'], 'image': {'type': 'image', 'transfer_method': 'local_file', 'upload_file_id': uploaded['id']}},
                'response_mode': 'blocking', 'user': case_id})
            if not isinstance(result, dict) or not isinstance(result.get('data'), dict):
                raise ValueError('Dify运行响应不符合协议')
            data = result['data']
            run_id = result.get('workflow_run_id') or data.get('id')
            if run_id is not None and (not isinstance(run_id, str) or not run_id or len(run_id) > 256):
                raise ValueError('Dify运行ID无效')
            with db() as con:
                con.execute('UPDATE cases SET run_id=? WHERE id=?', (run_id, case_id))
                # Do not invent pricing; store only explicit nonnegative actual metadata.
                metadata = data.get('metadata') or {}
                if not isinstance(metadata, dict):
                    raise ValueError('Dify费用元数据无效')
                price = metadata.get('total_price')
                currency = metadata.get('currency')
                if price is not None and currency:
                    value = float(price)
                    if 0 <= value < float('inf'):
                        con.execute('UPDATE cases SET cost=?,currency=? WHERE id=?', (value, str(currency)[:16], case_id))
            if data.get('status') != 'succeeded':
                raise RuntimeError('Dify Workflow 未成功')
            current = get_case(case_id)
            if current['status'] == 'running':
                outputs = data.get('outputs')
                raw = outputs.get('result') if isinstance(outputs, dict) else None
                try:
                    outcome = json.loads(raw) if isinstance(raw, str) else None
                except (ValueError, TypeError):
                    outcome = None
                if isinstance(outcome, dict) and outcome.get('status') == 'handoff':
                    reason = 'Workflow requested human review; no backend action verified'
                    if outcome.get('requested_action') == 'provide_clear_photo':
                        reason = 'Please supply a clear product photo; workflow requested human review'
                    event(case_id, 'workflow_handoff', True, {'reason': reason})
                    finish(case_id, 'handoff', reason)
                    current = get_case(case_id)
            if current['status'] not in ('application_created', 'handoff'):
                raise RuntimeError('Workflow 未产生经工具核验的结果')
            event(case_id, 'workflow', True, {'run_id': current['run_id'], 'status': data['status']})
    except (httpx.HTTPError, ValueError, KeyError, TypeError, RuntimeError):
        event(case_id, 'workflow', False, {'error': 'Dify 调用失败或返回结果不符合协议；检查服务端配置与工作流运行日志'})
        finish(case_id, 'handoff', 'Dify 执行失败或未调用核验工具，请人工核查')
    finally:
        with db() as con:
            con.execute('UPDATE cases SET execution_token=NULL WHERE id=?', (case_id,))


@app.post('/api/cases', status_code=202)
async def create_case(background: BackgroundTasks,
                      order_id: str = Form(min_length=1, max_length=80),
                      description: str = Form(default='', max_length=4000),
                      image: UploadFile | None = File(default=None)):
    order_id, description = order_id.strip(), description.strip()
    if not order_id:
        raise HTTPException(422, '订单号不能为空')
    content, mime = b'', None
    if image and image.filename:
        content = await image.read(MAX_IMAGE+1)
        if len(content) > MAX_IMAGE:
            raise HTTPException(413, '图片最大5MiB')
        try:
            with Image.open(io.BytesIO(content)) as pic:
                if pic.format not in ('PNG', 'JPEG', 'WEBP') or pic.width*pic.height > 20_000_000:
                    raise ValueError('不支持图片格式或尺寸')
                mime = Image.MIME[pic.format]
                pic.verify()
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            raise HTTPException(422, '请上传有效 PNG/JPEG/WebP 图片（不超过2000万像素）')
    case_id = secrets.token_hex(12)
    missing = [name for name, value in [('问题描述', description), ('商品照片', content)] if not value]
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        if os.getenv('RELAYOPS_PUBLIC_DEMO') == '1' and con.execute("SELECT count(*) FROM cases WHERE status IN ('queued','running')").fetchone()[0] >= 2:
            raise HTTPException(429, 'Demo concurrency limit; retry later')
        con.execute('INSERT INTO cases(id,order_id,description,status,reason,created,finished) VALUES(?,?,?,?,?,?,?)',
                    (case_id, order_id, description, 'needs_information' if missing else 'queued',
                     '请补充：'+'、'.join(missing) if missing else None, time.time(), time.time() if missing else None))
    event(case_id, 'submission', True, {'order_id': order_id, 'missing': missing, 'image_sha256': hashlib.sha256(content).hexdigest() if content else None})
    if not missing:
        background.add_task(run_workflow, case_id, content, 'evidence'+{ 'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'}[mime], mime)
    return {'id': case_id, 'status': 'needs_information' if missing else 'queued'}


@app.get('/api/metrics')
def metrics():
    with db() as con:
        rows = [dict(r) for r in con.execute('SELECT * FROM cases')]
        unique_applications = con.execute('SELECT count(*) FROM returns').fetchone()[0]
        tools = [dict(r) for r in con.execute("SELECT * FROM events WHERE step='resolve'")]
        requests = [dict(r) for r in con.execute("SELECT * FROM events WHERE step IN ('files/upload','workflows/run')")]
    total = len(rows)
    terminal = [r for r in rows if r['finished'] is not None]
    completed = sum(r['status'] == 'application_created' for r in rows)
    ratio = lambda a, b: a/b if b else None
    retried = {r['case_id'] for r in requests if json.loads(r['detail']).get('attempt') == 2}
    recovered = {r['id'] for r in rows if r['id'] in retried and r['status'] == 'application_created'}
    priced = [r for r in rows if r['cost'] is not None]
    return {'synthetic': True, 'total_cases': total, 'terminal_cases': len(terminal), 'created_applications': unique_applications, 'completed_cases': completed,
            'completion_rate': ratio(completed, total), 'automation_rate': ratio(completed, len(terminal)),
            'tool_calls': len(tools), 'tool_success_rate': ratio(sum(r['success'] for r in tools), len(tools)),
            'parameter_accuracy': ratio(sum(r['valid'] == 1 for r in tools), len(tools)),
            'average_duration_seconds': ratio(sum(r['finished']-r['created'] for r in terminal), len(terminal)),
            'handoff_rate': ratio(sum(r['status'] == 'handoff' for r in rows), len(terminal)),
            'retried_cases': len(retried), 'recovered_cases': len(recovered), 'recovery_rate': ratio(len(recovered), len(retried)),
            'priced_cases': len(priced), 'average_api_cost': ratio(sum(r['cost'] for r in priced), len(priced)) if len({r['currency'] for r in priced}) <= 1 else None,
            'currency': priced[0]['currency'] if priced and len({r['currency'] for r in priced}) == 1 else None,
            'cost_note': '仅统计Dify明确返回的费用；未知为null，不含模拟业务API本地资源成本'}


DIST = Path(__file__).resolve().parents[1] / 'web' / 'dist'
if DIST.exists():
    app.mount('/assets', StaticFiles(directory=DIST/'assets'), name='assets')

    @app.get('/')
    def index():
        return FileResponse(DIST/'index.html')
