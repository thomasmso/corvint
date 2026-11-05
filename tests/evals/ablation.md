# Eval ablation (2026-11-05, leak-free)

Each step adds one prompt or tool change on top of the previous one. Every step was run three
times on the full 49-case suite with `gpt-5.6-luna` and the reference snapshot, after the answer
leak was removed (see below). Steps ran in separate copies of the repository; results are in
`/tmp/abl2/results/<step>-run<n>.json` (not kept in the repo).

| Step | Change | Passed (3 runs) | Mean passed | Precision | Recall | False positives (mean) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | Baseline | 25, 27, 25 | 25.7 | 0.52 | 0.68 | 27.7 |
| 1 | `search_code` errors on a literal `\|` query with no hits; `regex` docstring | 34, 29, 30 | 31.0 | 0.75 | 0.80 | 12.0 |
| 2 | Plain-identifier search hints, regex escape advice, ground rule 7 (read before reporting missing) | 35, 32, 31 | 32.7 | 0.74 | 0.85 | 13.7 |
| 3 | AD-LOAD-MISSING and LOAD-BEFORE-INIT rule wording | 38, 40, 36 | **38.0** | **0.90** | 0.84 | **4.3** |
| 4 | Per-ad check split into a/b/c (cite the first load's line); check where an optional ad object is assigned | 35, 36, 33 | 34.7 | 0.89 | 0.76 | 4.3 |
| 5 | Objective-C callback names; `didFinishLaunchingWithOptions` hint (current prompt) | 36, 37, 33 | 35.3 | 0.85 | 0.80 | 6.3 |

Precision and recall are means over the three runs. Runs of the same step differ by up to five
cases, so only differences larger than that are worth reading.

## What each change did

- **Step 1 (regex tool error):** +5 cases. At baseline the model searched for
  `MAInterstitialAd|MARewardedAd` literally, got no hits and concluded MAX was absent, which
  produced most of the baseline's false positives (CMP-MISSING 24, SDK-KEY-MISSING 17,
  INIT-MISSING 16 over three runs). INIT-MISSING false positives went from 16 to 0.
- **Step 2 (search hints, rule 7):** recall up a little (0.80 to 0.85), false positives unchanged.
  Within noise for pass rate.
- **Step 3 (rule wording):** the largest single gain, +5 cases and false positives from 13.7 to
  4.3 per run. CMP-MISSING and SDK-KEY-MISSING false positives fell from 15 and 12 to 4 and 2.
  The earlier 21-case, one-run ablation called this step noise; with more cases and repeats it is
  the step that matters most.
- **Step 4 (a/b/c per-ad check, optionals):** a regression of about 3 cases. Precision held, but
  recall fell from 0.84 to 0.76: missed DELEGATE-MISSING went from 5 to 9 and missed
  RELOAD-MISSING from 4 to 9 over three runs. The longer, lettered check seems to make the model
  stop after the first sub-step it can confirm.
- **Step 5 (Objective-C names):** no measurable change from step 4.

**Implication:** the current prompt (step 5) is worse than step 3. Reverting step 4's per-ad
check to the step 3 wording, while keeping step 5's callback names, is the obvious next
experiment. It has not been run.

## Cases that fail most (out of 18 runs, all steps)

| Case | Failed | Typical failure |
| --- | --- | --- |
| `ios_swift_max_ad_load_missing` | 17 | misses the interstitial with no first load |
| `ios_objc_max_ad_load_missing` | 15 | same |
| `ios_swift_max_init_not_at_launch` | 13 | false LOAD-BEFORE-INIT |
| `ios_objc_max_init_not_at_launch` | 13 | same |
| `ios_swift_max_ad_delegate_missing` | 13 | misses the rewarded delegate |
| `ios_objc_max_decoy_dead_reload` | 13 | accepts the reload in a never-called helper |
| `ios_objc_max_ad_reload_missing_on_hide` | 12 | misses the reload, or a false LOAD-BEFORE-INIT on the banner |

All of these are "something is absent" defects, or a check that has to prove a call is never
reached. Defects with a visible wrong value (outdated SDK, empty key, missing plist entries) almost
always pass. The hard clean cases (8) and larger apps (4) rarely fail after step 3, so file count
and unusual-but-correct code are not the problem.

## Answer leak (found and fixed)

Before run `2026-11-05T105150`, `inspect_app_project` returned the repository folder name, so the
model saw fixture names like `ios_swift_max_ad_delegate_missing`. All earlier GPT results (the old
21-case ablation and the first 49-case run) were inflated by it and are not reported here. With the
current prompt, one run went from 42/49 with the leak to 40/49 without it, and recall from 0.95 to
0.86; the drop was concentrated on the delegate and missing-load defects, the same ones that fail
most above. The model was using the name as a hint for defects that are hard to prove absent.

The 40/49 run is the best of four leak-free runs of the current prompt (40, 36, 37, 33; mean 36.5).

## Reference point: Cursor models, blind (49 cases)

One Cursor subagent per case and model, each given the same instructions, rule catalog and
`inspect_app_project` output, and a copy of the fixture in a randomly named folder (no leak). The
subagents searched and read with Cursor's own tools, not `search_code` and `read_file_lines`, and
had no turn limit. Their reports went through the same citation check and scorer. One run per
model.

| Model (in Cursor) | Passed | Precision | Recall | False positives | Failed case |
| --- | --- | --- | --- | --- | --- |
| Claude Opus 5.5 | 49/49 | 1.00 | 1.00 | 0 | none |
| Claude Sonnet 5.5 | 48/49 | 1.00 | 0.98 | 0 | Swift `large_rewarded_reload_missing_on_hide` (summary says the rewarded ad reloads in didHide; it does not) |
| GPT-5.6 Sol | 48/49 | 0.98 | 1.00 | 1 | Objective-C `init_not_at_launch` (extra MAX-OTHER: "repeated SDK initialization") |
| Composer 2.5 | 48/49 | 0.98 | 1.00 | 1 | same case, same extra finding |

Every model in Cursor passed the defects the harness fails most: missing first load, missing
delegate, dead and commented-out code, and the extension Info.plist. The extra finding on
`init_not_at_launch` is arguably real (init runs on every Play tap) but is not in the catalog.

So the suite is solvable as written by every model tried, including a fast one, and the gap is
the harness, not the task: `gpt-5.6-luna` with three tools and a turn limit, against agents with
richer search and reading and no limit. This comparison does not separate the model from the
tools; running another model inside this harness would.
