import Ajv2020 from 'ajv/dist/2020.js';
import { readFileSync } from 'node:fs';
import { parse as parseJson, isSafeNumber } from 'lossless-json';

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export type WireObject = { [key: string]: Json };
export const SDK_VERSION = '0.1.0';
export const VCP_VERSION = 'draft';
export const PROVIDER_CONTRACT_VERSION = '0.1';
export const SPEC_REVISION = '5f17f402a270882f244a54dde25eda92a085eb39';
type Rule = { code: string; schema: object };
const bundle = JSON.parse(readFileSync(new URL('../schemas/bundle.json', import.meta.url), 'utf8'));
const ajv = new Ajv2020.default({ strict: false, validateFormats: false, allErrors: true });
for (const schema of Object.values(bundle.schemas)) ajv.addSchema(schema as object);

/** Stable codes are normative where defined; SDK_UNSUPPORTED is local. */
export class ProtocolError extends Error {
  constructor(public readonly code: string, message: string, public readonly path = '') { super(message); }
}
function fail(code: string, message = code): never { throw new ProtocolError(code, message); }
function id(contract: string, type: string): string {
  if (contract !== 'vcp' && contract !== 'provider') fail('SDK_UNSUPPORTED', 'Unknown contract');
  return (contract === 'vcp' ? 'urn:verification:draft:' : 'urn:openverify:provider:0.1:') + type;
}
function check(schema: object | boolean, value: Json, code: string): void {
  if (!ajv.validate(schema, value)) fail(code, ajv.errorsText());
}
/** Structural validation only. Does not certify semantic or execution support. */
export function validateStructure(contract: string, type: string, value: Json): void {
  const schema = bundle.schemas[id(contract, type)];
  if (!schema) fail('SDK_UNSUPPORTED', 'Unknown object type');
  if (contract === 'vcp' && value && !Array.isArray(value) && typeof value === 'object' && 'protocol' in value && value.protocol !== 'draft') fail('PROTOCOL_VERSION');
  if (contract === 'provider' && type === 'invocation' && value && !Array.isArray(value) && typeof value === 'object' && 'contract_version' in value && value.contract_version !== '0.1') fail('CONTRACT_VERSION_UNSUPPORTED');
  check(schema, value, contract === 'vcp' ? 'PROTOCOL_STRUCTURE' : type === 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT');
}
/** Validates a self-contained capability schema without network resolution. */
export function validateData(schema: Json, value: Json, code = 'INVALID_INPUT'): void {
  const root = schema;
  const positions = new Set<Json>();
  const refs: string[] = [];
  const maps = ['properties', 'patternProperties', '$defs', 'dependentSchemas'];
  const singles = ['additionalProperties','unevaluatedProperties','propertyNames','contains','items','unevaluatedItems','not','if','then','else','contentSchema'];
  const arrays = ['allOf','anyOf','oneOf','prefixItems'];
  function visit(s: Json, top = false): void {
    if (typeof s === 'boolean') { positions.add(s); return; }
    if (!s || Array.isArray(s) || typeof s !== 'object') fail('INVALID_PROVIDER_OUTPUT', 'Invalid schema position');
    positions.add(s);
    if ((!top && '$id' in s) || ['$dynamicRef','$dynamicAnchor','$anchor'].some(k => k in s)) fail('INVALID_PROVIDER_OUTPUT', 'Unsupported schema resource');
    if ('$schema' in s && s.$schema !== 'https://json-schema.org/draft/2020-12/schema') fail('INVALID_PROVIDER_OUTPUT', 'Wrong schema draft');
    if ('$ref' in s) {
      if (typeof s.$ref !== 'string' || !(s.$ref === '#' || s.$ref.startsWith('#/'))) fail('INVALID_PROVIDER_OUTPUT', 'External reference');
      refs.push(s.$ref);
    }
    for (const k of maps) if (s[k] && typeof s[k] === 'object' && !Array.isArray(s[k])) for (const v of Object.values(s[k])) visit(v);
    for (const k of singles) if (k in s) visit(s[k]);
    for (const k of arrays) if (Array.isArray(s[k])) for (const v of s[k]) visit(v);
  }
  visit(root, true);
  for (const ref of refs) {
    let target: any = root;
    for (const part of ref === '#' ? [] : ref.slice(2).split('/')) {
      if (/~(?:[^01]|$)/.test(part)) fail('INVALID_PROVIDER_OUTPUT', 'Invalid pointer');
      const key = part.replace(/~1/g,'/').replace(/~0/g,'~');
      if (target === null || typeof target !== 'object' || !Object.hasOwn(target,key)) fail('INVALID_PROVIDER_OUTPUT', 'Dangling reference');
      target = target[key];
    }
    if (!positions.has(target)) fail('INVALID_PROVIDER_OUTPUT', 'Reference outside schema positions');
  }
  // A fresh registry avoids root $id collisions between independent capabilities.
  const validator = new Ajv2020.default({ strict: false, validateFormats: false, allErrors: true });
  let compiled;
  try { compiled = validator.compile(schema as object | boolean); } catch (e) { fail('INVALID_PROVIDER_OUTPUT', String(e)); }
  if (!compiled(value)) fail(code, validator.errorsText(compiled.errors));
}
function semantics(contract: string, type: string, value: WireObject): void {
  for (const rule of (bundle.rules[type] || []) as Rule[]) check(rule.schema, value, contract === 'provider' ? 'INVALID_PROVIDER_OUTPUT' : rule.code);
  if (type === 'resource' && value.kind === 'RANGE' && (value.minimum as number) > (value.maximum as number)) fail(contract === 'vcp' ? 'RESOURCE_MEASUREMENT' : 'INVALID_PROVIDER_OUTPUT');
  if (contract === 'vcp') {
    for (const e of (Array.isArray(value.extensions) ? value.extensions : [])) validate('vcp','extension',e);
    for (const e of (Array.isArray(value.evidence) ? value.evidence : [])) validate('vcp','evidence',e);
    if (value.artifact_ref != null) validate('vcp','artifact-ref',value.artifact_ref);
    if (value.usage) for (const r of Object.values(value.usage)) validate('vcp','resource',r);
  } else {
    if (value.deadline !== undefined || value.timestamp !== undefined) fail('SDK_UNSUPPORTED','Timestamp semantics are not implemented');
    if (type === 'provider-event' && ['evidence','artifact'].includes(value.kind as string)) {
      try { validate('vcp',value.kind === 'evidence' ? 'evidence' : 'artifact-ref',value.payload); } catch { fail('INVALID_PROVIDER_OUTPUT'); }
    }
    if (type === 'provider-event' && value.kind === 'resource_usage') for (const r of Object.values(value.payload as WireObject)) {
      try { validate('vcp','resource',r); } catch { fail('INVALID_PROVIDER_OUTPUT'); }
    }
    if (type === 'provider-manifest') {
      const identities = new Set<string>();
      for (const c of value.capabilities as WireObject[]) {
        const key = JSON.stringify([c.capability_id,c.capability_version]);
        if (identities.has(key)) fail('INVALID_PROVIDER_OUTPUT','Duplicate capability');
        identities.add(key);
        if (c.vcp_version && !(value.supported_vcp_versions as Json[]).includes(c.vcp_version)) fail('INVALID_PROVIDER_OUTPUT','Unadvertised VCP');
        semantics('provider','capability',c);
      }
    }
    if (type === 'capability') for (const k of ['input_schema','output_schema','config_schema']) {
      // Compile and validate schema itself; a rejected instance is expected here.
      try { validateData(value[k], null); } catch (e) { if (!(e instanceof ProtocolError) || e.code !== 'INVALID_INPUT') throw e; }
    }
    if (type === 'initialize-result') validate('provider','provider-manifest',value.manifest);
    if (value.vcp_version != null && value.vcp_version !== 'draft') fail(type === 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT');
    if (type === 'invocation' && value.contract_version !== '0.1') fail('CONTRACT_VERSION_UNSUPPORTED');
    for (const k of ['resource_budget','resource_usage']) if (value[k]) {
      for (const r of Object.values(value[k])) {
        try { validate('vcp','resource',r); } catch { fail(type === 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT'); }
        if (k === 'resource_budget' && (r as WireObject).kind !== 'EXACT') fail('INVALID_INVOCATION');
      }
      if (type === 'invocation' && !value.vcp_version) fail('INVALID_INVOCATION');
    }
  }
}
/** Validate the documented standalone semantic subset; unsupported types fail closed. */
export function validate(contract: string, type: string, value: Json): WireObject {
  validateStructure(contract,type,value);
  if (contract === 'vcp' && !bundle.semantic_vcp_types.includes(type)) fail('SDK_UNSUPPORTED','Only structural validation is implemented for '+type);
  semantics(contract,type,value as WireObject);
  return value as WireObject;
}
export function parse(contract: string, type: string, text: string): WireObject {
  let value: Json;
  try {
    // Syntax is checked by the parser below. This token pass counts every key,
    // including repeated keys with equal values that lossless-json permits.
    const tokens = text.match(/"(?:[^"\\]|\\.)*"|[{}\[\]:,]/g) || [];
    const stack: Set<string>[] = [];
    for (let i=0;i<tokens.length;i++) {
      const token=tokens[i];
      if (token==='{' || token==='[') stack.push(new Set());
      else if (token==='}' || token===']') stack.pop();
      else if (token.startsWith('"') && tokens[i+1]===':') {
        const key=JSON.parse(token) as string;
        if (stack.at(-1)!.has(key)) throw new Error('Duplicate JSON key');
        stack.at(-1)!.add(key);
      }
    }
    parseJson(text, undefined, {parseNumber: (source: string) => {
    if (!isSafeNumber(source)) throw new Error('JSON number cannot be represented faithfully');
    return Number(source);
    }});
    value = JSON.parse(text) as Json;
  } catch (e) { fail(contract === 'vcp' ? 'PROTOCOL_JSON' : type === 'invocation' ? 'INVALID_INVOCATION' : 'INVALID_PROVIDER_OUTPUT', String(e)); }
  return validate(contract,type,value);
}
/** Preserve absence, explicit payload null, and unknown optional extension data. */
export function serialize(value: Json): string {
  const encoded = JSON.stringify(value, (_key, v) => {
    if (typeof v === 'number' && !Number.isFinite(v)) fail('PROTOCOL_JSON');
    if (v === undefined || typeof v === 'bigint' || typeof v === 'function' || typeof v === 'symbol') fail('PROTOCOL_JSON');
    return v;
  });
  if (encoded === undefined) fail('PROTOCOL_JSON');
  return encoded;
}
