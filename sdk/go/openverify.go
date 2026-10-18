// Package openverify validates the documented standalone VCP/Provider wire subset.
package openverify

import (
	"bytes"
	_ "embed"
	"encoding/json"
	"fmt"
	"github.com/dlclark/regexp2"
	"github.com/santhosh-tekuri/jsonschema/v6"
	"io"
	"math/big"
	"strings"
	"unicode/utf8"
)

const SDKVersion = "0.1.0"
const VCPVersion = "draft"
const ProviderContractVersion = "0.1"
const SpecRevision = "5f17f402a270882f244a54dde25eda92a085eb39"

// WireObject preserves absence and explicit JSON null without pointer defaults.
type WireObject map[string]any

// ProtocolError exposes stable classification independently of validator messages.
type ProtocolError struct {
	Code    string
	Message string
	Path    string
}

func (e *ProtocolError) Error() string { return e.Code + ": " + e.Message }
func failure(code string) error        { return &ProtocolError{Code: code, Message: code} }

type offlineLoader struct{}

func (offlineLoader) Load(url string) (any, error) {
	return nil, fmt.Errorf("offline: unknown schema %s", url)
}

type ecmaRegexp regexp2.Regexp

func (r *ecmaRegexp) MatchString(s string) bool {
	ok, e := (*regexp2.Regexp)(r).MatchString(s)
	return e == nil && ok
}
func (r *ecmaRegexp) String() string { return (*regexp2.Regexp)(r).String() }
func ecmaCompile(s string) (jsonschema.Regexp, error) {
	r, e := regexp2.Compile(s, regexp2.ECMAScript)
	return (*ecmaRegexp)(r), e
}

//go:embed bundle.json
var bundleBytes []byte
var bundle map[string]any

func init() {
	if err := json.Unmarshal(bundleBytes, &bundle); err != nil {
		panic(err)
	}
}
func object(v any) map[string]any { m, _ := v.(map[string]any); return m }
func list(v any) []any            { a, _ := v.([]any); return a }
func contains(a any, v any) bool {
	for _, x := range list(a) {
		if x == v {
			return true
		}
	}
	return false
}
func check(schema, value any, code string) error {
	c := jsonschema.NewCompiler()
	c.DefaultDraft(jsonschema.Draft2020)
	c.UseRegexpEngine(ecmaCompile)
	c.UseLoader(offlineLoader{})
	id := "urn:openverify:sdk:validation"
	if m := object(schema); m != nil {
		if own, ok := m["$id"].(string); ok {
			id = own
		}
	}
	if e := c.AddResource(id, schema); e != nil {
		return &ProtocolError{Code: "INVALID_PROVIDER_OUTPUT", Message: e.Error()}
	}
	compiled, e := c.Compile(id)
	if e != nil {
		return &ProtocolError{Code: "INVALID_PROVIDER_OUTPUT", Message: e.Error()}
	}
	if e = compiled.Validate(value); e != nil {
		return failure(code)
	}
	return nil
}

// ValidateStructure performs schema validation only; all resources are offline.
func ValidateStructure(contract, kind string, value any) error {
	prefix := "urn:verification:draft:"
	if contract == "provider" {
		prefix = "urn:openverify:provider:0.1:"
	} else if contract != "vcp" {
		return failure("SDK_UNSUPPORTED")
	}
	schema, ok := object(bundle["schemas"])[prefix+kind]
	if !ok {
		return failure("SDK_UNSUPPORTED")
	}
	m := object(value)
	if p, ok := m["protocol"]; contract == "vcp" && ok && p != "draft" {
		return failure("PROTOCOL_VERSION")
	}
	if v, ok := m["contract_version"]; contract == "provider" && kind == "invocation" && ok && v != "0.1" {
		return failure("CONTRACT_VERSION_UNSUPPORTED")
	}
	code := "PROTOCOL_STRUCTURE"
	if contract == "provider" {
		code = "INVALID_PROVIDER_OUTPUT"
		if kind == "invocation" {
			code = "INVALID_INVOCATION"
		}
	}
	_ = schema
	compound := map[string]any{}
	for k, v := range object(bundle["compound"]) {
		compound[k] = v
	}
	compound["$ref"] = "#/$defs/" + prefix + kind
	return check(compound, value, code)
}

// ValidateData checks a self-contained capability schema and an input/config/output.
func ValidateData(schema, value any, code string) error {
	positions := map[string]bool{}
	refs := []string{}
	var walk func(any, string, bool) error
	walk = func(s any, path string, top bool) error {
		positions[path] = true
		if _, ok := s.(bool); ok {
			return nil
		}
		m := object(s)
		if m == nil {
			return failure("INVALID_PROVIDER_OUTPUT")
		}
		if _, ok := m["$id"]; ok && !top {
			return failure("INVALID_PROVIDER_OUTPUT")
		}
		for _, k := range []string{"$anchor", "$dynamicRef", "$dynamicAnchor"} {
			if _, ok := m[k]; ok {
				return failure("INVALID_PROVIDER_OUTPUT")
			}
		}
		if d, ok := m["$schema"]; ok && d != "https://json-schema.org/draft/2020-12/schema" {
			return failure("INVALID_PROVIDER_OUTPUT")
		}
		if r, ok := m["$ref"]; ok {
			ref, ok := r.(string)
			if !ok || (ref != "#" && !strings.HasPrefix(ref, "#/")) {
				return failure("INVALID_PROVIDER_OUTPUT")
			}
			refs = append(refs, ref[1:])
		}
		for _, k := range []string{"properties", "patternProperties", "$defs", "dependentSchemas"} {
			for name, v := range object(m[k]) {
				name = strings.ReplaceAll(strings.ReplaceAll(name, "~", "~0"), "/", "~1")
				if e := walk(v, path+"/"+k+"/"+name, false); e != nil {
					return e
				}
			}
		}
		for _, k := range []string{"additionalProperties", "unevaluatedProperties", "propertyNames", "contains", "items", "unevaluatedItems", "not", "if", "then", "else", "contentSchema"} {
			if v, ok := m[k]; ok {
				if e := walk(v, path+"/"+k, false); e != nil {
					return e
				}
			}
		}
		for _, k := range []string{"allOf", "anyOf", "oneOf", "prefixItems"} {
			for n, v := range list(m[k]) {
				if e := walk(v, fmt.Sprintf("%s/%s/%d", path, k, n), false); e != nil {
					return e
				}
			}
		}
		return nil
	}
	if e := walk(schema, "", true); e != nil {
		return e
	}
	for _, r := range refs {
		if !positions[r] {
			return failure("INVALID_PROVIDER_OUTPUT")
		}
	}
	return check(schema, value, code)
}

// Validate checks standalone semantics. Unsupported semantic types fail closed.
func Validate(contract, kind string, value any) error {
	if e := ValidateStructure(contract, kind, value); e != nil {
		return e
	}
	if contract == "vcp" && !contains(bundle["semantic_vcp_types"], kind) {
		return failure("SDK_UNSUPPORTED")
	}
	m := object(value)
	for _, r := range list(object(bundle["rules"])[kind]) {
		rule := object(r)
		code := rule["code"].(string)
		if contract == "provider" {
			code = "INVALID_PROVIDER_OUTPUT"
		}
		if e := check(rule["schema"], value, code); e != nil {
			return e
		}
	}
	if kind == "resource" && m["kind"] == "RANGE" {
		a, ok := new(big.Rat).SetString(fmt.Sprint(m["minimum"]))
		if !ok {
			return failure("RESOURCE_MEASUREMENT")
		}
		b, ok := new(big.Rat).SetString(fmt.Sprint(m["maximum"]))
		if !ok || a.Cmp(b) > 0 {
			return failure("RESOURCE_MEASUREMENT")
		}
	}
	if contract == "vcp" {
		for key, target := range map[string]string{"extensions": "extension", "evidence": "evidence"} {
			for _, v := range list(m[key]) {
				if e := Validate("vcp", target, v); e != nil {
					return e
				}
			}
		}
		if m["artifact_ref"] != nil {
			if e := Validate("vcp", "artifact-ref", m["artifact_ref"]); e != nil {
				return e
			}
		}
		for _, v := range object(m["usage"]) {
			if e := Validate("vcp", "resource", v); e != nil {
				return e
			}
		}
	} else {
		if _, ok := m["deadline"]; ok {
			return failure("SDK_UNSUPPORTED")
		}
		if _, ok := m["timestamp"]; ok {
			return failure("SDK_UNSUPPORTED")
		}
		if kind == "provider-event" {
			target := ""
			if m["kind"] == "evidence" {
				target = "evidence"
			}
			if m["kind"] == "artifact" {
				target = "artifact-ref"
			}
			if target != "" {
				if e := Validate("vcp", target, m["payload"]); e != nil {
					return failure("INVALID_PROVIDER_OUTPUT")
				}
			}
			if m["kind"] == "resource_usage" {
				for _, r := range object(m["payload"]) {
					if e := Validate("vcp", "resource", r); e != nil {
						return failure("INVALID_PROVIDER_OUTPUT")
					}
				}
			}
		}
		if kind == "provider-manifest" {
			seen := map[string]bool{}
			for _, v := range list(m["capabilities"]) {
				cap := object(v)
				key := fmt.Sprintf("%q/%q", cap["capability_id"], cap["capability_version"])
				if seen[key] {
					return failure("INVALID_PROVIDER_OUTPUT")
				}
				seen[key] = true
				if v, ok := cap["vcp_version"]; ok && !contains(m["supported_vcp_versions"], v) {
					return failure("INVALID_PROVIDER_OUTPUT")
				}
				if e := Validate("provider", "capability", cap); e != nil {
					return e
				}
			}
		}
		if kind == "capability" {
			for _, k := range []string{"input_schema", "config_schema", "output_schema"} {
				if e := ValidateData(m[k], nil, "INVALID_INPUT"); e != nil {
					if p, ok := e.(*ProtocolError); !ok || p.Code != "INVALID_INPUT" {
						return e
					}
				}
			}
		}
		if kind == "initialize-result" {
			if e := Validate("provider", "provider-manifest", m["manifest"]); e != nil {
				return e
			}
		}
		if v, ok := m["vcp_version"]; ok && v != "draft" {
			if kind == "invocation" {
				return failure("INVALID_INVOCATION")
			}
			return failure("INVALID_PROVIDER_OUTPUT")
		}
		for _, k := range []string{"resource_budget", "resource_usage"} {
			for _, r := range object(m[k]) {
				if e := Validate("vcp", "resource", r); e != nil {
					if kind == "invocation" {
						return failure("INVALID_INVOCATION")
					}
					return failure("INVALID_PROVIDER_OUTPUT")
				}
				if k == "resource_budget" && (object(r)["kind"] != "EXACT" || m["vcp_version"] != "draft") {
					return failure("INVALID_INVOCATION")
				}
			}
		}
	}
	return nil
}
func number(v any) (float64, error) {
	if n, ok := v.(json.Number); ok {
		return n.Float64()
	}
	n, ok := v.(float64)
	if !ok {
		return 0, fmt.Errorf("not a number")
	}
	return n, nil
}

// Decode rejects duplicate keys at every nesting level, retaining JSON numbers.
func Decode(text []byte) (any, error) {
	if !utf8.Valid(text) {
		return nil, fmt.Errorf("invalid UTF-8 JSON")
	}
	d := json.NewDecoder(bytes.NewReader(text))
	d.UseNumber()
	var read func() (any, error)
	read = func() (any, error) {
		t, e := d.Token()
		if e != nil {
			return nil, e
		}
		switch t {
		case json.Delim('{'):
			m := map[string]any{}
			for d.More() {
				key, e := d.Token()
				if e != nil {
					return nil, e
				}
				k := key.(string)
				if _, ok := m[k]; ok {
					return nil, fmt.Errorf("duplicate key")
				}
				v, e := read()
				if e != nil {
					return nil, e
				}
				m[k] = v
			}
			_, e = d.Token()
			return m, e
		case json.Delim('['):
			a := []any{}
			for d.More() {
				v, e := read()
				if e != nil {
					return nil, e
				}
				a = append(a, v)
			}
			_, e = d.Token()
			return a, e
		default:
			return t, nil
		}
	}
	v, e := read()
	if e != nil {
		return nil, e
	}
	if _, e = d.Token(); e != io.EOF {
		return nil, fmt.Errorf("trailing JSON")
	}
	return v, nil
}

// Parse decodes and validates a wire object.
func Parse(contract, kind string, text []byte) (WireObject, error) {
	v, e := Decode(text)
	if e != nil {
		code := "PROTOCOL_JSON"
		if contract == "provider" {
			code = "INVALID_PROVIDER_OUTPUT"
			if kind == "invocation" {
				code = "INVALID_INVOCATION"
			}
		}
		return nil, failure(code)
	}
	if e = Validate(contract, kind, v); e != nil {
		return nil, e
	}
	return WireObject(object(v)), nil
}

// Serialize preserves wire values; it does not provide canonical signing bytes.
func Serialize(v WireObject) ([]byte, error) { return json.Marshal(v) }
