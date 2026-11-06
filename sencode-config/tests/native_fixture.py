"""Manual native UI fixture: owned DB/credentials, loopback server, minimal PATH."""
from bridge_fixture import Catalog
from contextlib import closing
import ctypes
from http.server import ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

image=Path(sys.argv[1]).resolve(strict=True)
output=Path(sys.argv[2]).resolve(); output.parent.mkdir(parents=True,exist_ok=True)
root=Path(tempfile.mkdtemp(prefix='sencode-config-native-')).resolve()
database=root/'native.sqlite3'; stop=root/'stop'
server=ThreadingHTTPServer(('127.0.0.1',0),Catalog)
threading.Thread(target=server.serve_forever,daemon=True).start()
bridge=image.parent/'resources/sencode-config-bridge.exe'
ids=['custom-native-'+uuid.uuid4().hex for _ in range(2)]
evidence={'result':'pending','scope':'portable Windows UI with owned store/credentials and loopback, minimal runtime PATH; not fresh VM or live provider','app_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'bridge_sha256':hashlib.sha256(bridge.read_bytes()).hexdigest()}
app=None
def call(action,**args):
    response=subprocess.run([str(bridge)],input=json.dumps(dict(action=action,database=str(database),**args))+'\n',text=True,encoding='utf-8',capture_output=True,timeout=30)
    data=json.loads(response.stdout); assert data['ok'],data
    return data['data']
try:
    for index,identifier in enumerate(ids):
        call('save',input=dict(id=identifier,name=['验证 API','本地测试'][index],base_url=f'http://127.0.0.1:{server.server_port}/chunked',protocol='responses',model='model-a',api_key='owned-native-'+uuid.uuid4().hex,existing=False,enabled_models=[dict(id=id,label=None,capabilities=dict(visionSupported=False)) for id in ['model-a','model-b']],discovered_model_ids=['model-a','model-b']))
    call('select',id=ids[0])
    env=os.environ.copy(); env['SENCODE_CONFIG_DATABASE']=str(database)
    env['PATH']=os.environ['WINDIR']+'\\System32;'+os.environ['WINDIR']
    for key in ['SENGOO_CLANG','SENGOO_MODULE_MAP','CARGO_HOME','RUSTUP_HOME']: env.pop(key,None)
    app=subprocess.Popen([str(image)],cwd=root,env=env)
    print(json.dumps(dict(database=str(database),stop=str(stop),pid=app.pid),ensure_ascii=False),flush=True)
    deadline=time.monotonic()+1200
    while not stop.exists() and time.monotonic()<deadline and app.poll() is None: time.sleep(.5)
    snapshot=call('snapshot')
    expected=next(c for c in snapshot['connections'] if c['id']==ids[1])
    evidence['checks']={
        'native_selected_connection_committed':snapshot['current']==ids[1],
        'native_multi_model_saved':len(expected['enabled_models'])==3,
        'native_default_model_committed':expected['model']=='model-b',
        'native_image_capability_saved':next(m for m in expected['enabled_models'] if m['id']=='model-b')['capabilities']['visionSupported'],
        'native_probe_reached_loopback':any(p=='/chunked/models' for p,_ in Catalog.requests),
    }
    with closing(sqlite3.connect(database)) as db: evidence['checks']['no_chat_history_created']=db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0
    if stop.exists() and stop.read_text(encoding='utf-8-sig').strip().startswith('interrupted'):
        evidence['result']='interrupted'
        evidence['reason']='Manual user interaction changed the scripted fixture before its final assertions; these partial checks are not a passing gate.'
    else: evidence['result']='passed' if all(evidence['checks'].values()) else 'failed'
    print(json.dumps(evidence,ensure_ascii=False),flush=True)
finally:
    if app is not None and app.poll() is None: app.terminate(); app.wait(timeout=10)
    server.shutdown();server.server_close()
    for identifier in ids: ctypes.windll.advapi32.CredDeleteW('Sencode/connection/'+identifier,1,0)
    output.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    for directory,_,files in os.walk(root,topdown=False,followlinks=False):
        current=Path(directory).resolve(); assert current==root or root in current.parents
        for name in files: (current/name).unlink()
        current.rmdir()
if evidence['result']=='failed': sys.exit(1)
