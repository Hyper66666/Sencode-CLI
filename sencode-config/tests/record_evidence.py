"""Collect artifact/source identities; never read user configuration."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from datetime import datetime, timezone

root=Path(__file__).resolve().parents[1]
digest=lambda file:hashlib.sha256(file.read_bytes()).hexdigest()
sha=lambda directory:subprocess.check_output(['git','-C',str(directory),'rev-parse','HEAD'],text=True).strip()
files=[root/name for name in ['package.json','package-lock.json','src-tauri/Cargo.toml','src-tauri/Cargo.lock','src-tauri/tauri.conf.json','src-tauri/src/main.rs']]
files+=list((root/'src').glob('*'))+list((root/'scripts').glob('*'))+list((root/'tests').glob('*.*'))
files += [root.parent/'sencode-cli/src/config_bridge.sg',root.parent/'sencode-cli/src/config_probe.sg']
files += list((root.parent/'openspec/changes/add-sencode-config').rglob('*.md'))
manifest={'recorded_at':datetime.now(timezone.utc).isoformat(),'host':platform.node(),'platform':platform.platform(),'sencode_base_sha':sha(root),'sengoo_base_sha':sha(Path('D:/Sengoo')),'working_tree':'dirty; preserved; new app/bridge changes are not committed','source_sha256':{str(file.relative_to(root.parent)).replace('\\','/'):digest(file) for file in sorted(set(files)) if file.is_file()},'artifacts':{str(file):digest(file) for file in [Path('D:/SencodeConfig/sencode-config.exe'),Path('D:/SencodeConfig/resources/sencode-config-bridge.exe'),Path('D:/sencode-config-0.1.0-windows-x64.zip'),Path('D:/SencodeCLI/bin/sen.exe'),Path('D:/Sengoo/target/bounded-request-build/debug/sgc.exe')]}}
(root/'target/build-evidence.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({key:manifest[key] for key in ['recorded_at','host','sencode_base_sha','sengoo_base_sha','artifacts']},ensure_ascii=False,indent=2))
