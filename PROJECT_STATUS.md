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
| 4 | Experiments | COMPLETE (experiments 1-7 run, 8 judged infeasible, combo02 run); next: Stage 5 validation and further submissions |
| 5 | Validate best on all 52 sound tasks | NOT STARTED |
| 6 | Package and submit | IN PROGRESS: calibration submission made (ref 57200006, PENDING); final package not built |

## Experiments
| # | Experiment | Status | Score (20 tasks) |
|---|---|---|---|
| 0 | Baseline | done | 3/20 |
| 1 | max_output_tokens 8192 | done, retained | 3/20 |
| 2 | thinking_budget 1024 | done, REJECTED | 2/20 |
| 3 | brief-reasoning prompt | done, provisional keep | 5/20 raw; 4/19 adjusted (14851 vacuous) |
| 4 | sandbox-gap prompt | done, KEEP | 6/20 raw; 5/19 adjusted |
| 5 | per-repo cheat sheets | done, inconclusive | 4/20 raw; 4/19 adjusted |
| 6 | structured pipeline (prompt-level) | done, KEEP | 5/20 raw; 5/19 adjusted |
| 7 | graph-tools-first navigation (best-of-N judged infeasible, see log) | done, KEEP (best single) | 6/20 raw; 6/19 adjusted |
| 8 | LoRA fine-tune | NOT RUN: infeasible (6 distinct solved tasks, all in eval sample; quantized-base mismatch); see log | - |

## Current best configuration
`experiments/best.json` = unmodified sample agent + `max_output_tokens 8192` (base). Best single prompt change so far: Exp 7 (6/19). Candidates: Exp 7 (6/19, simple) and combo02 (6/19, all prompts): tie on the 20-task sample; decide by 51-task validation and leaderboard scores. Model `gemma-4-12b-it-qat-w4a16-ct`.

## Kaggle submissions
| Ref | Date (UTC) | Artifact | Status | Public score |
|---|---|---|---|---|
| 57200006 | 2026-10-15 00:31:44 | exp04 config (sample + max_output_tokens 8192 + sandbox-gap prompt), 12B, 5 min/40 calls. zip sha256 d3c61b6e... (`findings/submissions/57200006_exp04_MANIFEST.txt`) | PENDING | - |
Built with `scripts/build_submission.py exp04_sandbox` (runs the notebook's own setup code; verified identical to the Kaggle run's file list/settings). Submit via `kaggle competitions submit gemma-4-developer-agent -f <zip> -m "<msg>"` (file upload route works). 1 submission/day.

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

## Exact next action (resume plan; times are UTC)
State at 2026-10-15 ~04:20: GPU quota 1.01 h left (refills 2026-10-17 00:00); today's submission used; calibration submission 57200006 PENDING.
1. **2026-10-16 >= 00:07 (submission slot opens):** check calibration score (`kaggle competitions submissions`). Then submit the Exp 7 package: `venv312/bin/python scripts/build_submission.py exp07_graphfirst` (if `build/` is missing), then `kaggle competitions submit gemma-4-developer-agent -f build/exp07_graphfirst/submission.zip -m "<msg>"`. Record ref, sha256 (see `findings/submissions/exp07_graphfirst_MANIFEST.txt`) and score here.
2. **2026-10-17 >= 00:09 (quota refills to 30 h):** verify `kaggle quota`; then (see `IDEAS.md` section 4):
   a. launch `pilot_conc3` (best prompt, 3 tasks at once; ~1.5 h) and `exp08_model31b` (31B + best prompt; ~4 h) - max 2 GPU sessions at once;
   b. compare `pilot_conc3` with `exp07` (per-task seconds / tool calls) to decide if concurrency is faithful; if yes add `"concurrency": 3` to later specs and run `exp09_deadline`, `exp10_nothoughts`, `exp11_temp`, `exp12_editfromsearch`;
   c. validate the best candidates on the 51 valid sound tasks (`val51_exp07`, `val51_combo02`, plus any new winner);
   d. fetch with `scripts/fetch_output.sh`, compare with `scripts/compare.py` (paired sign test) and `scripts/task_stats.py`.
3. Choose the final agent from: 51-task validation, leaderboard scores of submitted candidates, simplicity (prefer Exp 7 if tied). Build with `scripts/build_submission.py`, verify, submit, and select up to 2 final submissions before 2026-12-02 23:59.
4. Further ideas and the full backlog: `IDEAS.md`.

Trace analysis (exp07 + combo02, 40 runs, 168 min): read_file = 51% of calls and 37% of time; edit_file waits average 32 s (composing the edit); gaps >40 s are 42% of all time; run_command is mostly grep (254/381); pytest was called only twice in 40 runs (the agent rarely verifies). Ideas: encourage fewer, larger reads; encourage one verification run; reduce long pre-edit thinking.

## Blockers
- GPU quota (1.01 h) until 2026-10-17 00:00 UTC and one-submission-per-day until 2026-10-16 00:00 UTC. Independent work is done; the plan above resumes at those times.
