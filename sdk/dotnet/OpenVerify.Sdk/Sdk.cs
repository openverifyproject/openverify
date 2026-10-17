using System.Text.Json;
using System.Text.Json.Nodes;
using Json.Schema;

namespace OpenVerify;

/// <summary>Protocol failure with stable code and informative message/path.</summary>
public sealed class ProtocolException(string code, string? message = null, string path = "") : Exception(message ?? code)
{
    /// <summary>Normative classification where defined; SDK_UNSUPPORTED is local.</summary>
    public string Code { get; } = code;
    /// <summary>JSON Pointer when available.</summary>
    public string Path { get; } = path;
}
/// <summary>Wire object retaining absent properties and explicit null values.</summary>
public sealed record WireObject(JsonObject Data);
/// <summary>Offline schema and supported standalone semantic validation.</summary>
public static class Sdk
{
    /// <summary>Independent SDK version.</summary>
    public const string Version = "0.1.0";
    /// <summary>Revision-sensitive VCP wire marker.</summary>
    public const string VcpVersion = "draft";
    /// <summary>Provider Contract version.</summary>
    public const string ProviderContractVersion = "0.1";
    /// <summary>Exact normative source revision.</summary>
    public const string SpecRevision = "5f17f402a270882f244a54dde25eda92a085eb39";
    private static readonly JsonObject Bundle = LoadBundle();
    private static JsonObject LoadBundle()
    {
        using var stream = typeof(Sdk).Assembly.GetManifestResourceStream("OpenVerify.bundle.json")!;
        return JsonNode.Parse(stream)!.AsObject();
    }
    private static string? Text(JsonNode? n) => n is JsonValue v && v.TryGetValue<string>(out var s) ? s : null;
    private static IEnumerable<JsonNode?> Array(JsonNode? n) => n is JsonArray a ? a : [];
    private static IEnumerable<JsonNode?> Values(JsonNode? n) => n is JsonObject o ? o.Select(p => p.Value) : [];
    private static void Check(JsonNode? schema, JsonNode? value, string code)
    {
        JsonSchema compiled;
        try { compiled = JsonSchema.FromText(schema?.ToJsonString() ?? "null"); }
        catch(Exception e) { throw new ProtocolException("INVALID_PROVIDER_OUTPUT", e.Message); }
        var result = compiled.Evaluate(value, new EvaluationOptions { EvaluateAs = SpecVersion.Draft202012, RequireFormatValidation = false });
        if (!result.IsValid) throw new ProtocolException(code);
    }
    /// <summary>Structural validity only; no graph/provenance semantic claim.</summary>
    public static void ValidateStructure(string contract, string type, JsonNode? value)
    {
        var prefix = contract switch { "vcp" => "urn:verification:draft:", "provider" => "urn:openverify:provider:0.1:", _ => throw new ProtocolException("SDK_UNSUPPORTED") };
        var id = prefix + type;
        if (Bundle["schemas"]?[id] is null) throw new ProtocolException("SDK_UNSUPPORTED");
        if (contract == "vcp" && value is JsonObject v && v.ContainsKey("protocol") && Text(v["protocol"]) != "draft") throw new ProtocolException("PROTOCOL_VERSION");
        if (contract == "provider" && type == "invocation" && value is JsonObject inv && inv.ContainsKey("contract_version") && Text(inv["contract_version"]) != "0.1") throw new ProtocolException("CONTRACT_VERSION_UNSUPPORTED");
        var schema = Bundle["compound"]!.DeepClone().AsObject();
        schema["$ref"] = "#/$defs/" + id;
        Check(schema, value, contract == "vcp" ? "PROTOCOL_STRUCTURE" : type == "invocation" ? "INVALID_INVOCATION" : "INVALID_PROVIDER_OUTPUT");
    }
    /// <summary>Validate a self-contained Draft 2020-12 input/config/output schema.</summary>
    public static void ValidateData(JsonNode? schema, JsonNode? value, string code = "INVALID_INPUT")
    {
        var positions = new HashSet<string>(); var refs = new List<string>();
        void Visit(JsonNode? s, string path, bool top)
        {
            positions.Add(path);
            if(s is JsonValue b && b.TryGetValue<bool>(out _)) return;
            if(s is not JsonObject o) throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
            if((!top && o.ContainsKey("$id")) || new[]{"$anchor","$dynamicAnchor","$dynamicRef"}.Any(o.ContainsKey)) throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
            if(o.ContainsKey("$schema") && Text(o["$schema"]) != "https://json-schema.org/draft/2020-12/schema") throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
            if(o.ContainsKey("$ref")) { var r = Text(o["$ref"]); if(r is null || (r != "#" && !r.StartsWith("#/", StringComparison.Ordinal))) throw new ProtocolException("INVALID_PROVIDER_OUTPUT"); refs.Add(r[1..]); }
            foreach(var k in new[]{"properties","patternProperties","$defs","dependentSchemas"}) if(o[k] is JsonObject map) foreach(var p in map) Visit(p.Value, path+"/"+k+"/"+p.Key.Replace("~","~0").Replace("/","~1"),false);
            foreach(var k in new[]{"additionalProperties","unevaluatedProperties","propertyNames","contains","items","unevaluatedItems","not","if","then","else","contentSchema"}) if(o.ContainsKey(k)) Visit(o[k],path+"/"+k,false);
            foreach(var k in new[]{"allOf","anyOf","oneOf","prefixItems"}) if(o[k] is JsonArray a) for(int n=0;n<a.Count;n++) Visit(a[n],path+"/"+k+"/"+n,false);
        }
        Visit(schema,"",true);
        if(refs.Any(r=>!positions.Contains(r))) throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
        Check(Bundle["meta"],schema,"INVALID_PROVIDER_OUTPUT");
        Check(schema,value,code);
    }
    /// <summary>Validate the documented semantic subset; unsupported types fail closed.</summary>
    public static WireObject Validate(string contract, string type, JsonNode? value)
    {
        ValidateStructure(contract,type,value);
        if(contract=="vcp" && !Array(Bundle["semantic_vcp_types"]).Any(s=>Text(s)==type)) throw new ProtocolException("SDK_UNSUPPORTED");
        var o=value!.AsObject();
        foreach(var r in Array(Bundle["rules"]?[type])) Check(r!["schema"],o,contract=="provider"?"INVALID_PROVIDER_OUTPUT":Text(r["code"])!);
        if(type=="resource" && Text(o["kind"])=="RANGE") Check(new JsonObject { ["minimum"] = o["minimum"]!.DeepClone() },o["maximum"],"RESOURCE_MEASUREMENT");
        if(contract=="vcp")
        {
            foreach(var e in Array(o["extensions"])) Validate("vcp","extension",e);
            foreach(var e in Array(o["evidence"])) Validate("vcp","evidence",e);
            if(o["artifact_ref"] is not null) Validate("vcp","artifact-ref",o["artifact_ref"]);
            foreach(var e in Values(o["usage"])) Validate("vcp","resource",e);
        }
        else
        {
            if(o.ContainsKey("deadline") || o.ContainsKey("timestamp")) throw new ProtocolException("SDK_UNSUPPORTED");
            if(type=="provider-event")
            {
                try
                {
                    var target = Text(o["kind"]) switch {"evidence"=>"evidence","artifact"=>"artifact-ref",_=>null};
                    if(target is not null) Validate("vcp",target,o["payload"]);
                    if(Text(o["kind"])=="resource_usage") foreach(var r in Values(o["payload"])) Validate("vcp","resource",r);
                }
                catch(ProtocolException){throw new ProtocolException("INVALID_PROVIDER_OUTPUT");}
            }
            if(type=="provider-manifest")
            {
                var seen=new HashSet<(string?,string?)>();
                foreach(var c in Array(o["capabilities"]))
                {
                    if(!seen.Add((Text(c!["capability_id"]),Text(c["capability_version"])))) throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
                    if(c["vcp_version"] is not null && !Array(o["supported_vcp_versions"]).Any(v=>JsonNode.DeepEquals(v,c["vcp_version"]))) throw new ProtocolException("INVALID_PROVIDER_OUTPUT");
                    Validate("provider","capability",c);
                }
            }
            if(type=="capability") foreach(var k in new[]{"input_schema","config_schema","output_schema"}) try{ValidateData(o[k],null);}catch(ProtocolException e) when(e.Code=="INVALID_INPUT"){}
            if(type=="initialize-result") Validate("provider","provider-manifest",o["manifest"]);
            if(o.ContainsKey("vcp_version") && Text(o["vcp_version"])!="draft") throw new ProtocolException(type=="invocation"?"INVALID_INVOCATION":"INVALID_PROVIDER_OUTPUT");
            foreach(var k in new[]{"resource_budget","resource_usage"}) foreach(var r in Values(o[k]))
            {
                try{Validate("vcp","resource",r);}catch(ProtocolException){throw new ProtocolException(type=="invocation"?"INVALID_INVOCATION":"INVALID_PROVIDER_OUTPUT");}
                if(k=="resource_budget" && (Text(r!["kind"])!="EXACT" || Text(o["vcp_version"])!="draft")) throw new ProtocolException("INVALID_INVOCATION");
            }
        }
        return new WireObject((JsonObject)o.DeepClone());
    }
    /// <summary>Parse strict JSON; reject duplicate properties at every depth.</summary>
    public static WireObject Parse(string contract,string type,string text)
    {
        JsonNode? value;
        try
        {
            using var doc=JsonDocument.Parse(text);
            void Visit(JsonElement e)
            {
                if(e.ValueKind==JsonValueKind.Object){var seen=new HashSet<string>();foreach(var p in e.EnumerateObject()){if(!seen.Add(p.Name)) throw new JsonException("Duplicate key");Visit(p.Value);}}
                if(e.ValueKind==JsonValueKind.Array) foreach(var item in e.EnumerateArray()) Visit(item);
            }
            Visit(doc.RootElement);value=JsonNode.Parse(text);
        }
        catch(JsonException e){throw new ProtocolException(contract=="vcp"?"PROTOCOL_JSON":type=="invocation"?"INVALID_INVOCATION":"INVALID_PROVIDER_OUTPUT",e.Message);}
        return Validate(contract,type,value);
    }
    /// <summary>Serialize without inserting defaults or claiming canonical bytes.</summary>
    public static string Serialize(WireObject value)=>value.Data.ToJsonString();
}
