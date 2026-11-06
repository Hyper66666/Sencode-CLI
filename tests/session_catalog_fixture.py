"""Native session catalog contracts; all databases live in an inventoried temp tree."""
from __future__ import annotations
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile


def cleanup(root):
    entries=list(root.rglob('*'))
    for entry in entries:
        assert entry.resolve().is_relative_to(root.resolve()), entry
    for entry in entries:
        if entry.is_file() or entry.is_symlink(): entry.unlink()
    for entry in sorted((p for p in entries if p.is_dir()),key=lambda p:len(p.parts),reverse=True): entry.rmdir()
    root.rmdir()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path)
    parser.add_argument('--evidence',type=Path)
    args=parser.parse_args()
    executable=args.executable.resolve(strict=True)
    root=Path(tempfile.mkdtemp(prefix='sencode-session-catalog-用户-')).resolve()
    directory=root/'project 中文';directory.mkdir()
    other=root/'other';other.mkdir()
    database=root/'catalog.sqlite3'
    checks=[]
    evidence={'schema':1,'scope':'isolated-native-session-catalog','platform':os.name,
              'binary_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),'checks':checks,'result':'running'}

    def run(action,*extra,cwd=directory,ok=True):
        result=subprocess.run([str(executable),str(database),str(cwd),action,*map(str,extra)],capture_output=True,text=True,encoding='utf-8',timeout=30)
        assert (result.returncode==0)==ok,(action,result.returncode,result.stdout,result.stderr)
        return result.stdout.strip()

    def sql(statement,params=()):
        with closing(sqlite3.connect(database)) as db:
            db.create_function('sengoo_context',1,lambda key:'isolated-catalog-fixture' if key=='instance_id' else None)
            rows=db.execute(statement,params).fetchall();db.commit();return rows

    def seed(identity,*,project=None,text='fixture user',mode=None,title='New task',source='placeholder',updated=9999999999999):
        project=project or sql('SELECT project_id FROM sessions WHERE id=?',(parent,))[0][0]
        sql('INSERT INTO sessions(id,project_id,title,title_source,created_at,updated_at) VALUES(?,?,?,?,1,?)',(identity,project,title,source,updated))
        if text is not None: sql("INSERT INTO messages(id,session_id,role,text,created_at,completed_at,revision) VALUES(?,?,'user',?,1,1,1)",('m-'+identity,identity,text))
        if mode is not None:sql('INSERT INTO shared_modes(session_id,mode_json,updated_at) VALUES(?,?,1)',(identity,mode))

    def ledger(identity,payload,*,name='spawn_agent',state='complete',owner=None):
        sql('INSERT INTO shared_tool_ledger(session_id,call_id,execution_id,fence,name,arguments,state,result,updated_at) VALUES(?,?,\'fixture\',0,?,\'{}\',?,?,1)',(owner or parent,identity,name,state,payload))

    def ids(action='list'): return [item['id'] for item in json.loads(run(action))['sessions']]

    try:
        parent=run('create')
        assert json.loads(sql('SELECT mode_json FROM shared_modes WHERE session_id=?',(parent,))[0][0])=={'session_origin':{'version':1,'kind':'root'}}
        assert run('member',parent)=='true' and run('eligible',parent)=='false' and ids()==[]
        before=sql('SELECT count(*) FROM sessions')[0][0]
        run('child','nonexistent',ok=False)
        assert sql('SELECT count(*) FROM sessions')[0][0]==before
        child=run('child',parent)
        assert json.loads(sql('SELECT mode_json FROM shared_modes WHERE session_id=?',(child,))[0][0])['session_origin']=={'version':1,'kind':'child','parent_session_id':parent}
        assert child in ids('agents') and run('eligible',child)=='false'
        checks.append('atomic-root-child-origin-invalid-parent-rollback-and-empty-membership')

        prompt='# **修复中文😀**\n- [x] 输入   测试'
        run('append',parent,prompt)
        assert sql('SELECT title,title_source FROM sessions WHERE id=?',(parent,))[0]==('修复中文😀 输入 测试','first_message')
        run('append',child,'child-only secret prompt')
        assert ids()==[parent]
        assert [p['session_id'] for p in json.loads(run('prompts'))['prompts']]==[parent]
        run('rename',parent,'New task');run('append',parent,'must not replace manual title')
        assert sql('SELECT title,title_source FROM sessions WHERE id=?',(parent,))[0]==('New task','user')
        branch=run('branch',child,'分支标题')
        run('append',branch,'must not replace branch title')
        assert sql('SELECT title,title_source FROM sessions WHERE id=?',(branch,))[0]==('分支标题','existing')
        assert json.loads(sql('SELECT mode_json FROM shared_modes WHERE session_id=?',(branch,))[0][0])['session_origin']=={'version':1,'kind':'branch','source_session_id':child}
        assert branch in ids() and branch not in ids('agents')
        checks.append('first-message-title-manual-title-branch-title-and-child-prompt-isolation')

        foreign=run('create',cwd=other)
        run('child',foreign,ok=False)
        for identity in ['legacy-spawn','legacy-list','legacy-wait','desktop-child','unknown-orphan','bad-json','duplicate-id','cross-project','running-only','self-child','fractional-origin']:
            seed(identity)
        ledger('spawn',json.dumps({'session_id':'legacy-spawn','role':'explore'}))
        ledger('list',json.dumps({'children':[None,5,'x',{'session_id':'legacy-list','role':'plan'}]}),name='list_agents')
        ledger('wait',json.dumps({'children':[{'session_id':'legacy-wait','role':'general'}]}),name='wait_agents')
        ledger('invalid','{broken')
        ledger('duplicate','{"session_id":"unknown-orphan","session_id":"duplicate-id","role":"explore"}')
        ledger('cross',json.dumps({'session_id':'cross-project','role':'explore'}),owner=foreign)
        ledger('running',json.dumps({'session_id':'running-only','role':'explore'}),state='running')
        ledger('scalar','5');ledger('null','null');ledger('string','"text"')
        sql("INSERT INTO subagent_runs(id,session_id,origin,child_session_id,status,record_json,started_at,updated_at) VALUES('desktop-run',?,'native','desktop-child','complete','{}',1,1)",(parent,))
        sql("INSERT INTO shared_modes VALUES('self-child',?,1)",(json.dumps({'session_origin':{'version':1,'kind':'child','parent_session_id':'self-child'}}),))
        sql("INSERT INTO shared_modes VALUES('fractional-origin',?,1)",(json.dumps({'session_origin':{'version':1.5,'kind':'child','parent_session_id':parent}}),))
        visible=set(ids());hidden={'legacy-spawn','legacy-list','legacy-wait','desktop-child',child}
        assert not visible & hidden, visible & hidden
        assert {'unknown-orphan','bad-json','duplicate-id','cross-project','running-only','self-child','fractional-origin'} <= visible
        assert hidden <= set(ids('agents'))
        checks.append('exact-legacy-ledger-and-desktop-evidence-without-orphan-cross-project-or-malformed-guessing')

        seed('legacy-custom',title='保留旧版手工标题')
        seed('legacy-placeholder',text='## 1. **旧记录标题😀**')
        listed={row['id']:row['title'] for row in json.loads(run('list'))['sessions']}
        assert listed['legacy-custom']=='保留旧版手工标题' and listed['legacy-placeholder']=='旧记录标题😀'
        assert sql("SELECT title,title_source FROM sessions WHERE id='legacy-placeholder'")[0]==('New task','placeholder')
        for n in range(151):
            seed('empty-'+str(n),text=None)
            seed('hidden-'+str(n),mode=json.dumps({'session_origin':{'version':1,'kind':'child','parent_session_id':parent}}))
        assert parent in ids() and len(ids()) < 100
        assert run('eligible','legacy-spawn')=='false' and run('eligible',parent)=='true'
        prompts=json.loads(run('prompts'))['prompts']
        assert all(not p['session_id'].startswith('hidden-') for p in prompts)
        checks.append('read-only-legacy-title-fallback-and-filtering-before-list-and-history-limits')
        seed('unicode-whitespace',text='\u00a0\u2003\u3000\n\t')
        assert run('eligible','unicode-whitespace')=='false'

        for text,expected in [('[empty]',''),('<system-reminder>hidden</system-reminder>\n## 标题','标题'),
                              ('internal <<<SENCODE_DESIGN_USER>>> 用户需求','用户需求'),
                              ('😀'*31,'😀'*30+'…'),('中'*30,'中'*30),('1. [x] **任务**','任务'),
                              ('[image: C:\\images\\架构.png, /tmp/second.png]','架构.png')]:
            assert run('title',text)==expected,(text,run('title',text),expected)
        safe=json.loads(run('sanitize',json.dumps({'session_origin':{'version':1,'kind':'child','parent_session_id':parent,'execute':'bad'},'context':'bad','goal':{'requests_used':7,'status':3}})))
        assert set(safe)=={'session_origin','goal'} and set(safe['session_origin'])=={'version','kind','parent_session_id'}
        assert safe['goal']['status']==2 and safe['goal']['requests']==7
        run('sanitize','{"session_origin":{"version":2,"kind":"root"}}',ok=False)
        shared=(Path(__file__).parent.parent/'shared-state/session-children-v1.sql').read_text(encoding='utf-8').strip()
        assert run('sql-source').strip()==shared
        checks.append('unicode-thirty-scalar-titles-and-non-executable-origin-import-allowlist-shared-sql')
        assistant={'role':'assistant','content':'分析中间态','responses_end_turn':False,'requires_continuation':True,
                   'responses_output':[{'type':'message','id':'opaque-message','phase':'commentary','content':[]}],
                   'responses_endpoint':'fixture-endpoint','responses_model':'fixture-model','responses_connection':'fixture-connection'}
        run('stream',parent,json.dumps(assistant))
        restored=json.loads(run('history',parent))['messages'][-1]
        assert restored==assistant
        assert sql('SELECT text FROM messages WHERE session_id=? ORDER BY revision DESC LIMIT 1',(parent,))[0][0]=='分析中间态'
        assistant['responses_end_turn']=True;assistant['requires_continuation']=False;assistant['content']='最终回答'
        run('stream',parent,json.dumps(assistant))
        assert json.loads(run('history',parent))['messages'][-1]==assistant
        checks.append('stream-finish-reopen-preserves-responses-control-output-scope-and-public-content')
        evidence['result']='passed'
        print(json.dumps(evidence,ensure_ascii=False,indent=2))
    except BaseException:
        evidence['result']='failed';raise
    finally:
        if args.evidence:
            args.evidence.parent.mkdir(parents=True,exist_ok=True)
            args.evidence.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        cleanup(root)


if __name__=='__main__':main()
