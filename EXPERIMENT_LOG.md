# Experiment log

All experiments: Gemma 4 12B (`gemma-4-12b-it-qat-w4a16-ct`), 4x L4, Kaggle notebook, starter's pinned image, `subprocess` sandbox,
same 20 sound tasks (`findings/baseline_tasks_20.txt`), budget 5 min / 40 tool calls / 80 turns per task.
Each experiment is generated from `experiments/<name>.json` merged onto `experiments/best.json` by `notebooks/make_exp.py`
(the merged config is saved as `notebooks/<name>/resolved_spec.json`). One change per experiment, measured against the base.

Reading the numbers: n = 20, so one task = 5 points. Differences under ~15 points are within noise. Failure causes are the
more informative signal. Never compare these 20-task numbers with the leaderboard.

## Reference points

| Version | Resolved | Notes |
|---|---|---|
| Baseline (unmodified sample) | 3/20 | 8 context-window errors, 5 timeouts, 3 tool-budget, 1 patch failed; 9 empty patches |
| Exp 1: `max_output_tokens` 16384 -> 8192 (= current best config `experiments/best.json`) | 3/20 | 0 context errors, 11 timeouts, 4 tool-budget, 2 patch failed; 6 empty patches |

## Exp 1: cap max_output_tokens
- Objective: remove `ContextWindowExceededError` (16384 requested output + >16.4k prompt > 32768 context).
- Change: `configs/sampling.yaml` `max_output_tokens: 16384 -> 8192`. Only change.
- Result: 3/20 (baseline 3/20). Context errors 8 -> 0. Gained `fastapi_14873`, lost `rich_2725` (ran out of time with a 41k-char patch).
- Cost: ~3.2 GPU-h. Decision: RETAIN (removes a known failure; no downside). Time is now the binding limit.
- Artifacts: `notebooks/exp01/`, `findings/exp01_results.csv`, Kaggle `bellosashmed/gemma-4-exp01-max-output`.

## Exp 2: lower thinking_budget  (RUNNING, launched 2026-10-14)
- Objective: reduce time spent reasoning per step (time is the binding limit).
- Change: `thinking_config.thinking_budget 4096 -> 1024` (on top of best). Only change.
- Kaggle: `bellosashmed/gemma-4-exp02-thinking`. Artifacts: `notebooks/exp02_thinking/`.

## Exp 3: prompt for brief reasoning and careful edit_file  (RUNNING, launched 2026-10-14)
- Change: append a "Working style" section to `prompts/system.md` (short reasoning, small exact `old_string`, confirm edits, minimal diff, scratch files in /tmp).
- Kaggle: `bellosashmed/gemma-4-exp03-prompt`. Artifacts: `notebooks/exp03_prompt/`.

## Exp 4: sandbox-gap awareness  (PREPARED, not run)
- Change: append a "Test environment limits" section to `prompts/system.md`.
- Artifacts: `notebooks/exp04_sandbox/` (generated, validated locally).

## Exp 5-8: not started
5 per-repo cheat sheets; 6 structured Localize->Reproduce->Fix->Verify pipeline; 7 graph-based context / best-of-N; 8 LoRA fine-tune.
