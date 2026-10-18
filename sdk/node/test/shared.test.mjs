import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parse,serialize,validateData,ProtocolError,validate} from '../dist/index.js';
const root = new URL('../../../conformance/sdk/',import.meta.url);
const manifest = JSON.parse(readFileSync(new URL('manifest.json',root)));
for (const path of manifest.cases) {
  const c = JSON.parse(readFileSync(new URL(path,root)));
  test(c.id,()=>{
    let value, error;
    try { value = c.operation === 'data' ? (validateData(c.schema,c.input),c.input) : parse(c.contract,c.type,JSON.stringify(c.input)); } catch(e) {error=e;}
    if (!c.expected.accepted) {
      assert.ok(error instanceof ProtocolError, String(error));
      if(c.expected.error !== '*') assert.equal(error.code,c.expected.error);
    } else {
      assert.ifError(error);
      assert.deepEqual(JSON.parse(serialize(value)),c.expected.normalized);
      if(c.operation==='parse') assert.deepEqual(parse(c.contract,c.type,serialize(value)),value);
    }
  });
}
test('duplicate keys',()=>assert.throws(()=>parse('vcp','result','{"protocol":"draft","protocol":"draft"}'),e=>e.code==='PROTOCOL_JSON'));
test('escaped duplicate keys',()=>assert.throws(()=>parse('provider','outcome','{"invocation_id":"i","state":"COMPLETED","output":{"x":1,"\\u0078":1}}'),ProtocolError));
test('prototype keys remain ordinary JSON',()=>{
 const raw='{"invocation_id":"i","state":"COMPLETED","output":{"__proto__":{"safe":true}}}';
 assert.deepEqual(JSON.parse(serialize(parse('provider','outcome',raw))),JSON.parse(raw));
});
test('nonfinite serialization',()=>assert.throws(()=>serialize({x:NaN}),ProtocolError));
test('numeric overflow rejects at parse',()=>assert.throws(()=>parse('provider','outcome','{"invocation_id":"i","state":"COMPLETED","output":1e400}'),ProtocolError));
test('precision loss rejects at parse',()=>assert.throws(()=>parse('provider','outcome','{"invocation_id":"i","state":"COMPLETED","output":9007199254740993}'),ProtocolError));
test('unsupported graph semantics fail closed',()=>assert.throws(()=>validate('vcp','graph',{nodes:[],edges:[]}),ProtocolError));
test('untrusted external ref is rejected',()=>assert.throws(()=>validateData({$ref:'https://example.com/a'},null),e=>e.code==='INVALID_PROVIDER_OUTPUT'));
