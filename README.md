# Gemma 4 Developer Agent (Kaggle)

Working repo for the Kaggle [Gemma 4 Developer Agent](https://www.kaggle.com/competitions/gemma-4-developer-agent)
competition: build a config-only coding agent (`agent.yaml`, prompts, skills, LoRA adapters) that fixes real
GitHub issues in `fastapi`, `rich`, `requests` and `httpx`. Score = share of tasks whose hidden tests pass.

This repo holds only small files (scripts, notes, our submission config). Data, virtualenvs and logs are
git-ignored and re-created with the steps below.

## Layout

| Path | What it is |
|---|---|
| `check_gold.py` | Sandbox sanity check: runs the harness's real verification with the task's reference patch (should pass) and an empty patch (should fail). No model needed. |
| `list_files.sh`, `download_all.sh`, `dl_one.sh` | Download all 524 competition files (22 GB), 6 in parallel, resumable. |
| `progress.sh` | Live progress bar for the download. |
| `spread_ids.txt` | Oldest + newest task per repo used for the sandbox spread check. |

## Setup (local, free)

1. **Kaggle CLI + token.** `python3 -m venv ~/kaggle-venv && ~/kaggle-venv/bin/pip install kaggle`, then save an
   API token (kaggle.com > Settings > API) to `~/.kaggle/access_token` (`chmod 600`). Join the competition and
   accept its rules on the website first, or downloads return 403.
2. **Data.** `kaggle competitions files --page-size 200 -v` into `kaggle-data/files_all.csv`
   (see `list_files.sh`), then `./download_all.sh`. Expect ~22 GB.
3. **Harness (Python 3.12 required).**
   `python3.12 -m venv venv312`, install CPU torch
   (`pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`), download
   `swegemma-0.2.11`, `adk_submission-0.2.13`, `adk_eval_core-0.1.0`, `google_adk-1.36.1` from the Kaggle dataset
   `metric/gemma-4-developer-agent-wheelhouse`, and `pip install` them plus `pytest pytest-timeout==2.1.0`.
4. **Sandbox image.** Build `kaggle-data/docker/Dockerfile.public` as `swebench-sandbox:latest` from a folder that
   also contains `imp.py`, `telnetlib.py` and `wheels/`.
5. **Check.** `venv312/bin/python check_gold.py fastapi_15661` (env `SANDBOX=subprocess` for the other backend).

The starter notebook is Kaggle's, not ours: `kaggle kernels pull ryanholbrook/getting-started-gemma-4-developer-agent`.

## Hardware notes

- Competition scoring runs on 4x NVIDIA L4 with vLLM. Allowed base models are the four 4-bit
  `gemma-4-{31b,12b,e4b,e2b}-it-qat-w4a16-ct`. Their weight files are large (e2b is 8.3 GB, e4b 11.5 GB), so none
  fit on an 8 GB laptop GPU. Real model runs therefore happen in a Kaggle notebook.
- Local machine is used for config editing, validation, packaging and sandbox checks.

## Findings so far

Reference-patch check on Kaggle's CPU notebook (`notebooks/gold_check_kaggle.ipynb`, Python 3.13, `subprocess` sandbox,
all 129 public tasks, no model). Raw results: `findings/gold_summary.csv`; passable tasks: `findings/sound_task_ids.txt`.

- **Only 52 of 129 tasks (40%) pass with the correct reference patch.** The 10 empty-patch controls all fail, as they should.
  A task whose correct fix fails cannot be solved by any agent in that environment.

| Repo | Reference patch passes |
|---|---|
| rich | 39 / 48 |
| fastapi | **10 / 67** |
| requests | 3 / 13 |
| httpx | 0 / 1 |

- Causes of the 77 failures (counted from the saved pytest output):
  - 26 fastapi tasks: tests import `inline_snapshot`, which is not in the competition `wheels/`.
  - 21 fastapi tasks: `TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'` (a Starlette
    version that is too new for the repo; the notebook host's packages are used, not the pinned wheels).
  - 5 fastapi tasks: tests import `dirty_equals`, also missing from `wheels/`.
  - 17 tasks end with an empty `STDERR:`; the cause is unknown (the notebook kept only the last 1,500 chars of output).
  - ~6 others: exact-output assertions (Pygments/terminal differences) or one-off errors (`httpx_3672`: `httpx.Stream` missing).
- Caveats: Kaggle's CPU notebook runs Python 3.13 but the wheelhouse targets the GPU image (Python 3.12), so the official
  scorer's environment may differ. Treat the numbers as strong evidence, not proof.
- Leaderboard (2026-10-13) top score was 0.24. Public-set ceiling here looks like roughly 52/129 = 0.40.
- Task mix is lopsided (67 fastapi, 48 rich, 13 requests, 1 httpx), and fastapi, the biggest repo, is where most tasks are unsound.

Earlier local Docker checks agreed in direction (reference patches passed on only 2 of 8 tasks) but with different causes
for some tasks, so local Docker results should not be trusted as a stand-in for the Kaggle environment.

## Baseline (unmodified sample agent, Gemma 4 12B, 20 sound tasks)

Notebook: `notebooks/baseline/` (Kaggle, 4x L4, starter's pinned image). Sample prompt, tools and sampling untouched;
budget 5 min / 40 tool calls per task. Tasks: `findings/baseline_tasks_20.txt` (10 fastapi, 8 rich, 2 requests).
Per-task results: `findings/baseline_20_results.csv`. Cost: ~2.8 GPU-hours of the free weekly quota.

**Resolved 3 / 20 (15%)**: fastapi 0/10, rich 3/8, requests 0/2. Mean 230 s and 25.6 tool calls per task; 9 tasks ended with no patch.

| Why the other 17 failed | Tasks |
|---|---|
| `ContextWindowExceededError`: sample asks for 16,384 output tokens, so once the prompt passes ~16.4k tokens every model call is rejected | 8 |
| Ran out of time (5 min) | 5 |
| Ran out of tool calls (40) | 3 |
| Patch recovered/submitted, tests failed | 1 |

Observed in traces (3-task pilot): the model sometimes stalls in one long call (~60 tokens/s, so a 16k-token reply is ~4 min),
repeats "Wait ..." reasoning loops, and burns calls on `edit_file` exact-match failures.

## Experiment log (same 20 tasks, same 5 min / 40 tool-call budget, Gemma 4 12B)

| # | Change | Resolved | Context errors | Timeouts | Tool-budget | Empty patches | GPU-h |
|---|---|---|---|---|---|---|---|
| 0 | Baseline (unmodified sample) | 3/20 | 8 | 5 | 3 | 9 | ~2.8 |
| 1 | `max_output_tokens` 16384 -> 8192 | 3/20 | 0 | 11 | 4 | 6 | ~3.2 |

- **Exp 1:** removed all 8 context-window failures and cut empty patches 9 -> 6, but the score did not move: one task gained
  (`fastapi_14873`), one lost (`rich_2725`, which ran out of time with a 41k-char patch). The freed tasks now hit the 5-minute
  limit instead (timeouts 5 -> 11). Time, not context, is now the binding limit. Keep the change (no downside), but it is not a win by itself.
- With n=20 a single task is 5 points; differences under ~15 points are within noise. Prefer secondary metrics (failure causes) and
  confirm any claimed gain on all 52 sound tasks.
- Per-task results: `findings/baseline_20_results.csv`, `findings/exp01_results.csv`.

## Plan

1. (Done) Reference-patch check on Kaggle: 52 sound tasks. Next: keep the 17 unknown-cause failures in mind and re-run with longer output tails if they matter.
2. (Done) Baseline: 3/20. Exp 1 (cap `max_output_tokens`) done: 3/20, time is now the limit. Next: reduce wasted generation (thinking budget, concise-reasoning prompt).
3. Improve in order: prompts and tool use, sub-agent for code search, budgets in `eval_config.yaml`,
   best-of-N with self-verification, LoRA only if it measurably helps. Keep a held-out validation split.
