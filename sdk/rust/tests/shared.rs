use verifyanything::{parse, serialize, validate_data};
use serde_json::Value;
#[test]
fn shared_fixtures() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../conformance/sdk");
    let manifest: Value =
        serde_json::from_slice(&std::fs::read(root.join("manifest.json")).unwrap()).unwrap();
    for p in manifest["cases"].as_array().unwrap() {
        let c: Value =
            serde_json::from_slice(&std::fs::read(root.join(p.as_str().unwrap())).unwrap())
                .unwrap();
        let result = if c["operation"] == "data" {
            validate_data(&c["schema"], &c["input"], "INVALID_INPUT").map(|_| c["input"].clone())
        } else {
            parse(
                c["contract"].as_str().unwrap(),
                c["type"].as_str().unwrap(),
                &c["input"].to_string(),
            )
            .map(|v| serde_json::from_str::<Value>(&serialize(&v).unwrap()).unwrap())
        };
        if c["expected"]["accepted"] == true {
            assert_eq!(
                result.unwrap_or_else(|e| panic!("{}: {e}", c["id"])),
                c["expected"]["normalized"],
                "{}",
                c["id"]
            );
        } else {
            let e = result.expect_err(&c["id"].to_string());
            if c["expected"]["error"] != "*" {
                assert_eq!(e.code, c["expected"]["error"], "{}", c["id"]);
            }
        }
    }
}
#[test]
fn duplicates() {
    assert_eq!(
        parse(
            "vcp",
            "result",
            r#"{"protocol":"draft","protocol":"draft"}"#
        )
        .unwrap_err()
        .code,
        "PROTOCOL_JSON"
    );
}
