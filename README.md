# adtech-agents (v0)

A read-only agent that audits AppLovin MAX SDK integrations in iOS apps. It never modifies the
repository, runs builds or changes mediation settings.

The agent (iOS MAX Audit Agent, OpenAI Agents SDK) has three tools:

- `inspect_app_project`: AppLovin pods from each `Podfile` (version constraints exactly as written,
  and whether the `AppLovinSDK` constraint allows the newest release), and per `Info.plist` the SDK
  key, `NSUserTrackingUsageDescription` and SKAdNetwork IDs missing from AppLovin's list.
- `search_code`: line search over project source, skipping `Pods/` and build output.
- `read_file_lines`: numbered lines from one file, inside the repository only.

Before the run, our code (never the model) fetches the newest `AppLovinSDK` version from
CocoaPods trunk and AppLovin's SKAdNetwork IDs; the audit fails if it cannot. Evals use the saved
`tests/evals/reference_data.json` instead, so scores do not move when AppLovin ships a release.

After the run, every cited file and line range is checked against the repository. Findings that
cite nothing real are rejected; findings with some bad citations are marked for manual review.

## Setup

```bash
uv sync
cp .env.example .env    # then set OPENAI_API_KEY
```

## Run

```bash
uv run adtech audit --repo tests/fixtures/ios_swift_max_clean   # prints the report as JSON
uv run adtech eval                     # every case in tests/evals/cases.jsonl; calls the model per case
                                       # results (pass/fail, misses, reports): eval-results/<time>.json
```

To step through in Cursor/VS Code, use the configurations in `.vscode/launch.json` (F5).

## Checks

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

## Layout

```text
src/adtech_agents/
  agents/ios_max_audit_agent.py  the agent: prompt and tool list
  workflows/audit_max_integration_workflow.py  audit_max_integration: run, validate evidence
  tools/inspect_app_project.py Podfile and Info.plist parsing; rejects Unity and oversized projects
  tools/code_search.py       repo walking, path guard, search and line reads
  reference_data.py          newest SDK version and AppLovin SKAdNetwork IDs (fixed URLs)
  rules.py                   rule ids shared by the prompt and the evals
  schemas.py                 pydantic models
  evals.py                   fixture eval runner and scoring
  config.py                  `Config`: settings (API key from the environment, turns, eval suite)
  context.py                 `Context`: config + task manager, created by the CLI and passed down
  cli.py                     `adtech audit` / `adtech eval`
tests/                       unit tests, fixtures/ (generated Xcode projects), evals/
```

## Not in v0

Unity and Android, adapter versions and SKAdNetwork IDs of networks other than AppLovin, choosing
the model, Swift Package Manager installs, documentation lookup, adapter/SDK compatibility checks,
runtime checks (builds, devices), any HTTP API, CI pipelines,
multi-agent orchestration. Agent quality has not been measured
yet: no live eval has been run.
