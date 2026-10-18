# Current Golden command paths

On this v0.3.1 branch, the two entrypoints delegate to
[Golden v0.3.1](../golden_v031/README.md):

```powershell
python -m pytest -q tests/golden_v03/test_contract_structure.py
python -m pytest -q tests/golden_v03/test_master_execution.py
```

The frozen v0.3 release remains in `conformance/golden-v0.3/`. Its original
adapters and documentation are preserved at commit
`a8c91ffe3879e0da495ff5c42b2e27858b122ab5`.
Production and normative specifications are unchanged.
