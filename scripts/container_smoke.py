"""Local-only container smoke with a disposable volume; publishes no ports."""
import json
import secrets
import subprocess
import time

name='relayops-smoke-'+secrets.token_hex(4)
volume=name+'-data'
token=secrets.token_urlsafe(32)
def docker(*args):
    return subprocess.check_output(['docker',*args],text=True,stderr=subprocess.PIPE).strip()
def request(path, method='GET', data=None, auth=False):
    code='''import urllib.request,urllib.error,json,os
r=urllib.request.Request('http://127.0.0.1:8123'+%r,method=%r,data=%r,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+os.environ['RELAYOPS_DEMO_TOKEN']} if %r else {})})
try:
 with urllib.request.urlopen(r) as response: print(json.dumps([response.status,json.load(response)]))
except urllib.error.HTTPError as e: print(json.dumps([e.code,json.load(e)]))
''' % (path,method,data,auth)
    return json.loads(docker('exec',name,'python','-c',code))
def ready():
    for _ in range(30):
        try:
            if request('/api/health')[0]==200: return
        except (subprocess.CalledProcessError,ValueError): pass
        time.sleep(.2)
    raise RuntimeError('Container not ready')
try:
    docker('volume','create',volume)
    docker('run','-d','--name',name,'--mount','type=volume,src='+volume+',dst=/data',
           '-e','PORT=8123','-e','RELAYOPS_DEMO_TOKEN='+token,
           '-e','RELAYOPS_CORS_ORIGINS=https://frontend.example','relayops-module1:local')
    ready()
    cors = docker('exec',name,'python','-c',"import urllib.request; r=urllib.request.Request('http://127.0.0.1:8123/api/cases',method='OPTIONS',headers={'Origin':'https://frontend.example','Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization'}); response=urllib.request.urlopen(r); assert response.headers['access-control-allow-origin']=='https://frontend.example'; print('CORS verified')")
    assert cors == 'CORS verified'
    cors_error = docker('exec',name,'python','-c',"import urllib.request,urllib.error; r=urllib.request.Request('http://127.0.0.1:8123/api/cases',headers={'Origin':'https://frontend.example'});\ntry: urllib.request.urlopen(r)\nexcept urllib.error.HTTPError as e: assert e.code==401 and e.headers['access-control-allow-origin']=='https://frontend.example'; print('error CORS verified')")
    assert cors_error == 'error CORS verified'
    assert request('/api/cases')[0]==401
    assert request('/api/cases','POST',b'{}',True)[0]==403
    status,order=request('/api/demo/orders','POST',b'{"scenario":"eligible"}',True)
    assert status==201
    docker('restart',name)
    ready()
    # Operator detail route does not expose tool-only facts; use DB read-only verification.
    code="import sqlite3; c=sqlite3.connect('file:/data/relayops.sqlite3?mode=ro',uri=True); assert c.execute('SELECT count(*) FROM orders WHERE id=?',(%r,)).fetchone()[0]==1; print('persisted')" % order['id']
    assert docker('exec',name,'python','-c',code)=='persisted'
    print('Container PASS: PORT=8123, health, HTTPS-origin CORS, unauthorized 401, default execution 403, fresh order, /data persistence after restart. No ports published.')
finally:
    subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(['docker','volume','rm',volume],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
