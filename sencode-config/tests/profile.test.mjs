import { test } from 'node:test';
import assert from 'node:assert/strict';
import { exportProfile, importProfile, modelEntry, newInput, validateInput, validModelId } from '../src/profile.ts';

test('exports only reviewed metadata and imports into a new profile', () => {
  const data = { id:'custom-owned', name:'中文😀',kind:'customApi',model:'model-a',base_url:'https://example.invalid/v1',protocol:'responses',models:['model-a'],enabled_models:[modelEntry('model-a'),{id:'model-b',label:'B',capabilities:{visionSupported:true,private:'private'}}],discovered_model_ids:['model-c'],api_key:'must-never-export',credentialRef:'private' };
  const output=exportProfile(data);
  assert.deepEqual(Object.keys(output),['schema','name','base_url','protocol','model','enabled_models','discovered_model_ids']);
  assert.ok(!JSON.stringify(output).includes('private'));
  const imported=importProfile(JSON.stringify({...output, api_key:'ignored'}));
  assert.equal(imported.api_key,''); assert.equal(imported.existing,false);
  assert.notEqual(imported.id,data.id); assert.equal(imported.name,data.name);
  assert.equal(imported.enabled_models[1].capabilities.visionSupported,true);
  assert.deepEqual(imported.discovered_model_ids,['model-c']);
});
test('creation requires a key while edit preserves an empty key', () => {
  const input={...newInput(),name:'Owned',base_url:'https://example.invalid',model:'test',enabled_models:[modelEntry('test')]};
  assert.equal(validateInput(input),'请输入 API Key');
  assert.equal(validateInput({...input,existing:true}),null);
});
test('URL, controls, oversized and unsupported imports are rejected', () => {
  const input={...newInput(),name:'Owned',base_url:'https://example.invalid',model:'test',api_key:'fixture',enabled_models:[modelEntry('test')]};
  for (const base_url of ['javascript:alert(1)','http://outside.invalid','https://user:pass@site.invalid','https://site.invalid?key=private']) assert.ok(validateInput({...input,base_url}));
  assert.equal(validateInput({...input,base_url:'http://127.0.0.1:11434/v1'}),null);
  assert.ok(validateInput({...input,name:'x\0y'}));
  assert.ok(validateInput({...input,name:'中'.repeat(50)}));
  assert.throws(()=>importProfile('{"schema":5}'));
  assert.throws(()=>importProfile('[]'));
  assert.throws(()=>importProfile('x'.repeat(65537)));
});
test('enabled catalog is bounded and default must be enabled; legacy import still works',()=>{
  const input={...newInput(),name:'Owned',base_url:'https://example.invalid',model:'a',api_key:'fixture',enabled_models:[modelEntry('a')]};
  assert.equal(validateInput(input),null);
  assert.ok(validateInput({...input,enabled_models:[]}));
  assert.ok(validateInput({...input,model:'disabled-model'}));
  assert.ok(validateInput({...input,enabled_models:[modelEntry('a'),modelEntry('a')]}));
  assert.ok(validateInput({...input,enabled_models:Array.from({length:257},(_,i)=>modelEntry(`model-${i}`))}));
  for(const id of ['','a b','a\nb','a\u2003b','a\u0085b','a\0b','a'.repeat(201)]) assert.equal(validModelId(id),false);
  assert.equal(validModelId('模型-😀'),true);
  const imported=importProfile(JSON.stringify({schema:1,name:'Legacy',base_url:'https://example.invalid',protocol:'responses',model:'a'}));
  assert.deepEqual(imported.enabled_models,[modelEntry('a')]);
  assert.throws(()=>importProfile(JSON.stringify({...exportProfile({...input,kind:'customApi',models:['a']}),enabled_models:[{id:'a',capabilities:{visionSupported:'yes'}}]})));
});
