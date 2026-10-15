# Project status

Last updated: 2026-10-14 (UTC). Resume from the "Exact next action" below. Details: `EXPERIMENT_LOG.md`, `README.md`.

## Overall
Gemma 4 Developer Agent (Kaggle). Config-only submission (`submission.zip`: agent.yaml, prompts, skills, optional LoRA).
Final submission deadline 2026-12-02 23:59 UTC; entry/team-merger deadline 2026-11-25. 1 submission/day, 2 final picks.
Keep the GitHub repo PRIVATE (rules: no private sharing; public sharing only on Kaggle).

## Stages
| # | Stage | Status |
|---|---|---|
| 1 | Setup | DONE |
| 2 | Measurement tools (sandbox check, 52 sound tasks, Kaggle notebooks) | DONE |
| 3 | Baseline | DONE: 3/20 |
| 4 | Experiments | IN PROGRESS (4 of 8 done; 5, 6 running) |
| 5 | Validate best on all 52 sound tasks | NOT STARTED |
| 6 | Package and submit | NOT STARTED (no submission made; `kaggle competitions submissions` shows none) |

## Experiments
| # | Experiment | Status | Score (20 tasks) |
|---|---|---|---|
| 0 | Baseline | done | 3/20 |
| 1 | max_output_tokens 8192 | done, retained | 3/20 |
| 2 | thinking_budget 1024 | done, REJECTED | 2/20 |
| 3 | brief-reasoning prompt | done, provisional keep | 5/20 raw; 4/19 adjusted (14851 vacuous) |
| 4 | sandbox-gap prompt | done, KEEP | 6/20 raw; 5/19 adjusted |
| 5 | per-repo cheat sheets | running | - |
| 6 | structured pipeline | running | - |
| 7 | graph context / best-of-N | not started | - |
| 8 | LoRA fine-tune | not started | - |

## Current best configuration
`experiments/best.json` = unmodified sample agent + `max_output_tokens 8192`. Model `gemma-4-12b-it-qat-w4a16-ct`.

## Resources (verified 2026-10-14)
- Kaggle GPU quota: 23.25 h remaining of 30 at the last check before experiments 2-3 (each run ~3.2 h); refills 2026-10-17.
- Leaderboard top (2026-10-14): 0.24. Our internal numbers are on a 20-task sample and are NOT comparable.

## Key artifacts
- Reference-patch check (52 of 129 tasks sound): `findings/sound_task_ids.txt`, `findings/gold_summary.csv`, `notebooks/gold_check_kaggle.*`
- Baseline / experiment notebooks: `notebooks/baseline/`, `notebooks/exp0*/`; generator `notebooks/make_exp.py`, template `notebooks/template/`
- Local venv (not in git): `venv312/`; competition data (not in git): `kaggle-data/`
- Kaggle notebooks (private): `bellosashmed/gemma-4-*`

## Known issues / limitations
- Kaggle token was pasted into chat early on: regenerate it (Settings > API) and replace `~/.kaggle/access_token`.
- Public-set ceiling ~52/129 (40%) because 77 tasks fail even with the reference patch in the CPU environment (missing `inline_snapshot`/`dirty_equals`, Starlette mismatch, 17 unknown). The official scorer's environment may differ.
- 20-task sample is noisy (1 task = 5 points). `fastapi_14851` passes with an empty patch (vacuous): excluded from adjusted scores.

## Exact next action
When experiments 5 and 6 finish finish (the empty-patch audit is DONE: only `fastapi_14851` is vacuous, excluded from adjusted scores): download results (`kaggle kernels output bellosashmed/<name>`), compare with 3/20, record in `EXPERIMENT_LOG.md`. Then build and run a COMBINED config of the retained prompt changes (3, 4, plus 5/6 if they help), then experiment 7 (context) and 8 (LoRA feasibility). Use the 51-task valid sound set (52 minus `fastapi_14851`) for Stage 5.

## Blockers
None.
