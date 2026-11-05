# Fixtures

Small, syntactically plausible projects used by unit tests and the evaluation suite. Each
directory is scanned as if it were a publisher repository, so **expected outcomes live in
`tests/evals/cases.jsonl`, never inside a fixture** (that would leak answers to the agent).

Pod names, APIs and versions are real (checked against the CocoaPods CDN and the official MAX iOS
integration docs). The versions are plausible project content, not claims about what is current.
Lockfiles are abbreviated (for example, no `SPEC CHECKSUMS` in `Podfile.lock`).

| Fixture | Content | Fixture-defined defect |
| --- | --- | --- |
| `ios_cocoapods_max` | `Podfile` constraints and a `Podfile.lock` with Google and Unity Ads adapters, init in `AppDelegate.swift` | None |

If you edit a fixture, re-check the line numbers referenced in `cases.jsonl` and the tests.
