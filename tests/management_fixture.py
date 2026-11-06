"""Public management commands, isolated files and no credentials/network."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile


def main():
    executable = Path(sys.argv[1]).resolve()
    root = Path(tempfile.mkdtemp(prefix='sencode-local-management-')).resolve()
    workspace = root / 'workspace 中文'
    workspace.mkdir()
    database = root / 'state.sqlite3'
    checks = []

    def run(*args, ok=True):
        result = subprocess.run([str(executable), '--cwd', str(workspace), '--database', str(database), *args], capture_output=True, text=True, encoding='utf-8', timeout=30)
        assert (result.returncode == 0) == ok, (args, result.returncode, result.stdout, result.stderr)
        return result

    try:
        result = run('mcp', 'list')
        assert json.loads(result.stdout)['servers'] == []
        assert not (workspace / '.sencode').exists()
        run('mcp', 'list', 'unexpected', ok=False)
        marker = root / 'server-started.txt'
        script = root / 'owned_server.py'
        script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("started")\n', encoding='utf-8')
        run('mcp', 'add', 'owned', sys.executable, str(script))
        before = (workspace / '.sencode/mcp.json').read_bytes()
        run('mcp', 'doctor', 'owned', ok=False)
        assert not marker.exists()
        run('--plan', '--allow-commands', 'mcp', 'doctor', 'owned', ok=False)
        run('--plan', 'mcp', 'remove', 'owned', ok=False)
        run('--plan', 'mcp', 'add', 'other', sys.executable, ok=False)
        assert (workspace / '.sencode/mcp.json').read_bytes() == before
        checks.append('MCP reads create no directory; process launch requires fresh approval; Plan cannot launch or mutate')
        run('extensions', 'list')
        sidecar = Path(str(database) + '.extensions.sqlite3')
        assert not sidecar.exists()
        run('extensions', 'inspect', 'missing', ok=False)
        assert not sidecar.exists()
        run('extensions', 'list', 'unexpected', ok=False)
        run('extensions', 'list', '--yes', ok=False)
        checks.append('extension inspection has no absent-store side effect and rejects stray review flags')
        worker = root / 'worker.exe'
        shutil.copyfile(executable, worker)
        manifest = root / 'worker.json'
        manifest.write_text(json.dumps({'schema': 1, 'id': 'owned-worker', 'version': '0.1.0', 'language': 'sengoo',
            'protocol': 'sencode.native-worker/1', 'executable': worker.name, 'sha256': hashlib.sha256(worker.read_bytes()).hexdigest(),
            'timeout_ms': 1000, 'before_tool': ['read_file'], 'after_tool': []}), encoding='utf-8')
        run('--plan', 'extensions', 'add', str(manifest), ok=False)
        assert not sidecar.exists()
        added = json.loads(run('extensions', 'add', str(manifest)).stdout)
        assert added['enabled'] is False
        run('--auto-edit', '--allow-commands', 'extensions', 'enable', 'owned-worker', ok=False)
        run('--plan', 'extensions', 'enable', 'owned-worker', '--yes', ok=False)
        enabled = json.loads(run('extensions', 'enable', 'owned-worker', '--yes').stdout)
        assert enabled['enabled'] is True
        run('extensions', 'disable', 'owned-worker')
        assert json.loads(run('extensions', 'inspect', 'owned-worker').stdout)['enabled'] is False
        run('extensions', 'remove', 'owned-worker')
        assert json.loads(run('extensions', 'list').stdout)['workers'] == []
        assert not marker.exists()
        checks.append('add is disabled; trust is explicit and Plan guarded; management never launches a worker')
        print(json.dumps({'result': 'passed', 'checks': checks}, ensure_ascii=False))
        return 0
    finally:
        for directory, _, files in os.walk(root, topdown=False, followlinks=False):
            for name in files:
                (Path(directory) / name).unlink()
            Path(directory).rmdir()


if __name__ == '__main__':
    raise SystemExit(main())
