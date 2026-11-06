"""Owned schema29 catalog and random disposable Windows credential targets."""
from contextlib import closing
import ctypes
from ctypes import wintypes
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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

class Credential(ctypes.Structure):
    _fields_ = [('Flags',wintypes.DWORD),('Type',wintypes.DWORD),('TargetName',wintypes.LPWSTR),('Comment',wintypes.LPWSTR),('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),('CredentialBlob',ctypes.POINTER(ctypes.c_ubyte)),('Persist',wintypes.DWORD),('AttributeCount',wintypes.DWORD),('Attributes',ctypes.c_void_p),('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]

class Catalog(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    requests=[]
    def log_message(self,*args): pass
    def do_GET(self):
        self.requests.append((self.path,dict(self.headers)))
        scenario=self.path.split('/')[1]
        if scenario=='stall': time.sleep(12)
        status=int(scenario) if scenario.isdigit() else 200
        data=[{'id':'model-a'},{'id':'model-b'},{'id':'模型-😀'},{'id':'model-a'},{'id':'invalid model'},{'id':'invalid\u2003model'},{'id':'invalid\u0085model'},{'id':3}]
        if scenario=='empty': data=[]
        if scenario=='many': data=[{'id':f'model-{i}'} for i in range(260)]
        raw=json.dumps({'data':data,'has_more':scenario=='paged'},ensure_ascii=False).encode()
        if scenario=='invalid': raw=b'{broken'
        if scenario=='shape': raw=b'{"data":{}}'
        if scenario=='large': raw=b'x'*1048577
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        if status==302: self.send_header('Location','/should-never-follow/models')
        if scenario=='chunked': self.send_header('Transfer-Encoding','chunked')
        else: self.send_header('Content-Length',str(len(raw)))
        self.end_headers()
        try:
            if scenario=='chunked':
                for offset in range(0,len(raw),3):
                    part=raw[offset:offset+3]
                    self.wfile.write(f'{len(part):x}\r\n'.encode()+part+b'\r\n'); self.wfile.flush()
                self.wfile.write(b'0\r\n\r\n')
            else: self.wfile.write(raw)
        except (ConnectionError,OSError): pass

def main():
    image = Path(sys.argv[1]).resolve(strict=True)
    evidence_path = Path(sys.argv[2]).resolve()
    root = Path(tempfile.mkdtemp(prefix='sencode-config-')).resolve()
    database = root / '目录😀' / 'state.sqlite3'
    database.parent.mkdir()
    identifier = 'custom-switch-' + uuid.uuid4().hex
    target = 'Sencode/connection/' + identifier
    checks = []
    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),Catalog)
    worker=threading.Thread(target=server.serve_forever,daemon=True); worker.start()
    advapi.CredReadW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))]
    advapi.CredFree.argtypes = [ctypes.c_void_p]
    def secret():
        pointer = ctypes.POINTER(Credential)()
        if not advapi.CredReadW(target,1,0,ctypes.byref(pointer)): return None
        try: return ctypes.string_at(pointer.contents.CredentialBlob,pointer.contents.CredentialBlobSize).decode('utf-8')
        finally: advapi.CredFree(pointer)
    def call(action, ok=True, **args):
        raw=json.dumps(dict(action=action,database=str(database),**args),ensure_ascii=False)+'\n'
        result=subprocess.run([str(image)],input=raw,text=True,encoding='utf-8',capture_output=True,timeout=30)
        assert 'owned-key-' not in result.stdout and 'owned-key-' not in result.stderr
        data=json.loads(result.stdout)
        assert data['ok'] == ok, (action,data,result.returncode)
        assert (result.returncode==0)==ok
        return data.get('data',data)
    def edit_db(sql,*args):
        with closing(sqlite3.connect(database)) as db:
            db.create_function('sengoo_context',1,lambda _:'owned-switch-test')
            db.execute(sql,args);db.commit()
    evidence={'result':'failed','scope':'owned temporary SQLite/Windows Credential Manager and loopback HTTP; no live provider API requests','bridge_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'checks':checks}
    try:
        assert call('snapshot')['connections']==[]
        checks.append('empty catalog and Unicode database path')
        entry=lambda id,vision=False:dict(id=id,label=None,capabilities=dict(visionSupported=vision))
        profile=dict(id=identifier,name='我的 API 😀',base_url='https://api.example.invalid/v1',protocol='responses',model='model-a',api_key='owned-key-first',existing=False,enabled_models=[entry('model-a')],discovered_model_ids=['model-a','model-b','model-c'])
        data=call('save',input=profile)
        assert len(data['connections'])==1 and data['connections'][0]['name']==profile['name']
        assert secret()=='owned-key-first'
        checks.append('create API and write only OS credential')
        assert call('select',id=identifier)['current']==identifier
        cli=Path('D:/SencodeCLI/bin/sen.exe')
        actual=subprocess.run([str(cli),'--database',str(database),'connections','list'],capture_output=True,text=True,encoding='utf-8',timeout=20)
        assert actual.returncode==0 and json.loads(actual.stdout)['current']==identifier
        checks.append('selection visible to real installed CLI')
        with closing(sqlite3.connect(database)) as db:
            raw=db.execute('SELECT config_json FROM connection_configs WHERE id=?',(identifier,)).fetchone()[0]
            assert 'owned-key-' not in raw
            conf=json.loads(raw);conf['extraFeature']={'preserved':True}
            conf['enabledModels'][0]['capabilities']['visionSupported']=True
            conf['enabledModels'][0]['capabilities']['futureCapability']=True
            conf['enabledModels'].append({'id':'model-b','capabilities':{'visionSupported':False}})
        edit_db('UPDATE connection_configs SET config_json=? WHERE id=?',json.dumps(conf),identifier)
        profile.update(existing=True,name='已编辑',api_key='',model='model-b',enabled_models=[entry('model-a',True),entry('model-b')])
        data=call('save',input=profile)
        assert secret()=='owned-key-first'
        assert data['connections'][0]['models']==['model-b','model-a']
        with closing(sqlite3.connect(database)) as db:
            saved=json.loads(db.execute('SELECT config_json FROM connection_configs WHERE id=?',(identifier,)).fetchone()[0])
        assert saved['extraFeature']['preserved'] and saved['enabledModels'][0]['capabilities']['visionSupported']
        assert saved['enabledModels'][0]['capabilities']['futureCapability']
        assert [m['id'] for m in saved['enabledModels']]==['model-a','model-b'] and saved['selectedModelId']=='model-b'
        assert saved['discoveredModelIds']==['model-a','model-b','model-c']
        checks.append('multi-model edit preserves blank key, capability metadata, candidates and unrelated fields')
        for changes in [dict(enabled_models=[]),dict(enabled_models=[entry('model-a')]),dict(enabled_models=[entry('model-b'),entry('model-b')]),dict(enabled_models=[entry('bad model')]),dict(discovered_model_ids=['bad\x00id']),dict(discovered_model_ids=['bad\u2003model']),dict(discovered_model_ids=['bad\u0085model'])]:
            call('save',ok=False,input={**profile,**changes})
        assert call('snapshot')['connections'][0]['model']=='model-b'
        checks.append('empty, duplicate, invalid and disabled-default catalogs refuse without mutation')
        before=json.dumps(call('snapshot'),sort_keys=True)
        base=f'http://127.0.0.1:{server.server_port}'
        for protocol in ['chatCompletions','responses','messages']:
            response=call('probe',input=dict(id=identifier,base_url=base+'/chunked',protocol=protocol,api_key='',existing=True))
            assert response==dict(model_ids=['model-a','model-b','模型-😀'],truncated=False),response
            path,headers=Catalog.requests[-1]
            assert path=='/chunked/models'
            if protocol=='messages': assert headers.get('x-api-key')=='owned-key-first' and headers.get('anthropic-version')=='2023-06-01' and 'Authorization' not in headers
            else: assert headers.get('Authorization')=='Bearer owned-key-first' and 'x-api-key' not in headers
        assert json.dumps(call('snapshot'),sort_keys=True)==before
        checks.append('three protocols use stored credentials; chunked Unicode discovery deduplicates without enabling or saving')
        probe=dict(id='custom-unsaved',base_url=base+'/many',protocol='responses',api_key='owned-key-probe',existing=False)
        response=call('probe',input=probe)
        assert response['truncated'] and len(response['model_ids'])==256
        response=call('probe',input={**probe,'base_url':base+'/paged'})
        assert response['truncated']
        checks.append('new unsaved key discovery is bounded to 256 and reports provider pagination')
        for scenario in ['401','403','404','429','500','302','invalid','shape','empty','large','stall']:
            call('probe',ok=False,input={**probe,'base_url':base+'/'+scenario})
        for changes in [dict(protocol='unknown'),dict(api_key=''),dict(api_key='x\r\ninject')]:
            call('probe',ok=False,input={**probe,**changes})
        assert not any(p.startswith('/should-never-follow') for p,_ in Catalog.requests)
        assert json.dumps(call('snapshot'),sort_keys=True)==before and secret()=='owned-key-first'
        checks.append('discovery rejects HTTP errors, redirect, malformed/oversized response, idle timeout and invalid credentials without changing config')
        call('save',ok=False,input={**profile,'existing':False,'api_key':'owned-key-conflict'})
        assert secret()=='owned-key-first'
        checks.append('duplicate creation does not overwrite')
        for changes in [dict(base_url='http://outside.invalid'),dict(base_url='https://user:pass@example.invalid'),dict(name='bad\x00name'),dict(model='bad\nmodel'),dict(protocol='unknown'),dict(api_key='bad\nsecret')]:
            call('save',ok=False,input={**profile,**changes})
        assert call('snapshot')['connections'][0]['name']=='已编辑'
        assert secret()=='owned-key-first'
        checks.append('invalid URL, NUL, newline and protocol refuse without mutation')
        edit_db("CREATE TRIGGER owned_abort BEFORE UPDATE ON connection_configs BEGIN SELECT RAISE(ABORT,'owned fixture'); END")
        call('save',ok=False,input={**profile,'api_key':'owned-key-rollback'})
        assert secret()=='owned-key-first'
        edit_db('DROP TRIGGER owned_abort')
        checks.append('failed DB update rolls credential back')
        account='account-'+uuid.uuid4().hex
        edit_db("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'codex','managed','Owned account','{}','account-model',1,1)",account)
        assert call('select',id=account)['current']==account
        call('remove',ok=False,id=account)
        call('save',ok=False,input={**profile,'id':account})
        checks.append('account selectable, editing and deletion refused')
        call('select',id=identifier)
        data=call('remove',id=identifier)
        assert data['current']=='' and secret() is None
        checks.append('delete clears selected default and owned credential')
        with closing(sqlite3.connect(database)) as db:
            assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0
        checks.append('configuration management creates no chat history')
        evidence['result']='passed'
        print(json.dumps(evidence,ensure_ascii=False))
    finally:
        server.shutdown(); server.server_close()
        advapi.CredDeleteW(target,1,0)
        evidence_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        for directory,_,files in os.walk(root,topdown=False,followlinks=False):
            current=Path(directory).resolve();assert current==root or root in current.parents
            for name in files: (current/name).unlink()
            current.rmdir()

if __name__=='__main__': main()
