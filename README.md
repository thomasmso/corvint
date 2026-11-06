# adtech-agents (v0)

An agent that audits AppLovin MAX SDK integrations in iOS apps, read-only. Separately, `adtech
install` installs or updates the AppLovinSDK and the Google/Unity Ads adapter pods through a GitHub
pull request; it never edits the publisher's checkout, builds, merges or changes mediation settings.
`adtech chat` puts both behind a conversation with the publisher.

The chat agent (MAX Chat Agent) asks for the project (local path or GitHub URL), runs the audit,
explains the findings, recommends the missing adapters or an SDK update, opens the pull request
once the publisher agrees, and asks about ad formats (advice only). It has two tools:
`audit_project` (the auditor below, on a temporary clone for GitHub URLs) and `install_pods` (the
pull request, only for the project it audited). Conversations live in `ChatSession`, shared by
the terminal and, later, Slack.

The auditor (iOS MAX Audit Agent, OpenAI Agents SDK) has three tools:

- `inspect_app_project`: AppLovin pods from each `Podfile` (version constraints exactly as written,
  and whether the `AppLovinSDK` constraint allows the newest release), and per `Info.plist` the SDK
  key, `NSUserTrackingUsageDescription` and SKAdNetwork IDs missing from AppLovin's list.
- `search_code`: line search over project source, skipping `Pods/` and build output.
- `read_file_lines`: numbered lines from one file, inside the repository only.

Before the run, our code (never the model) fetches the newest `AppLovinSDK` version from
CocoaPods trunk, the newest Google and Unity Ads adapter versions from AppLovin's Integration
Manager API, and AppLovin's SKAdNetwork IDs; the audit fails if it cannot. Evals use the saved
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
uv run adtech chat                     # talk with the agent; pull requests need the GitHub App below
uv run adtech audit --repo tests/fixtures/ios_swift_max_clean   # prints the report as JSON
uv run adtech eval                     # every case in tests/evals/cases.jsonl; calls the model per case
                                       # results (pass/fail, misses, reports): eval-results/<time>.json
uv run adtech install --repo <local repo or GitHub URL> --pod AppLovinMediationUnityAdsAdapter
                                       # opens a pull request (needs the GitHub App below)
```

## Pull requests (GitHub App)

`adtech install` (and `install_pods` in the chat) works in a temporary copy: a git worktree of a local repository (whose `origin`
must be on GitHub), or a clone of a GitHub URL, on a new `corvint/install-pods-<time>` branch off
the default branch. It edits the `Podfile` (and, for the AdMob adapter, adds a placeholder
`GADApplicationIdentifier` to the app's `Info.plist` if it has none), commits as the app, pushes
the branch and opens a pull request marked "not built or tested". The copy is then deleted.

One-time setup:

1. Create the app at <https://github.com/settings/apps/new>: any name and homepage URL; under
   Webhook, untick Active; Repository permissions: Contents **Read and write**, Pull requests
   **Read and write** (Metadata read-only is added automatically); "Only on this account".
2. On the app's page, note the App ID and generate a private key. Keep the `.pem` outside the
   repository, e.g. `~/.config/corvint/github-app.pem`.
3. Install the app (Install App, left menu) on the repositories it may open pull requests in.
4. In `.env`: `GITHUB_APP_ID=<App ID>` and `GITHUB_APP_PRIVATE_KEY_PATH=<path to the .pem>`.

The private key and tokens never reach the model. Each run asks GitHub for a one-hour token limited
to the one repository; git receives it through environment variables, not the command line or
`.git/config`.

To step through in Cursor/VS Code, use the configurations in `.vscode/launch.json` (F5).

## Checks

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

## Layout

```text
src/adtech_agents/
  chat_session.py            ChatSession: one conversation, shared by every interface
  agents/max_chat_agent.py   the chat agent: loads its text, tool list
  prompts/<locale>/chat.toml the chat agent's text: instructions, greeting (only `en` so far)
  tools/chat_tools.py        audit_project and install_pods, per-conversation state
  agents/ios_max_audit_agent.py  the auditor: prompt and tool list
  workflows/audit_max_integration_workflow.py  audit_max_integration: run, validate evidence
  tools/inspect_app_project.py Podfile and Info.plist parsing; rejects Unity and oversized projects
  tools/code_search.py       repo walking, path guard, search and line reads
  reference_data.py          newest SDK and adapter versions, AppLovin SKAdNetwork IDs (fixed URLs)
  project_changes.py         Podfile pod lines and AdMob app ID placeholder: plan, diff, apply
  workflows/install_pods_workflow.py  install_pods: workspace, changes, pull request (all interfaces)
  workspace.py               temporary worktree or clone, commit, push, open the pull request
  github_app.py              GitHub App: installation tokens, default branch, pull requests
  rules.py                   rule ids shared by the prompt and the evals
  schemas.py                 pydantic models
  evals.py                   fixture eval runner and scoring
  config.py                  `Config`: settings (API key from the environment, turns, eval suite)
  context.py                 `Context`: config + task manager, created by the CLI and passed down
  cli.py                     `adtech chat` / `audit` / `eval` / `install`
tests/                       unit tests, fixtures/ (generated Xcode projects), evals/
                             (cases.jsonl, ablation.md: eval history per change)
```

## Not in v0

Unity and Android, adapter versions and SKAdNetwork IDs of networks other than AppLovin, choosing
the model, Swift Package Manager installs, documentation lookup, adapter/SDK compatibility checks,
runtime checks (builds, devices), any HTTP API, CI pipelines,
multi-agent orchestration. Eval results so far: `tests/evals/ablation.md`.
