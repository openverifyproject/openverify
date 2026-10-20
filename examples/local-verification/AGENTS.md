# Local verification workflow

Before committing code, run `openverify code check --staged` and inspect every
Finding. For prose, run `openverify english check --staged`. Stage corrections
and rerun; unstaged corrections do not change the staged verdict. Do not allow
checks to rewrite source or install missing tools during verification.
