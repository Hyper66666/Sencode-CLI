import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const sections=['sencode-config third-party notices\n\nMicrosoft Visual C++ runtime: Microsoft redistributable license terms apply.\nSQLite: public domain.'];
async function collect(label,directory,license) {
  let entries;
  try { entries=await readdir(directory); } catch(error) { if(error.code==='ENOENT') return; throw error; }
  sections.push(`\n===== ${label} (${license ?? 'see license below'}) =====\n`);
  for(const file of entries.filter(name=>/^(LICENSE|LICENCE|COPYING|NOTICE)([._-].*)?$/i.test(name)).sort()) {
    try { sections.push(`${file}\n${await readFile(path.join(directory,file),'utf8')}`); } catch { /* license directory, not a text file */ }
  }
}
const lock=JSON.parse(await readFile(path.join(root,'package-lock.json'),'utf8'));
for(const [folder,pkg] of Object.entries(lock.packages)) {
  if(!folder) continue;
  await collect(`${folder.replace(/^.*node_modules\//,'')} ${pkg.version}`,path.join(root,folder),pkg.license);
}
const metadata=spawnSync('cargo',['metadata','--locked','--format-version','1','--manifest-path',path.join(root,'src-tauri/Cargo.toml')],{encoding:'utf8',windowsHide:true,maxBuffer:32*1024*1024});
if(metadata.status!==0) throw new Error('Cannot collect Rust dependency notices');
for(const pkg of JSON.parse(metadata.stdout).packages) await collect(`${pkg.name} ${pkg.version}`,path.dirname(pkg.manifest_path),pkg.license);
await collect('Sencode',path.resolve(root,'../..'),'Apache-2.0');
await collect('Sengoo',process.env.SENCODE_SENGOO_ROOT ?? 'D:/Sengoo','see license');
await mkdir(path.join(root,'target'),{recursive:true});
await writeFile(path.join(root,'target/THIRD-PARTY-NOTICES.txt'),sections.join('\n'),'utf8');
console.log('Dependency notices collected');
