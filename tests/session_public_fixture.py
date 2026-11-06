"""Final CLI session gate in an isolated profile and owned hidden console Job.

Calls only a synthetic loopback provider and a unique fixture credential. SQL
seeds old/empty/child records; title, rename, branch, resume and host entrypoints
run through the actual product executable, never a substitute native probe.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import ctypes
from ctypes import wintypes
import hashlib
import http.server
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import threading
import time
import traceback
import uuid

import agent_reliability_fixture as harness
from cli_fixture import Credential
from fullscreen_console_fixture import wait
from tui_console_fixture import Console, checked, environment_for, write_json


class Provider(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*_): pass
    def do_POST(self):
        try:
            assert self.headers.get('Authorization')=='Bearer fixture-key'
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            users=[m['content'] for m in request['messages'] if m['role']=='user']
            assert users
            self.server.requests.append(users[-1])
            payload={'choices':[{'delta':{'content':'PUBLIC_ACK '+users[-1]},'finish_reason':'stop'}],
                     'usage':{'prompt_tokens':12,'completion_tokens':8}}
            body=('data: '+json.dumps(payload,ensure_ascii=False)+'\n\ndata: [DONE]\n\n').encode()
            self.send_response(200)
            self.send_header('Content-Type','text/event-stream')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Connection','close');self.end_headers()
            self.wfile.write(body);self.wfile.flush()
        except (BrokenPipeError,ConnectionResetError): pass
        except BaseException:self.server.errors.append(traceback.format_exc())
        finally:self.close_connection=True


def worker(args):
    evidence={'schema':1,'scope':'final product CLI, isolated DB/profile, owned hidden Windows console and loopback provider',
              'binary_sha256':hashlib.sha256(args.executable.read_bytes()).hexdigest(),
              'fixture_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'result':'running','checks':[],'snapshots':{}}
    process=None;console=None;credential_written=False
    target='Sencode/connection/custom-session-public-'+uuid.uuid4().hex
    identifier=target.rsplit('/',1)[1]
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Provider)
    server.requests=[];server.errors=[]
    threading.Thread(target=server.serve_forever,daemon=True).start()
    advapi=ctypes.WinDLL('advapi32',use_last_error=True)
    advapi.CredWriteW.argtypes=[ctypes.POINTER(Credential),wintypes.DWORD];advapi.CredWriteW.restype=wintypes.BOOL
    advapi.CredDeleteW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD];advapi.CredDeleteW.restype=wintypes.BOOL

    def record(name,condition=True,detail=None):
        evidence['checks'].append({'name':name,'status':'passed' if condition else 'failed','detail':detail})
        assert condition,(name,detail)

    try:
        deadline=time.monotonic()+10
        while not args.ready.exists():
            assert time.monotonic()<deadline,'Owned console Job not established'
            time.sleep(.02)
        environment=environment_for(args.scratch);os.environ.clear();os.environ.update(environment)
        workspace=args.scratch/'before 项目';workspace.mkdir()
        database=args.scratch/'isolated.sqlite3'

        def run(*arguments,prompt='/exit\n',ok=True,directory=None):
            directory=directory or workspace
            result=subprocess.run([str(args.executable),'--cwd',str(directory),'--database',str(database),
                                   '--connection',identifier,'--tui','plain',*map(str,arguments)],cwd=directory,env=environment,
                                  input=prompt,capture_output=True,text=True,encoding='utf-8',timeout=40)
            assert (result.returncode==0)==ok,(arguments,result.returncode,result.stdout,result.stderr)
            return result

        def sql(statement,parameters=()):
            with closing(sqlite3.connect(database,timeout=5)) as db:
                db.create_function('sengoo_context',1,lambda key:'isolated-public-session-fixture' if key=='instance_id' else None)
                rows=db.execute(statement,parameters).fetchall();db.commit();return rows

        def response(result):
            records=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
            records=[r for r in records if r.get('type')=='result']
            assert len(records)==1,result.stdout
            return records[0]

        run()
        empty=sql('SELECT id FROM sessions')[0][0]
        record('public-new-creates-atomic-root-origin',json.loads(sql('SELECT mode_json FROM shared_modes WHERE session_id=?',(empty,))[0][0])['session_origin']=={'version':1,'kind':'root'})
        host=subprocess.run([str(args.executable),'--cwd',str(workspace),'--database',str(database),'--engine-stdio','resume',empty],
                            input='{"type":"shutdown"}\n',capture_output=True,text=True,encoding='utf-8',env=environment,cwd=workspace,timeout=15)
        ready=[json.loads(line) for line in host.stdout.splitlines() if line.startswith('{')]
        record('private-engine-stdio-accepts-empty-session-and-emits-ready',host.returncode==0 and any(v.get('type')=='ready' and v.get('session_id')==empty for v in ready),{'exit':host.returncode,'stderr':host.stderr})
        rejected_empty=run('resume',empty,ok=False)
        record('ordinary-resume-rejects-empty-session','Error code: 5' in rejected_empty.stderr)

        key=(ctypes.c_ubyte*11).from_buffer_copy(b'fixture-key')
        credential=Credential(Type=1,TargetName=target,CredentialBlobSize=11,CredentialBlob=key,Persist=1)
        checked(advapi.CredWriteW(ctypes.byref(credential),0));credential_written=True
        config={'version':2,'baseUrl':f'http://127.0.0.1:{server.server_port}/v1','protocol':'chatCompletions',
                'successfulProtocol':'chatCompletions','selectedModelId':'fixture','credentialRef':target,'enabledModels':[{'id':'fixture'}]}
        sql("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,'customApi','managed','isolated fixture',?,'fixture',1,1)",(identifier,json.dumps(config)))
        first='# **修复中文😀会话**\n- 保留项目历史'
        parent=response(run('-p',first,'--output-format','json'))['session_id']
        record('public-accepted-first-message-generates-unicode-title',sql('SELECT title,title_source FROM sessions WHERE id=?',(parent,))[0]==('修复中文😀会话 保留项目历史','first_message'))

        console=Console();console.resize(120,42);console.clear();baseline=console.modes()
        def launch(*arguments):
            nonlocal process
            console.clear()
            process=subprocess.Popen([str(args.executable),'--cwd',str(workspace),'--database',str(database),'--connection',identifier,*map(str,arguments)],cwd=workspace,env=environment)
            return wait(console,process,lambda s:'MESSAGE' in s['text'],'public session TUI',20)

        def stop():
            nonlocal process
            if process is not None and process.poll() is None:
                console.key(0x1B,'\x1b');console.key(0x44,'\x04',8);process.wait(timeout=12)
            assert process is None or process.returncode==0
            assert console.modes()==baseline
            process=None

        def slash(name,value=''):
            console.key(0x1B,'\x1b');console.key(0x55,'\x15',8);console.inject(name)
            wait(console,process,lambda s:('COMMANDS' in s['text'] or 'COMMAND ARGUMENTS' in s['text']) and name in s['text'],name+' menu')
            console.key(0x0D,'\r')
            wait(console,process,lambda s:'Command completed' in s['text'] and 'COMMANDS' not in s['text'],name+' completion')
            if value:console.inject(value)
            console.key(0x0D,'\r')

        launch('resume',parent)
        slash('/rename','手工标题 Public')
        wait(console,process,lambda s:'Session renamed.' in s['text'],'rename completion')
        console.command('MANUAL_FOLLOWUP')
        wait(console,process,lambda s:'PUBLIC_ACK MANUAL_FOLLOWUP' in s['text'] and 'NEXT MESSAGE' not in s['text'],'manual followup')
        record('public-rename-is-user-owned-and-survives-next-turn',sql('SELECT title,title_source FROM sessions WHERE id=?',(parent,))[0]==('手工标题 Public','user'))
        slash('/branch','分支标题 Public')
        deadline=time.monotonic()+12;branch=None
        while time.monotonic()<deadline:
            rows=sql("SELECT id,title,title_source FROM sessions WHERE title='分支标题 Public'")
            if rows:branch=rows[0][0];break
            time.sleep(.03)
        assert branch,'Public branch was not created'
        wait(console,process,lambda s:'MESSAGE' in s['text'] and '/branch' not in s['text'],'branch switch')
        console.command('BRANCH_FOLLOWUP')
        wait(console,process,lambda s:'PUBLIC_ACK BRANCH_FOLLOWUP' in s['text'] and 'NEXT MESSAGE' not in s['text'],'branch followup')
        record('public-branch-has-independent-origin-title-and-history',
               sql('SELECT title,title_source FROM sessions WHERE id=?',(branch,))[0]==('分支标题 Public','existing') and
               json.loads(sql('SELECT mode_json FROM shared_modes WHERE session_id=?',(branch,))[0][0])['session_origin']=={'version':1,'kind':'branch','source_session_id':parent} and
               sql("SELECT count(*) FROM messages WHERE session_id=? AND text='BRANCH_FOLLOWUP'",(parent,))[0][0]==0 and
               sql("SELECT count(*) FROM messages WHERE session_id=? AND text='BRANCH_FOLLOWUP'",(branch,))[0][0]==1)
        stop()
        long_prompt='界'*29+'😀'+'尾'
        long_session=response(run('-p',long_prompt,'--output-format','json'))['session_id']
        record('public-first-title-truncates-thirty-unicode-scalars',sql('SELECT title FROM sessions WHERE id=?',(long_session,))[0][0]=='界'*29+'😀…')

        project=sql('SELECT project_id FROM sessions WHERE id=?',(parent,))[0][0]
        with closing(sqlite3.connect(database)) as db:
            db.create_function('sengoo_context',1,lambda key:'isolated-public-seed' if key=='instance_id' else None)
            for index in range(160):
                for kind in ('empty','child'):
                    identity=f'fixture-{kind}-{index:03d}'
                    db.execute("INSERT INTO sessions(id,project_id,title,title_source,created_at,updated_at) VALUES(?,?,?,'placeholder',1,9999999999999)",(identity,project,'EMPTY_SHOULD_NOT_APPEAR' if kind=='empty' else 'CHILD_SHOULD_NOT_APPEAR'))
                    if kind=='child':
                        db.execute("INSERT INTO messages(id,session_id,role,text,created_at,completed_at,revision) VALUES(?,?,'user','child private prompt',1,1,1)",('message-'+identity,identity))
                        db.execute('INSERT INTO shared_modes VALUES(?,?,1)',(identity,json.dumps({'session_origin':{'version':1,'kind':'child','parent_session_id':parent}})))
            db.execute("INSERT INTO sessions(id,project_id,title,title_source,created_at,updated_at) VALUES('fixture-stale-root',?,'Stale selection Public','existing',1,1)",(project,))
            db.execute("INSERT INTO messages(id,session_id,role,text,created_at,completed_at,revision) VALUES('stale-user','fixture-stale-root','user','stale candidate text',1,1,1)")
            db.execute("INSERT INTO shared_modes VALUES('fixture-stale-root',?,1)",(json.dumps({'session_origin':{'version':1,'kind':'root'}}),))
            db.commit()
        rejected_child=run('resume','fixture-child-000',ok=False)
        rejected_search=run('-r','CHILD_SHOULD_NOT_APPEAR',ok=False)
        recent=run('-c',prompt='/context\n/exit\n')
        record('public-id-search-and-continue-exclude-children-and-many-empty-records','Error code: 5' in rejected_child.stderr and 'Error code: 5' in rejected_search.stderr and 'child private prompt' not in recent.stdout and long_prompt in recent.stdout)
        selected=launch('-r')
        picker=wait(console,process,lambda s:'Resume a project session' in s['text'] and '手工标题 Public' in s['text'] and '分支标题 Public' in s['text'],'filtered public resume menu')
        evidence['snapshots']['resume-picker']=picker
        record('public-resume-menu-filters-before-limit-and-hides-internal-ids',
               'SHOULD_NOT_APPEAR' not in picker['text'] and 'fixture-child-' not in picker['text'] and 'session-' not in picker['text'] and 'branch-' not in picker['text'])
        console.inject('Stale selection Public')
        wait(console,process,lambda s:'Resume a project session' in s['text'] and 'Stale selection Public' in s['text'],'stale candidate filter')
        sql("UPDATE shared_modes SET mode_json=?,updated_at=updated_at+1 WHERE session_id='fixture-stale-root'",(json.dumps({'session_origin':{'version':1,'kind':'child','parent_session_id':parent}}),))
        console.key(0x0D,'\r')
        refused=wait(console,process,lambda s:'Conversation is no longer available' in s['text'],'stale picker refusal')
        record('public-resume-picker-revalidates-stale-candidate', 'stale candidate text' not in refused['text'])
        slash('/resume')
        wait(console,process,lambda s:'Resume a project session' in s['text'],'reopened public resume picker')
        console.inject('手工标题 Public');console.key(0x0D,'\r')
        restored=wait(console,process,lambda s:'Resume a project session' not in s['text'] and 'PUBLIC_ACK MANUAL_FOLLOWUP' in s['text'],'public picker selection')
        record('public-resume-selection-restores-parent-context','BRANCH_FOLLOWUP' not in restored['text'])
        stop()
        renamed=args.scratch/'after 改名项目😀';workspace.rename(renamed)
        context=run('resume',parent,prompt='/context\n/exit\n',directory=renamed)
        record('public-resume-after-project-directory-rename-keeps-history','MANUAL_FOLLOWUP' in context.stdout and 'BRANCH_FOLLOWUP' not in context.stdout)
        with closing(sqlite3.connect(renamed/'.sencode/history.sqlite3')) as archive:
            record('project-local-archive-keeps-title-provenance-and-identity',
                   archive.execute('SELECT title,title_source FROM ph_sessions WHERE id=?',(parent,)).fetchone()==('手工标题 Public','user') and
                   json.loads(archive.execute('SELECT mode_json FROM ph_shared_modes WHERE session_id=?',(parent,)).fetchone()[0])['session_origin']=={'version':1,'kind':'root'})
        record('no-remote-provider-request',len(server.requests)==4 and not server.errors,{'loopback_requests':len(server.requests),'errors':server.errors})
        evidence['result']='passed'
    except BaseException:
        evidence['result']='failed';evidence['error']=traceback.format_exc()
        if console is not None and process is not None and process.poll() is None:
            evidence['last_screen']=console.read(viewport=True)
    finally:
        if process is not None and process.poll() is None:
            process.terminate();process.wait(timeout=5)
        if credential_written:checked(advapi.CredDeleteW(target,1,0))
        server.shutdown();server.server_close()
        evidence['provider_errors']=server.errors
        write_json(args.evidence,evidence)
    return 0 if evidence['result']=='passed' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path);parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--scratch',type=Path);parser.add_argument('--ready',type=Path)
    args=parser.parse_args();args.executable=args.executable.resolve(strict=True);args.evidence=args.evidence.resolve()
    if args.worker:return worker(args)
    gate=json.loads((args.executable.parent/'build-result.json').read_text(encoding='utf-8-sig'))
    assert gate['result']=='built' and gate['inputs_unchanged'] is True
    assert gate['exe_sha256']==hashlib.sha256(args.executable.read_bytes()).hexdigest()
    harness.__file__=__file__
    return harness.controller(args)


if __name__=='__main__':raise SystemExit(main())
