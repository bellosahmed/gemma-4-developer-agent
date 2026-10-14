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

## Exp 4: sandbox-gap awareness  (RUNNING, launched 2026-10-14)
- Change: append a "Test environment limits" section to `prompts/system.md`.
- Artifacts: `notebooks/exp04_sandbox/` (generated, validated locally).

## Exp 5: per-repo cheat sheets  (RUNNING, launched 2026-10-14)
- Change: append verified per-repo notes (fastapi, rich, requests) to the system prompt. Artifacts: `notebooks/exp05_cheatsheets/`.

## Exp 6-8: not started (6 prepared)
 6 structured Localize->Reproduce->Fix->Verify pipeline; 7 graph-based context / best-of-N; 8 LoRA fine-tune.
