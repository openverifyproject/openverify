//! Offline wire validation for a documented subset of the OpenVerify draft.
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{collections::HashSet, sync::LazyLock};
pub const SDK_VERSION: &str = env!("CARGO_PKG_VERSION");
pub const VCP_VERSION: &str = "draft";
pub const PROVIDER_CONTRACT_VERSION: &str = "0.1";
pub const SPEC_REVISION: &str = "5f17f402a270882f244a54dde25eda92a085eb39";
static BUNDLE: LazyLock<Value> =
    LazyLock::new(|| serde_json::from_str(include_str!("../schemas/bundle.json")).unwrap());
/// A wire value preserves absent fields, explicit payload null and extensions.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(transparent)]
pub struct WireObject(pub serde_json::Map<String, Value>);
/// Stable protocol code and an informative message. SDK_UNSUPPORTED is local.
#[derive(Debug, Clone)]
pub struct ProtocolError {
    pub code: String,
    pub message: String,
    pub path: String,
}
impl std::fmt::Display for ProtocolError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}
impl std::error::Error for ProtocolError {}
fn err(code: &str) -> ProtocolError {
    ProtocolError {
        code: code.into(),
        message: code.into(),
        path: String::new(),
    }
}
fn check(schema: &Value, value: &Value, code: &str) -> Result<(), ProtocolError> {
    let mut local = BUNDLE["compound"].clone();
    if let Some(id) = schema.get("$id").and_then(Value::as_str) {
        if BUNDLE["schemas"].get(id).is_some() {
            local["$ref"] = Value::String(format!("#/$defs/{id}"));
        } else {
            local = schema.clone();
        }
    } else {
        local = schema.clone();
    }
    let validator = jsonschema::draft202012::options()
        .should_validate_formats(false)
        .build(&local)
        .map_err(|e| ProtocolError {
            code: "INVALID_PROVIDER_OUTPUT".into(),
            message: e.to_string(),
            path: String::new(),
        })?;
    if validator.is_valid(value) {
        Ok(())
    } else {
        Err(err(code))
    }
}
/// Schema validation only, with all references resolved from bundled resources.
pub fn validate_structure(contract: &str, kind: &str, value: &Value) -> Result<(), ProtocolError> {
    let prefix = match contract {
        "vcp" => "urn:verification:draft:",
        "provider" => "urn:openverify:provider:0.1:",
        _ => return Err(err("SDK_UNSUPPORTED")),
    };
    let schema = &BUNDLE["schemas"][format!("{prefix}{kind}")];
    if schema.is_null() {
        return Err(err("SDK_UNSUPPORTED"));
    }
    if contract == "vcp" && value.get("protocol").is_some_and(|p| p != "draft") {
        return Err(err("PROTOCOL_VERSION"));
    }
    if contract == "provider"
        && kind == "invocation"
        && value.get("contract_version").is_some_and(|v| v != "0.1")
    {
        return Err(err("CONTRACT_VERSION_UNSUPPORTED"));
    }
    check(
        schema,
        value,
        if contract == "vcp" {
            "PROTOCOL_STRUCTURE"
        } else if kind == "invocation" {
            "INVALID_INVOCATION"
        } else {
            "INVALID_PROVIDER_OUTPUT"
        },
    )
}
/// Validate a self-contained Draft 2020-12 input/config/output schema.
pub fn validate_data(schema: &Value, value: &Value, code: &str) -> Result<(), ProtocolError> {
    fn walk(
        s: &Value,
        top: bool,
        root: &Value,
        positions: &mut HashSet<String>,
        refs: &mut Vec<String>,
        path: String,
    ) -> Result<(), ProtocolError> {
        if !s.is_object() && !s.is_boolean() {
            return Err(err("INVALID_PROVIDER_OUTPUT"));
        }
        positions.insert(path.clone());
        if s.is_boolean() {
            return Ok(());
        }
        if (!top && s.get("$id").is_some())
            || ["$anchor", "$dynamicAnchor", "$dynamicRef"]
                .iter()
                .any(|k| s.get(k).is_some())
        {
            return Err(err("INVALID_PROVIDER_OUTPUT"));
        }
        if s.get("$schema")
            .is_some_and(|x| x != "https://json-schema.org/draft/2020-12/schema")
        {
            return Err(err("INVALID_PROVIDER_OUTPUT"));
        }
        if let Some(r) = s.get("$ref") {
            let r = r.as_str().ok_or_else(|| err("INVALID_PROVIDER_OUTPUT"))?;
            if r != "#" && !r.starts_with("#/") {
                return Err(err("INVALID_PROVIDER_OUTPUT"));
            }
            refs.push(r[1..].into());
        }
        for k in [
            "properties",
            "patternProperties",
            "$defs",
            "dependentSchemas",
        ] {
            if let Some(m) = s.get(k).and_then(Value::as_object) {
                for (n, v) in m {
                    walk(
                        v,
                        false,
                        root,
                        positions,
                        refs,
                        format!("{path}/{k}/{}", n.replace('~', "~0").replace('/', "~1")),
                    )?;
                }
            }
        }
        for k in [
            "additionalProperties",
            "unevaluatedProperties",
            "propertyNames",
            "contains",
            "items",
            "unevaluatedItems",
            "not",
            "if",
            "then",
            "else",
            "contentSchema",
        ] {
            if let Some(v) = s.get(k) {
                walk(v, false, root, positions, refs, format!("{path}/{k}"))?;
            }
        }
        for k in ["allOf", "anyOf", "oneOf", "prefixItems"] {
            if let Some(a) = s.get(k).and_then(Value::as_array) {
                for (n, v) in a.iter().enumerate() {
                    walk(v, false, root, positions, refs, format!("{path}/{k}/{n}"))?;
                }
            }
        }
        Ok(())
    }
    let mut positions = HashSet::new();
    let mut refs = Vec::new();
    walk(
        schema,
        true,
        schema,
        &mut positions,
        &mut refs,
        String::new(),
    )?;
    for r in refs {
        if !positions.contains(&r) || schema.pointer(&r).is_none() {
            return Err(err("INVALID_PROVIDER_OUTPUT"));
        }
    }
    let validator = jsonschema::draft202012::options()
        .should_validate_formats(false)
        .build(schema)
        .map_err(|_| err("INVALID_PROVIDER_OUTPUT"))?;
    if validator.is_valid(value) {
        Ok(())
    } else {
        Err(err(code))
    }
}
/// Validate the standalone semantic subset. Graph/provenance semantics fail closed.
pub fn validate(contract: &str, kind: &str, value: &Value) -> Result<(), ProtocolError> {
    validate_structure(contract, kind, value)?;
    if contract == "vcp"
        && !BUNDLE["semantic_vcp_types"]
            .as_array()
            .unwrap()
            .iter()
            .any(|s| s == kind)
    {
        return Err(err("SDK_UNSUPPORTED"));
    }
    if let Some(rules) = BUNDLE["rules"][kind].as_array() {
        for r in rules {
            check(
                &r["schema"],
                value,
                if contract == "provider" {
                    "INVALID_PROVIDER_OUTPUT"
                } else {
                    r["code"].as_str().unwrap()
                },
            )?;
        }
    }
    if kind == "resource" && value["kind"] == "RANGE" {
        check(
            &serde_json::json!({"minimum":value["minimum"]}),
            &value["maximum"],
            "RESOURCE_MEASUREMENT",
        )?;
    }
    if contract == "vcp" {
        for (key, target) in [("extensions", "extension"), ("evidence", "evidence")] {
            if let Some(items) = value[key].as_array() {
                for item in items {
                    validate("vcp", target, item)?;
                }
            }
        }
        if !value["artifact_ref"].is_null() {
            validate("vcp", "artifact-ref", &value["artifact_ref"])?;
        }
        if let Some(items) = value["usage"].as_object() {
            for item in items.values() {
                validate("vcp", "resource", item)?;
            }
        }
    } else {
        if value.get("deadline").is_some() || value.get("timestamp").is_some() {
            return Err(err("SDK_UNSUPPORTED"));
        }
        if kind == "provider-event" {
            match value["kind"].as_str() {
                Some("evidence") => validate("vcp", "evidence", &value["payload"])
                    .map_err(|_| err("INVALID_PROVIDER_OUTPUT"))?,
                Some("artifact") => validate("vcp", "artifact-ref", &value["payload"])
                    .map_err(|_| err("INVALID_PROVIDER_OUTPUT"))?,
                Some("resource_usage") => {
                    for r in value["payload"].as_object().unwrap().values() {
                        validate("vcp", "resource", r)
                            .map_err(|_| err("INVALID_PROVIDER_OUTPUT"))?;
                    }
                }
                _ => {}
            }
        }
        if kind == "provider-manifest" {
            let mut seen = HashSet::new();
            for c in value["capabilities"].as_array().unwrap() {
                if !seen.insert((c["capability_id"].clone(), c["capability_version"].clone())) {
                    return Err(err("INVALID_PROVIDER_OUTPUT"));
                }
                if c.get("vcp_version").is_some_and(|v| {
                    !value["supported_vcp_versions"]
                        .as_array()
                        .unwrap()
                        .contains(v)
                }) {
                    return Err(err("INVALID_PROVIDER_OUTPUT"));
                }
                validate("provider", "capability", c)?;
            }
        }
        if kind == "capability" {
            for k in ["input_schema", "output_schema", "config_schema"] {
                if let Err(e) = validate_data(&value[k], &Value::Null, "INVALID_INPUT") {
                    if e.code != "INVALID_INPUT" {
                        return Err(e);
                    }
                }
            }
        }
        if kind == "initialize-result" {
            validate("provider", "provider-manifest", &value["manifest"])?;
        }
        if value.get("vcp_version").is_some_and(|v| v != "draft") {
            return Err(err(if kind == "invocation" {
                "INVALID_INVOCATION"
            } else {
                "INVALID_PROVIDER_OUTPUT"
            }));
        }
        for k in ["resource_budget", "resource_usage"] {
            if let Some(items) = value[k].as_object() {
                for r in items.values() {
                    validate("vcp", "resource", r).map_err(|_| {
                        err(if kind == "invocation" {
                            "INVALID_INVOCATION"
                        } else {
                            "INVALID_PROVIDER_OUTPUT"
                        })
                    })?;
                    if k == "resource_budget"
                        && (r["kind"] != "EXACT" || value["vcp_version"] != "draft")
                    {
                        return Err(err("INVALID_INVOCATION"));
                    }
                }
            }
        }
    }
    Ok(())
}
/// Parse JSON and validate. Duplicate object keys are rejected before serde mapping.
pub fn parse(contract: &str, kind: &str, text: &str) -> Result<WireObject, ProtocolError> {
    // Deserialize through a visitor to retain duplicate-key detection at every depth.
    struct Strict(Value);
    impl<'de> Deserialize<'de> for Strict {
        fn deserialize<D: serde::Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
            struct Visitor;
            impl<'de> serde::de::Visitor<'de> for Visitor {
                type Value = Strict;
                fn expecting(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
                    write!(f, "JSON")
                }
                fn visit_bool<E: serde::de::Error>(self, v: bool) -> Result<Strict, E> {
                    Ok(Strict(v.into()))
                }
                fn visit_i64<E: serde::de::Error>(self, v: i64) -> Result<Strict, E> {
                    Ok(Strict(v.into()))
                }
                fn visit_u64<E: serde::de::Error>(self, v: u64) -> Result<Strict, E> {
                    Ok(Strict(v.into()))
                }
                fn visit_f64<E: serde::de::Error>(self, v: f64) -> Result<Strict, E> {
                    serde_json::Number::from_f64(v)
                        .map(|n| Strict(n.into()))
                        .ok_or_else(|| E::custom("nonfinite"))
                }
                fn visit_str<E: serde::de::Error>(self, v: &str) -> Result<Strict, E> {
                    Ok(Strict(v.into()))
                }
                fn visit_string<E: serde::de::Error>(self, v: String) -> Result<Strict, E> {
                    Ok(Strict(v.into()))
                }
                fn visit_unit<E: serde::de::Error>(self) -> Result<Strict, E> {
                    Ok(Strict(Value::Null))
                }
                fn visit_seq<A: serde::de::SeqAccess<'de>>(
                    self,
                    mut a: A,
                ) -> Result<Strict, A::Error> {
                    let mut v = Vec::new();
                    while let Some(Strict(x)) = a.next_element()? {
                        v.push(x);
                    }
                    Ok(Strict(v.into()))
                }
                fn visit_map<A: serde::de::MapAccess<'de>>(
                    self,
                    mut a: A,
                ) -> Result<Strict, A::Error> {
                    let mut v = serde_json::Map::new();
                    while let Some(k) = a.next_key::<String>()? {
                        if v.contains_key(&k) {
                            return Err(serde::de::Error::custom("duplicate key"));
                        }
                        let Strict(x) = a.next_value()?;
                        v.insert(k, x);
                    }
                    Ok(Strict(v.into()))
                }
            }
            d.deserialize_any(Visitor)
        }
    }
    let code = if contract == "vcp" {
        "PROTOCOL_JSON"
    } else if kind == "invocation" {
        "INVALID_INVOCATION"
    } else {
        "INVALID_PROVIDER_OUTPUT"
    };
    let Strict(_) = serde_json::from_str::<Strict>(text).map_err(|_| err(code))?;
    let value: Value = serde_json::from_str(text).map_err(|_| err(code))?;
    validate(contract, kind, &value)?;
    Ok(WireObject(value.as_object().unwrap().clone()))
}
/// Wire serialization makes no canonical hashing claim.
pub fn serialize(value: &WireObject) -> Result<String, ProtocolError> {
    serde_json::to_string(value).map_err(|_| err("PROTOCOL_JSON"))
}
