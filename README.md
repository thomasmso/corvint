# Corvint (adtech-agents v0)

Corvint is an agent that audits AppLovin MAX ad SDK integrations in iOS apps. It reads an app's
`Podfile`, `Info.plist` and Swift or Objective-C source, reports integration defects with file and
line citations (missing mediation adapters, an outdated SDK, ads that are never loaded, missing
delegates, initialization at the wrong time, privacy settings), and, if you agree, opens a GitHub
pull request that adds the missing adapter pods. You talk to it in the terminal with `adtech chat`.

This README gets you from a fresh clone to a running agent and a reproduced evaluation. Sections 1
to 4 are all you need for the audit and the evaluation; section 5 (pull requests) is optional.

## 1. Prerequisites

| Needed for | What |
| --- | --- |
| Everything | macOS or Linux, `git`, [uv](https://docs.astral.sh/uv/) (installs Python 3.12 for you) |
| The agent and the evaluation | An OpenAI API key with access to `gpt-5.6-luna` (the openai-agents default model) |
| Pull requests (optional) | A GitHub account and your own GitHub App (section 5) |
| Build check before pull requests (optional) | macOS with Xcode and CocoaPods (`brew install cocoapods`) |
| Regenerating fixtures (optional, rarely) | XcodeGen (`brew install xcodegen`) |

Install uv if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # or: brew install uv
```

## 2. Install

```bash
git clone https://github.com/thomasmso/corvint.git
cd corvint
uv sync                  # creates .venv with Python 3.12 and every dependency from uv.lock
```

Check that the install works (no API key needed, takes a few seconds):

```bash
uv run pytest
```

All tests should pass. They use fake models and a fake GitHub, so they make no network calls to
OpenAI or GitHub.

## 3. Configure the API key

```bash
cp .env.example .env
```

Open `.env` and set `OPENAI_API_KEY=sk-...`. `adtech` reads `.env` from the directory you run it
in; variables exported in your shell take precedence. `.env` is git-ignored; never commit it.

Optional: set `OPENAI_DEFAULT_MODEL` (in `.env` or your shell) to try another OpenAI model. The
reported results use the default, `gpt-5.6-luna`.

Leave `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY_PATH` empty unless you set up pull requests
(section 5). Tracing to the OpenAI dashboard is off, because traces would contain the audited code.

## 4. Run the agent

### Chat (the main interface)

```bash
uv run adtech chat
```

Corvint asks which project to look at. Give it a local directory or a GitHub URL. To try it
without any app of your own, use one of the test apps in this repository, for example one where the
Google AdMob adapter is missing:

```text
> tests/fixtures/ios_swift_max_network_missing_admob
```

It prints each step while it works ("Reading the Podfile and Info.plist…", "Searching *.swift for
…"), then explains the findings and offers a pull request. Opening one needs section 5; without
it, the agent explains why it can't. Type `exit` or press Ctrl-D to quit. Add `--verbose` to see
every model turn, tool call, token count and HTTP request.

An audit takes about 10 to 20 seconds and a dozen or so model calls.

### One audit, as JSON

```bash
uv run adtech audit --repo tests/fixtures/ios_swift_max_ad_delegate_missing
```

Prints the report: a summary, the findings (rule id, severity, evidence with file and line range),
and any findings the citation check rejected.

## 5. Reproduce the evaluation

The evaluation runs the auditor on every case in `tests/evals/cases.jsonl` and scores its
findings against the expected ones.

```bash
uv run adtech eval
```

**This calls the model for every case and costs money** (50 audits per run, each about a dozen
model calls; the token count of each audit is logged). It takes roughly 10 to 15 minutes. It
prints one row per case and the totals (numbers below are illustrative):

```text
case                                      tp  fp  fn
ios_swift_max_clean                  pass   0   0   0
ios_swift_max_ad_load_missing        FAIL   0   0   1
    missed: MAX-AD-LOAD-MISSING (interstitial)
...
passed=36/50 precision=0.88 recall=0.82 false_positives=5
```

and writes everything (per-case pass/fail, misses, false alarms, each full report) to
`eval-results/<date-time>.json` (git-ignored).

### What the suite contains

- 50 cases, one per generated Xcode test app in `tests/fixtures/` (fixture data: realistic but
  invented apps, never real publisher code). 13 cases are clean apps that must produce no
  findings; the rest each plant one or more defects, in Swift and in Objective-C, including
  larger apps and decoys such as a reload in a function that is never called.
- Each case names the expected findings (rule id, optional subject such as "interstitial", and
  the files a correct citation may point to) and optional acceptable extras.
- Versions and SKAdNetwork IDs come from the saved `tests/evals/reference_data.json`, not the
  live APIs, so a new AppLovin release does not change the scores.

### How it is scored

The grader is code, not an LLM judge (`src/adtech_agents/evals.py`):

1. Before scoring, every cited file and line range is checked against the fixture; findings citing
   nothing real are dropped (`validate_findings` in
   `src/adtech_agents/workflows/audit_max_integration_workflow.py`).
2. A reported finding matches an expected one if the rule id is the same, the expected subject
   appears in its subject, and at least one cited file is an expected file (`_matches`). Line
   numbers and wording are not compared.
3. Each expected finding claims at most one reported finding (true positive) or counts as missed
   (false negative). Leftover findings are false positives unless they match an acceptable extra.
   A case passes with no misses and no false positives.
4. Precision and recall are totals over the suite.

### Matching the numbers in the paper

- **The paper's 49 cases** are all of the current cases except
  `ios_swift_max_network_missing_admob`, which was added afterwards. To compare, leave that row
  out of the totals (the JSON file has per-case `tp`, `fp` and `fn`).
- **Expect noise.** Identical runs of the same prompt differed by up to five passed cases. The paper
  reports three runs per configuration; run `adtech eval` three times and compare means, not
  single runs. For the current prompt (step 5 of the ablation) the three runs passed 36, 37 and
  33 of 49 (precision 0.85, recall 0.80).
- **The ablation** (`tests/evals/ablation.md`) describes each prompt and tool change, the scores
  of its three runs, which cases fail most and the answer leak that was found and fixed. Each
  step was run in a separate copy of the repository; the steps are not separate commits, so only
  the current prompt is reproducible directly from this checkout.

## 6. Optional: pull requests through a GitHub App

Corvint never edits your checkout. To install pods it works in a temporary copy, edits only the
`Podfile` (and, for the AdMob adapter, adds a placeholder `GADApplicationIdentifier` to the app's
`Info.plist`), builds it, and opens a pull request through a GitHub App you own. You need a
repository with an iOS app that uses CocoaPods; the easiest is to fork the test app
[thomasmso/cs329z-test-app](https://github.com/thomasmso/cs329z-test-app), which is missing the
Google adapter.

One-time setup:

1. Create a GitHub App at <https://github.com/settings/apps/new>: any name and homepage URL; under
   Webhook, untick **Active**; Repository permissions: **Contents: Read and write** and **Pull
   requests: Read and write** (Metadata read-only is added automatically); "Only on this
   account".
2. On the app's page, note the **App ID** and click **Generate a private key**. Save the `.pem`
   outside the repository, e.g. `~/.config/corvint/github-app.pem`.
3. Click **Install App** (left menu) and install it only on the repositories it may open pull
   requests in, e.g. your fork of the test app.
4. In `.env`: `GITHUB_APP_ID=<App ID>` and `GITHUB_APP_PRIVATE_KEY_PATH=<path to the .pem>`.

Then either ask for the pull request in the chat (give it your fork's URL), or run it directly:

```bash
uv run adtech install --repo https://github.com/<you>/cs329z-test-app --pod AppLovinMediationGoogleAdapter
```

`--repo` also accepts a local clone whose `origin` is on GitHub. The pull request starts from the
default branch on GitHub, so uncommitted local changes are not included.

The private key and tokens never reach the model. Each run asks GitHub for a one-hour token
limited to that one repository; git gets it through environment variables, not the command line
or `.git/config`.

### Build check

Before each pull request, Corvint runs `pod install` and then `xcodebuild build` of the project's
only scheme for `generic/platform=iOS Simulator`, with code signing off, in the temporary copy.
The pull request states the result:

- **succeeded:** it compiles for the simulator. Nothing was run or tested on a simulator or device.
- **failed:** the pull request is a draft and includes the compiler's error lines.
- **skipped:** Xcode or CocoaPods is not installed, or the project has several `.xcodeproj` files
  or schemes. The pull request says to build it yourself.

The first build of a project downloads and compiles every pod and can take several minutes;
later ones take seconds. A Podfile is Ruby and build phases are scripts, so the build runs the
repository's own code on your machine: only point Corvint at repositories you trust. The build
gets a minimal environment (`PATH`, `HOME`, locale; no API keys or GitHub App settings).

## 7. Troubleshooting

| Message | Fix |
| --- | --- |
| `OPENAI_API_KEY is not set` | Set it in `.env` in the directory you run `adtech` from (section 3). |
| `the GitHub App is not installed on <owner>/<repo>` | Install your app on that repository (section 6, step 3). |
| `401 Bad credentials` from GitHub | Check `GITHUB_APP_ID` and that the `.pem` belongs to that app. |
| `Not built: pod not found on this machine` | Install CocoaPods, or ignore: the pull request opens without the build. |
| `… is a Unity project` or `… is not an iOS project` | The audit handles native iOS apps (an `.xcodeproj` or `Podfile`); Unity, Android and Flutter projects are not supported yet. |

## How it works

Two agents, built on the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python):

- **The chat agent** (`agents/max_chat_agent.py`) talks with the publisher. Its two tools are
  `audit_project`, which runs the auditor (on a temporary clone for GitHub URLs), and
  `install_pods`, which opens the pull request, only for the project it audited last and only
  with pods from a fixed list. Its wording and conversation steps live in
  `prompts/en/chat.toml`; what it may do is enforced in `tools/chat_tools.py`.
- **The auditor** (`agents/ios_max_audit_agent.py`) is read-only and has three tools:
  `inspect_app_project` (AppLovin pods and their version constraints from each `Podfile`, and per
  `Info.plist` the SDK key, tracking description and missing SKAdNetwork IDs),
  `search_code` (line search, skipping `Pods/` and build output) and `read_file_lines`. Findings
  use the rule ids in `rules.py`, which the evaluation shares.

Our code, never the model, fetches the newest `AppLovinSDK` version (CocoaPods trunk), the newest
adapter versions (AppLovin's Integration Manager) and AppLovin's SKAdNetwork IDs before each
audit, and computes the comparisons the model sees. The model never supplies paths outside the
repository, URLs or shell commands, and repository content is treated as untrusted data.

```text
src/adtech_agents/
  cli.py                     `adtech chat` / `audit` / `eval` / `install`
  chat_session.py            ChatSession: one conversation, shared by every interface
  agents/max_chat_agent.py   the chat agent: loads its text, tool list
  prompts/<locale>/chat.toml the chat agent's text (only `en` so far)
  tools/chat_tools.py        audit_project and install_pods, per-conversation state and limits
  agents/ios_max_audit_agent.py  the auditor: prompt and tool list
  workflows/audit_max_integration_workflow.py  run the auditor, validate citations
  tools/inspect_app_project.py Podfile and Info.plist parsing
  tools/code_search.py       repository walking, path guard, search and line reads
  step_logger.py             per-step logs and the readable progress lines
  reference_data.py          newest SDK and adapter versions, SKAdNetwork IDs (fixed URLs)
  project_changes.py         Podfile pod lines and AdMob placeholder: plan, diff, apply
  workflows/install_pods_workflow.py  copy, change, build, pull request
  build_check.py             pod install + xcodebuild for the simulator, minimal environment
  workspace.py               temporary worktree or clone, commit, push
  github_app.py              GitHub App tokens and pull requests
  rules.py                   rule ids shared by the prompt and the evaluation
  evals.py                   evaluation runner and grader
  config.py                  settings (model turns, URLs, timeouts, paths)
tests/
  fixtures/                  generated Xcode test apps (fixture data)
  generate_fixtures.py       regenerates them: uv run python -m tests.generate_fixtures
  evals/                     cases.jsonl, reference_data.json, ablation.md
```

## Development

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

To step through in Cursor or VS Code, use the configurations in `.vscode/launch.json` (F5).

Not in v0: Unity and Android apps, Swift Package Manager installs, adapters other than Google and
Unity Ads, adapter/SDK compatibility checks, running the app on a simulator or device, builds on a
remote runner, Slack, and an evaluation of the chat agent.
