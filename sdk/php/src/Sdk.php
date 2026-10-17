<?php
declare(strict_types=1);
namespace OpenVerify;
use Opis\JsonSchema\Validator;
final class Sdk {
    public const VERSION = '0.1.0';
    public const VCP_VERSION = 'draft';
    public const PROVIDER_CONTRACT_VERSION = '0.1';
    public const SPEC_REVISION = '5f17f402a270882f244a54dde25eda92a085eb39';
    private static function bundle(): \stdClass {
        static $bundle;
        return $bundle ??= json_decode(file_get_contents(__DIR__.'/../resources/bundle.json'), false, 512, JSON_THROW_ON_ERROR);
    }
    private static function check(mixed $schema, mixed $value, string $code): void {
        $validator = new Validator();
        foreach (['allowFormats','allowFilters','allowMappers','allowTemplates','allowGlobals','allowDefaults','allowSlots','allowKeywordValidators','allowPragmas','allowDataKeyword'] as $option) $validator->parser()->setOption($option,false);
        $validator->parser()->setOption('allowKeywordsAlongsideRef',true);
        foreach (self::bundle()->schemas as $id=>$s) $validator->resolver()->registerRaw($s, $id);
        if (!$validator->validate($value, $schema)->isValid()) throw new ProtocolError($code);
    }
    public static function validateStructure(string $contract, string $type, mixed $value): void {
        $prefix = match($contract) {'vcp'=>'urn:verification:draft:', 'provider'=>'urn:openverify:provider:0.1:', default=>throw new ProtocolError('SDK_UNSUPPORTED')};
        $schema = self::bundle()->schemas->{$prefix.$type} ?? throw new ProtocolError('SDK_UNSUPPORTED');
        if ($contract==='vcp' && is_object($value) && property_exists($value,'protocol') && $value->protocol!=='draft') throw new ProtocolError('PROTOCOL_VERSION');
        if ($contract==='provider' && $type==='invocation' && is_object($value) && property_exists($value,'contract_version') && $value->contract_version!=='0.1') throw new ProtocolError('CONTRACT_VERSION_UNSUPPORTED');
        self::check($schema,$value,$contract==='vcp'?'PROTOCOL_STRUCTURE':($type==='invocation'?'INVALID_INVOCATION':'INVALID_PROVIDER_OUTPUT'));
    }
    public static function validateData(mixed $schema, mixed $value, string $code='INVALID_INPUT'): void {
        $positions=[]; $refs=[];
        $visit = function(mixed $s, string $path, bool $top) use (&$visit,&$positions,&$refs): void {
            $positions[$path]=true;
            if (is_bool($s)) return;
            if (!is_object($s)) throw new ProtocolError('INVALID_PROVIDER_OUTPUT');
            if ((!$top && property_exists($s,'$id')) || property_exists($s,'$anchor') || property_exists($s,'$dynamicAnchor') || property_exists($s,'$dynamicRef')) throw new ProtocolError('INVALID_PROVIDER_OUTPUT');
            if (property_exists($s,'$schema') && $s->{'$schema'}!=='https://json-schema.org/draft/2020-12/schema') throw new ProtocolError('INVALID_PROVIDER_OUTPUT');
            if (property_exists($s,'$ref')) { $ref=$s->{'$ref'}; if (!is_string($ref)||($ref!=='#'&&!str_starts_with($ref,'#/'))) throw new ProtocolError('INVALID_PROVIDER_OUTPUT'); $refs[]=substr($ref,1); }
            foreach (['properties','patternProperties','$defs','dependentSchemas'] as $k) foreach (($s->$k??new \stdClass) as $name=>$v) $visit($v,$path.'/'.$k.'/'.str_replace(['~','/'],['~0','~1'],(string)$name),false);
            foreach (['additionalProperties','unevaluatedProperties','propertyNames','contains','items','unevaluatedItems','not','if','then','else','contentSchema'] as $k) if (property_exists($s,$k)) $visit($s->$k,$path.'/'.$k,false);
            foreach (['allOf','anyOf','oneOf','prefixItems'] as $k) foreach (($s->$k??[]) as $n=>$v) $visit($v,$path.'/'.$k.'/'.$n,false);
        };
        $visit($schema,'',true);
        foreach ($refs as $r) if (!isset($positions[$r])) throw new ProtocolError('INVALID_PROVIDER_OUTPUT');
        self::check(self::bundle()->meta,$schema,'INVALID_PROVIDER_OUTPUT');
        self::check($schema,$value,$code);
    }
    public static function validate(string $contract, string $type, mixed $value): WireObject {
        self::validateStructure($contract,$type,$value);
        if ($contract==='vcp' && !in_array($type,self::bundle()->semantic_vcp_types,true)) throw new ProtocolError('SDK_UNSUPPORTED');
        foreach ((self::bundle()->rules->$type??[]) as $r) self::check($r->schema,$value,$contract==='provider'?'INVALID_PROVIDER_OUTPUT':$r->code);
        if ($type==='resource' && $value->kind==='RANGE' && $value->minimum>$value->maximum) throw new ProtocolError('RESOURCE_MEASUREMENT');
        if ($contract==='vcp') {
            foreach (['extensions'=>'extension','evidence'=>'evidence'] as $k=>$target) foreach (($value->$k??[]) as $v) self::validate('vcp',$target,$v);
            if (isset($value->artifact_ref)) self::validate('vcp','artifact-ref',$value->artifact_ref);
            foreach (($value->usage??new \stdClass) as $v) self::validate('vcp','resource',$v);
        } else {
            if (property_exists($value,'deadline')||property_exists($value,'timestamp')) throw new ProtocolError('SDK_UNSUPPORTED');
            if ($type==='provider-event') {
                try {
                    $target=['evidence'=>'evidence','artifact'=>'artifact-ref'][$value->kind]??null;
                    if ($target) self::validate('vcp',$target,$value->payload);
                    if ($value->kind==='resource_usage') foreach ($value->payload as $r) self::validate('vcp','resource',$r);
                } catch(ProtocolError $e) {throw new ProtocolError('INVALID_PROVIDER_OUTPUT');}
            }
            if ($type==='provider-manifest') {
                $seen=[];
                foreach ($value->capabilities as $c) {
                    $key=json_encode([$c->capability_id,$c->capability_version]);
                    if (isset($seen[$key])) throw new ProtocolError('INVALID_PROVIDER_OUTPUT');
                    $seen[$key]=true;
                    if (isset($c->vcp_version) && !in_array($c->vcp_version,$value->supported_vcp_versions,true)) throw new ProtocolError('INVALID_PROVIDER_OUTPUT');
                    self::validate('provider','capability',$c);
                }
            }
            if ($type==='capability') foreach (['input_schema','config_schema','output_schema'] as $k) {
                try {self::validateData($value->$k,null);} catch(ProtocolError $e) {if ($e->errorCode!=='INVALID_INPUT') throw $e;}
            }
            if ($type==='initialize-result') self::validate('provider','provider-manifest',$value->manifest);
            if (isset($value->vcp_version) && $value->vcp_version!=='draft') throw new ProtocolError($type==='invocation'?'INVALID_INVOCATION':'INVALID_PROVIDER_OUTPUT');
            foreach (['resource_budget','resource_usage'] as $k) foreach (($value->$k??new \stdClass) as $r) {
                try {self::validate('vcp','resource',$r);} catch(ProtocolError $e) {throw new ProtocolError($type==='invocation'?'INVALID_INVOCATION':'INVALID_PROVIDER_OUTPUT');}
                if ($k==='resource_budget' && ($r->kind!=='EXACT'||($value->vcp_version??null)!=='draft')) throw new ProtocolError('INVALID_INVOCATION');
            }
        }
        return new WireObject($value);
    }
    public static function parse(string $contract,string $type,string $text): WireObject {
        try {
            $value=json_decode($text,false,512,JSON_THROW_ON_ERROR);
            // The native decoder validates syntax; this token pass detects duplicate keys.
            preg_match_all('/"(?:[^"\\\\]|\\\\.)*"|-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|[{}\\[\\]:,]/s',$text,$matches);
            $tokens=$matches[0];$stack=[];
            foreach ($tokens as $i=>$token) {
                if (preg_match('/^-?[0-9]/',$token)) {
                    $native=json_decode($token,false,512,JSON_THROW_ON_ERROR);
                    if (!is_finite((float)$native) || self::decimal($token)!==self::decimal(json_encode($native,JSON_THROW_ON_ERROR|JSON_PRESERVE_ZERO_FRACTION))) throw new \JsonException('JSON number cannot be represented faithfully');
                }
                if ($token==='{'||$token==='[') $stack[]=[];
                elseif ($token==='}'||$token===']') array_pop($stack);
                elseif (str_starts_with($token,'"') && ($tokens[$i+1]??null)===':') {
                    $key=json_decode($token,false,512,JSON_THROW_ON_ERROR);$n=count($stack)-1;
                    if (array_key_exists($key,$stack[$n])) throw new \JsonException('duplicate key');
                    $stack[$n][$key]=true;
                }
            }
        } catch(\JsonException $e) {throw new ProtocolError($contract==='vcp'?'PROTOCOL_JSON':($type==='invocation'?'INVALID_INVOCATION':'INVALID_PROVIDER_OUTPUT'),$e->getMessage());}
        return self::validate($contract,$type,$value);
    }
    public static function serialize(WireObject $value): string {return json_encode($value,JSON_THROW_ON_ERROR|JSON_PRESERVE_ZERO_FRACTION|JSON_UNESCAPED_UNICODE);}
    private static function decimal(string $number): string {
        preg_match('/^(-?)([0-9]+)(?:\\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/',$number,$m);
        $fraction=$m[3]??'';$digits=ltrim($m[2].$fraction,'0');
        if ($digits==='') return '0';
        $exponent=(int)($m[4]??'0')-strlen($fraction);
        $trimmed=rtrim($digits,'0');$exponent+=strlen($digits)-strlen($trimmed);
        return $m[1].$trimmed.'e'.$exponent;
    }
}
