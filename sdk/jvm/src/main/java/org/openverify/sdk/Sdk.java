package org.openverify.sdk;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.node.*;
import com.networknt.schema.*;
import java.io.*;
import java.util.*;

/** Offline wire validation for the documented standalone semantic subset. */
public final class Sdk {
 /** Independent package version. */ public static final String VERSION="0.1.1";
 /** Revision-sensitive VCP marker. */ public static final String VCP_VERSION="draft";
 /** Provider Contract exact version. */ public static final String PROVIDER_CONTRACT_VERSION="0.1";
 /** Normative source revision. */ public static final String SPEC_REVISION="5f17f402a270882f244a54dde25eda92a085eb39";
 private static final ObjectMapper MAPPER=new ObjectMapper().enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
 private static final JsonNode BUNDLE=load();
 private static final JsonSchemaFactory FACTORY=JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V202012);
 private Sdk(){}
 private static JsonNode load(){try(InputStream s=Sdk.class.getResourceAsStream("/bundle.json")){return MAPPER.readTree(s);}catch(IOException e){throw new ExceptionInInitializerError(e);}}
 // Normalize validation trees to one exact JSON-number representation. Jackson
 // numeric node subtypes otherwise compare 1 and 1.0 as different uniqueItems.
 private static JsonNode numbers(JsonNode n){
  if(n.isNumber())return DecimalNode.valueOf(n.decimalValue().stripTrailingZeros());
  if(n.isObject()){ObjectNode o=JsonNodeFactory.instance.objectNode();n.fields().forEachRemaining(p->o.set(p.getKey(),numbers(p.getValue())));return o;}
  if(n.isArray()){ArrayNode a=JsonNodeFactory.instance.arrayNode();n.forEach(v->a.add(numbers(v)));return a;}
  return n;
 }
 private static void check(JsonNode schema,JsonNode value,String code){if(!FACTORY.getSchema(numbers(schema)).validate(numbers(value)).isEmpty())throw new ProtocolException(code);}
 private static Iterable<JsonNode> items(JsonNode n){return n!=null&&n.isContainerNode()?n:List.of();}
 /** Validate structure only; no graph/provenance semantic claim.
  * @param contract vcp or provider @param type wire object type @param value JSON value */
 public static void validateStructure(String contract,String type,JsonNode value){
  String prefix=switch(contract){case "vcp"->"urn:verification:draft:";case "provider"->"urn:openverify:provider:0.1:";default->throw new ProtocolException("SDK_UNSUPPORTED");};
  String id=prefix+type;if(!BUNDLE.path("schemas").has(id))throw new ProtocolException("SDK_UNSUPPORTED");
  if(contract.equals("vcp")&&value.has("protocol")&&!value.path("protocol").asText().equals("draft"))throw new ProtocolException("PROTOCOL_VERSION");
  if(contract.equals("provider")&&type.equals("invocation")&&value.has("contract_version")&&!value.path("contract_version").asText().equals("0.1"))throw new ProtocolException("CONTRACT_VERSION_UNSUPPORTED");
  ObjectNode schema=BUNDLE.path("compound").deepCopy();schema.put("$ref","#/$defs/"+id);
  check(schema,value,contract.equals("vcp")?"PROTOCOL_STRUCTURE":type.equals("invocation")?"INVALID_INVOCATION":"INVALID_PROVIDER_OUTPUT");
 }
 private static void visit(JsonNode s,String path,boolean top,Set<String> positions,List<String> refs){
  positions.add(path);if(s.isBoolean())return;if(!s.isObject())throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
  if((!top&&s.has("$id"))||s.has("$anchor")||s.has("$dynamicRef")||s.has("$dynamicAnchor"))throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
  if(s.has("$schema")&&!s.path("$schema").asText().equals("https://json-schema.org/draft/2020-12/schema"))throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
  if(s.has("$ref")){String r=s.path("$ref").asText();if(!s.path("$ref").isTextual()||(!r.equals("#")&&!r.startsWith("#/")))throw new ProtocolException("INVALID_PROVIDER_OUTPUT");refs.add(r.substring(1));}
  for(String k:List.of("properties","patternProperties","$defs","dependentSchemas")){var fields=s.path(k).fields();while(fields.hasNext()){var p=fields.next();visit(p.getValue(),path+"/"+k+"/"+p.getKey().replace("~","~0").replace("/","~1"),false,positions,refs);}}
  for(String k:List.of("additionalProperties","unevaluatedProperties","propertyNames","contains","items","unevaluatedItems","not","if","then","else","contentSchema"))if(s.has(k))visit(s.path(k),path+"/"+k,false,positions,refs);
  for(String k:List.of("allOf","anyOf","oneOf","prefixItems")){int n=0;for(JsonNode v:items(s.path(k)))visit(v,path+"/"+k+"/"+n++,false,positions,refs);}
 }
 /** Validate capability input/config/output against a self-contained schema.
  * @param schema Draft 2020-12 schema @param value instance @param code failure code */
 public static void validateData(JsonNode schema,JsonNode value,String code){
  Set<String> positions=new HashSet<>();List<String> refs=new ArrayList<>();visit(schema,"",true,positions,refs);if(refs.stream().anyMatch(r->!positions.contains(r)))throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
  check(BUNDLE.path("meta"),schema,"INVALID_PROVIDER_OUTPUT");
  check(schema,value,code);
 }
 /** Validate standalone semantics, rejecting unsupported semantic object types.
  * @param contract vcp or provider @param type wire object type @param value JSON value @return validated object */
 public static WireObject validate(String contract,String type,JsonNode value){
  validateStructure(contract,type,value);
  if(contract.equals("vcp")){boolean supported=false;for(JsonNode v:BUNDLE.path("semantic_vcp_types"))if(v.asText().equals(type))supported=true;if(!supported)throw new ProtocolException("SDK_UNSUPPORTED");}
  for(JsonNode r:items(BUNDLE.path("rules").path(type)))check(r.path("schema"),value,contract.equals("provider")?"INVALID_PROVIDER_OUTPUT":r.path("code").asText());
  if(type.equals("resource")&&value.path("kind").asText().equals("RANGE")&&value.path("minimum").decimalValue().compareTo(value.path("maximum").decimalValue())>0)throw new ProtocolException("RESOURCE_MEASUREMENT");
  if(contract.equals("vcp")){
   for(JsonNode e:items(value.path("extensions")))validate("vcp","extension",e);
   for(JsonNode e:items(value.path("evidence")))validate("vcp","evidence",e);
   if(value.hasNonNull("artifact_ref"))validate("vcp","artifact-ref",value.path("artifact_ref"));
   for(JsonNode e:items(value.path("usage")))validate("vcp","resource",e);
  }else{
   if(value.has("deadline")||value.has("timestamp"))throw new ProtocolException("SDK_UNSUPPORTED");
   if(type.equals("provider-event")){String target=switch(value.path("kind").asText()){case "evidence"->"evidence";case "artifact"->"artifact-ref";default->"";};try{if(!target.isEmpty())validate("vcp",target,value.path("payload"));if(value.path("kind").asText().equals("resource_usage"))for(JsonNode r:items(value.path("payload")))validate("vcp","resource",r);}catch(ProtocolException e){throw new ProtocolException("INVALID_PROVIDER_OUTPUT");}}
   if(type.equals("provider-manifest")){Set<List<String>> seen=new HashSet<>();for(JsonNode c:value.path("capabilities")){if(!seen.add(List.of(c.path("capability_id").asText(),c.path("capability_version").asText())))throw new ProtocolException("INVALID_PROVIDER_OUTPUT");if(c.has("vcp_version")){boolean found=false;for(JsonNode v:value.path("supported_vcp_versions"))if(v.equals(c.path("vcp_version")))found=true;if(!found)throw new ProtocolException("INVALID_PROVIDER_OUTPUT");}validate("provider","capability",c);}}
   if(type.equals("capability"))for(String k:List.of("input_schema","config_schema","output_schema")){try{validateData(value.path(k),NullNode.instance,"INVALID_INPUT");}catch(ProtocolException e){if(!e.code().equals("INVALID_INPUT"))throw e;}}
   if(type.equals("initialize-result"))validate("provider","provider-manifest",value.path("manifest"));
   if(value.has("vcp_version")&&!value.path("vcp_version").asText().equals("draft"))throw new ProtocolException(type.equals("invocation")?"INVALID_INVOCATION":"INVALID_PROVIDER_OUTPUT");
   for(String k:List.of("resource_budget","resource_usage"))for(JsonNode r:items(value.path(k))){try{validate("vcp","resource",r);}catch(ProtocolException e){throw new ProtocolException(type.equals("invocation")?"INVALID_INVOCATION":"INVALID_PROVIDER_OUTPUT");}if(k.equals("resource_budget")&&(!r.path("kind").asText().equals("EXACT")||!value.path("vcp_version").asText().equals("draft")))throw new ProtocolException("INVALID_INVOCATION");}
  }
  return new WireObject(value.deepCopy());
 }
 /** Parse strict JSON and validate standalone semantics.
  * @param contract vcp or provider @param type wire object type @param text JSON document @return validated wire object */
 public static WireObject parse(String contract,String type,String text){JsonNode value;try{value=MAPPER.readTree(text);if(value==null)throw new IOException("empty JSON");}catch(IOException e){throw new ProtocolException(contract.equals("vcp")?"PROTOCOL_JSON":type.equals("invocation")?"INVALID_INVOCATION":"INVALID_PROVIDER_OUTPUT");}return validate(contract,type,value);}
 /** Serialize preserving JSON values; no canonical bytes claim.
  * @param value wire object @return JSON text */
 public static String serialize(WireObject value){return value.data().toString();}
}
