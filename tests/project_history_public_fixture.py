"""Real CLI resume from a renamed external project, with no API/key/user DB."""
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


def main():
    executable = Path(sys.argv[1]).resolve()
    root = Path(tempfile.mkdtemp(prefix='sencode-portable-public-')).resolve()
    before = root / 'before 项目'
    after = root / 'after 项目😀'
    before.mkdir()
    catalog = root / 'catalog.sqlite3'

    def run(directory, db, *arguments, prompt='/context\n/exit\n'):
        result = subprocess.run([str(executable), '--cwd', str(directory), '--database', str(db), '--tui', 'plain', *arguments],
                                cwd=directory, input=prompt, capture_output=True, text=True, encoding='utf-8', timeout=45)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        return result

    try:
        run(before, catalog, prompt='/exit\n')
        with closing(sqlite3.connect(catalog)) as db:
            db.create_function('sengoo_context', 1, lambda key: 'owned-desktop-fixture' if key == 'instance_id' else None)
            session, project = db.execute('SELECT id,project_id FROM sessions').fetchone()
            db.execute("UPDATE sessions SET title='portable unique 会话' WHERE id=?", (session,))
            db.execute("INSERT INTO messages(id,session_id,role,text,created_at,completed_at,revision) VALUES('owned-message',?,'user',?,1,1,1)", (session, '聊天跟随文件夹😀'))
            # Session creation now atomically creates root provenance. Model
            # a desktop Goal update without replacing that shared metadata.
            db.execute("INSERT INTO shared_modes(session_id,mode_json,updated_at) VALUES(?,?,1) ON CONFLICT(session_id) DO UPDATE SET mode_json=json_set(shared_modes.mode_json,'$.goal',json_extract(excluded.mode_json,'$.goal')),updated_at=shared_modes.updated_at+1", (session, json.dumps({'goal': {'objective': 'kept paused', 'requests': 5, 'status': 3, 'checks': []}})))
            db.commit()
        # Capture a desktop-style shared write before moving the idle project.
        assert '聊天跟随文件夹' in run(before, catalog, 'resume', session).stdout
        assert before.parent == root and after.parent == root
        before.rename(after)
        result = run(after, catalog, '-c')
        assert '聊天跟随文件夹' in result.stdout
        assert '聊天跟随文件夹' in run(after, catalog, '-r', 'portable unique').stdout
        with closing(sqlite3.connect(after / '.sencode/history.sqlite3')) as db:
            assert db.execute('SELECT id FROM ph_sessions').fetchone()[0] == session
            assert db.execute('SELECT project_id FROM ph_meta').fetchone()[0] == project
            assert json.loads(db.execute('SELECT mode_json FROM ph_shared_modes').fetchone()[0])['goal']['requests'] == 5
        retired = root / 'retired.sqlite3'
        assert catalog.parent == root and retired.parent == root
        catalog.rename(retired)
        replacement = root / 'new-catalog.sqlite3'
        assert '聊天跟随文件夹' in run(after, replacement, '--import-history', 'resume', session).stdout
        with closing(sqlite3.connect(replacement)) as db:
            assert db.execute('SELECT id FROM sessions').fetchone()[0] == session
            assert db.execute('SELECT count(*) FROM shared_executions WHERE active=1').fetchone()[0] == 0
        print(json.dumps({'result': 'passed', 'checks': ['project-local capture', 'renamed root -c', 'renamed root -r search', 'stable session and project IDs', 'Goal budget preserved and paused', 'missing catalog restore via public resume']}, ensure_ascii=False))
        return 0
    finally:
        for directory, _, files in os.walk(root, topdown=False, followlinks=False):
            for name in files:
                (Path(directory) / name).unlink()
            Path(directory).rmdir()


if __name__ == '__main__':
    raise SystemExit(main())
