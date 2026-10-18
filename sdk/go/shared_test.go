package openverify

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestShared(t *testing.T) {
	root := filepath.Join("..", "..", "conformance", "sdk")
	raw, e := os.ReadFile(filepath.Join(root, "manifest.json"))
	if e != nil {
		t.Fatal(e)
	}
	var manifest struct{ Cases []string }
	if e = json.Unmarshal(raw, &manifest); e != nil {
		t.Fatal(e)
	}
	for _, p := range manifest.Cases {
		raw, e = os.ReadFile(filepath.Join(root, p))
		if e != nil {
			t.Fatal(e)
		}
		v, e := Decode(raw)
		if e != nil {
			t.Fatal(e)
		}
		c := object(v)
		t.Run(c["id"].(string), func(t *testing.T) {
			var result any
			var err error
			if c["operation"] == "data" {
				err = ValidateData(c["schema"], c["input"], "INVALID_INPUT")
				result = c["input"]
			} else {
				b, _ := json.Marshal(c["input"])
				var wire WireObject
				wire, err = Parse(c["contract"].(string), c["type"].(string), b)
				if err == nil {
					b, _ = Serialize(wire)
					result, _ = Decode(b)
				}
			}
			expected := object(c["expected"])
			if expected["accepted"] == true {
				if err != nil {
					t.Fatal(err)
				}
				if !reflect.DeepEqual(result, expected["normalized"]) {
					t.Fatalf("roundtrip mismatch: %v / %v", result, expected["normalized"])
				}
			} else {
				p, ok := err.(*ProtocolError)
				if !ok {
					t.Fatalf("expected protocol error, got %v", err)
				}
				if expected["error"] != "*" && p.Code != expected["error"] {
					t.Fatalf("%s != %s", p.Code, expected["error"])
				}
			}
		})
	}
}
func TestDuplicate(t *testing.T) {
	if _, e := Parse("vcp", "result", []byte(`{"protocol":"draft","protocol":"draft"}`)); e == nil {
		t.Fatal("accepted duplicate")
	}
}
func TestInvalidUTF8(t *testing.T) {
	if _, e := Decode([]byte{'"', 0xff, '"'}); e == nil {
		t.Fatal("invalid UTF-8 accepted")
	}
}
