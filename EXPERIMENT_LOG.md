# Experiment log

All experiments: Gemma 4 12B (`gemma-4-12b-it-qat-w4a16-ct`), 4x L4, Kaggle notebook, starter's pinned image, `subprocess` sandbox,
same 20 sound tasks (`findings/baseline_tasks_20.txt`), budget 5 min / 40 tool calls / 80 turns per task.
Each experiment is generated from `experiments/<name>.json` merged onto `experiments/best.json` by `notebooks/make_exp.py`
(the merged config is saved as `notebooks/<name>/resolved_spec.json`). One change per experiment, measured against the base.

Vacuous task: `fastapi_14851` passes with no patch and is excluded from adjusted scores (`findings/vacuous_task_ids.txt`; `scripts/compare.py` prints the adjusted score). Valid sound set = 51 tasks; valid 20-sample = 19 tasks.

Reading the numbers: n = 19-20, so one task = ~5 points. Differences under ~15 points are within noise. Failure causes are the
more informative signal. Never compare these 20-task numbers with the leaderboard.

## Reference points

| Version | Resolved | Notes |
|---|---|---|
| Baseline (unmodified sample) | 3/20 | 8 context-window errors, 5 timeouts, 3 tool-budget, 1 patch failed; 9 empty patches |
| Exp 1: `max_output_tokens` 16384 -> 8192 (= current best config `experiments/best.json`) | 3/20 | 0 context errors, 11 timeouts, 4 tool-budget, 2 patch failed; 6 empty patches |
| Exp 2: thinking_budget 4096 -> 1024 (rejected) | 2/20 | 9 timeouts, 9 tool-budget, 0 patch-failed; 12 empty patches |
| Exp 6: repair procedure prompt (keep) | 5/20 raw, **5/19 adjusted** | 10 timeouts, 4 tool-budget, 1 patch-failed; 10 empty patches |
| Exp 5: per-repo cheat sheets (inconclusive) | 4/20 raw, 4/19 adjusted | 11 timeouts, 3 tool-budget, 2 patch-failed; 8 empty patches |
| Exp 4: sandbox-gap prompt (keep) | 6/20 raw, **5/19 adjusted** | 7 timeouts, 4 tool-budget, 3 patch-failed; 8 empty patches |
| Exp 3: brief-reasoning prompt (provisional keep) | 5/20 raw, **4/19 adjusted** | 8 timeouts, 4 tool-budget, 3 patch-failed; 10 empty patches; `fastapi_14851` gain is vacuous |

## Exp 1: cap max_output_tokens
- Objective: remove `ContextWindowExceededError` (16384 requested output + >16.4k prompt > 32768 context).
- Change: `configs/sampling.yaml` `max_output_tokens: 16384 -> 8192`. Only change.
- Result: 3/20 (baseline 3/20). Context errors 8 -> 0. Gained `fastapi_14873`, lost `rich_2725` (ran out of time with a 41k-char patch).
- Cost: ~3.2 GPU-h. Decision: RETAIN (removes a known failure; no downside). Time is now the binding limit.
- Artifacts: `notebooks/exp01/`, `findings/exp01_results.csv`, Kaggle `bellosashmed/gemma-4-exp01-max-output`.

## Exp 2: lower thinking_budget  (DONE, REJECTED)
- Objective: reduce time spent reasoning per step (time was the binding limit).
- Change: `thinking_config.thinking_budget 4096 -> 1024` (on top of best). Only change.
- Result: **2/20** (best 3/20). Lost `fastapi_14873`, gained nothing. Empty patches 6 -> 12; tool-budget exhaustion 4 -> 9 tasks;
  timeouts 11 -> 9; mean tool calls 28.1 -> 36.1; mean 246 s/task.
- Reading: with less room to think the agent explores more and plans less, burning the 40-call budget without producing a patch.
  Thinking is not what is wasting the time; unfocused exploration is.
- Decision: REJECT (keep thinking_budget 4096). Cost ~2.2-3 GPU-h.
- Artifacts: `notebooks/exp02_thinking/`, `findings/exp02_results.csv`, Kaggle `bellosashmed/gemma-4-exp02-thinking`.

## Exp 3: prompt for brief reasoning and careful edit_file  (DONE, PROVISIONAL KEEP)
- Change: append a "Working style" section to `prompts/system.md` (short reasoning, small exact `old_string`, confirm edits, minimal diff, scratch files in /tmp). Only change.
- Result: **5/20** (best 3/20). Gained `fastapi_14851`, `rich_2725`; lost none. Failure causes: 8 out of time, 4 out of tool calls, 3 patch submitted/tests failed; 10 empty patches. Mean 251 s, 29.8 tool calls.
- AUDIT RESULT: `fastapi_14851` passes with an EMPTY patch (vacuous, exit 0), so its 'resolved' is not real. The empty-patch audit (`notebooks/empty_control`, `findings/empty_patch_audit.csv`) ran all 52 sound tasks: exactly 1 vacuous, 51 correctly fail. **Adjusted score excluding it: 4/19 vs baseline 3/19** (one real gain, `rich_2725`), within noise.
- Decision: provisional KEEP (prompt-only, no downside observed); re-confirm on the 52-task validation.
- Artifacts: `notebooks/exp03_prompt/`, `findings/exp03_results.csv`, Kaggle `bellosashmed/gemma-4-exp03-prompt`.

## Exp 4: sandbox-gap awareness  (DONE, KEEP)
- Change: append a "Test environment limits" section to `prompts/system.md` (test-only module/network failures are environment limits; do not retry or pip install; verify with a short inline check; never claim an unrun test passed; at most 2 calls on a test that cannot run, then submit). Only change.
- Result: **6/20 raw, 5/19 adjusted** (baseline 3/19). Gained `fastapi_14372`, `rich_2725`, `rich_3718` (+ vacuous `fastapi_14851`); lost `fastapi_14873`. Timeouts 11 -> 7, empty patches 6 -> 8, patch-failed 2 -> 3. Mean 265 s, 30.6 tool calls.
- Decision: KEEP (best single change so far, +2 over baseline on 19 tasks; still within noise for n=19, to be re-confirmed on the 51-task validation).
- Artifacts: `notebooks/exp04_sandbox/`, `findings/exp04_results.csv`, Kaggle `bellosashmed/gemma-4-exp04-sandbox`.

## Exp 5: per-repo cheat sheets  (DONE, INCONCLUSIVE)
- Change: append concise verified per-repo notes (fastapi, rich, requests: where the code lives, test layout, rich exact-output tests, requests httpbin caveat) to the system prompt. Only change.
- Result: **4/20 raw, 4/19 adjusted** (baseline 3/19). Gained `rich_2725`, lost none. Timeouts stayed 11, empty patches 6 -> 8. Mean 283 s, 27.4 tool calls.
- Reading: a one-task gain is within noise. The notes did not reduce exploration time (timeouts unchanged).
- Decision: INCONCLUSIVE; candidate for the combined config only if the combined run shows no harm (ablate if it does).
- Artifacts: `notebooks/exp05_cheatsheets/`, `findings/exp05_results.csv`, Kaggle `bellosashmed/gemma-4-exp05-cheatsheets`.

## Exp 6: structured repair procedure  (DONE, KEEP)
- Change: prompt-level Localize -> Reproduce (script in /tmp) -> Fix -> Verify -> Regression guard (git diff --stat, only intended files) -> Submit, with explicit call budgets per phase and "never claim a check you did not run". Single agent; the multi-agent chain was not tried (re-prompt/restart risk).
- Result: **5/20 raw, 5/19 adjusted** (baseline 3/19). Gained `fastapi_14372`, `rich_2725`, `rich_3718` (the same three as Exp 4); lost `fastapi_14873`. Timeouts 10, tool-budget 4, patch-failed 1; 10 empty patches. Mean 258 s, 28.8 tool calls.
- Tool mix: read_file 292, run_command 208, write_file 42, edit_file 19, search_similar_code 17 (graph share 2.9%, up from 0.5%), submit_patch 4. Note write_file (42) outnumbers edit_file (19).
- Decision: KEEP (ties best). Same gains as Exp 4, so the two prompts may overlap; the combined run will test additivity.
- Artifacts: `notebooks/exp06_pipeline/`, `findings/exp06_results.csv`, Kaggle `bellosashmed/gemma-4-exp06-pipeline`.

## Exp 7: graph-tools-first navigation budget  (RUNNING, launched 2026-10-15)
- Motivation: in exp04 traces the graph tools were 3 of 626 tool calls (0.5%) in 2 of 20 tasks; the agent mostly read files (57%) and ran commands (32%); unresolved tasks averaged 18.8 reads / 1.6 edits vs 15.8 reads / 3.3 edits for resolved.
- Change: append a "Navigation budget" section (first two calls = search_similar_code then get_code_neighbors; <=6 line-range reads before the first edit; first edit by call 15; submit by call 30). Artifacts: `notebooks/exp07_graphfirst/`.

## Exp 8: LoRA fine-tune  (NOT RUN: judged infeasible/unjustified, evidence below)
- Training data: 120 recorded agent runs, 21 valid successes, but only **6 distinct solved tasks** (fastapi_14372, fastapi_14873, rich_2725, rich_3454, rich_3718, rich_3905), **all inside the 20-task evaluation sample**. Training on them would contaminate our only metric, and 6 tasks is far too few to teach anything.
- Collecting more: running the agent on the other ~31 valid sound tasks costs ~5 GPU-h and would yield maybe 3-8 more successes.
- Base mismatch: the served model is the W4A16 compressed-tensors checkpoint (10.3 GB). Standard PEFT cannot train on those quantized weights; a LoRA would have to be trained on the 23.9 GB bf16 base (needs sharding across 4x24 GB L4, hours per run) and then applied to the quantized base at serving time, which changes numerics and may degrade the model.
- Budget: remaining GPU quota is reserved for the combined-config run, the 51-task validation (~8 GPU-h) and a possible regression fix.
- Competition-rule note: distilling trajectories from a stronger paid model was deliberately avoided (reasonable-cost and provider-terms gray area).
- Decision: NOT attempted; fallback = current best prompt-only config (no adapter). Requirement to revisit: >=100 distinct successful trajectories on tasks outside the evaluation sample, plus a validated way to train against the quantized base.

## Calibration submission
- 2026-10-15 00:31:44 UTC: submitted the exp04 configuration (ref 57200006). Purpose: obtain a real leaderboard score to compare with the internal 20-task numbers (they are NOT comparable). Result: see PROJECT_STATUS.md (updated when the score is available).
- Risk noted: the scorer has 12 h for all tasks; our per-task cap is 5 min. If the hidden set were larger than ~140 tasks the tail could be cut off. Observed mean is ~4.4 min/task.
