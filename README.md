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

- Task mix: 129 public tasks, 67 fastapi / 48 rich / 13 requests / 1 httpx.
- Leaderboard (2026-10-13) top score was 0.24.
- **Local Docker grading is not reliable.** Reference patches pass on only 2 of 8 tasks tried
  (`fastapi_15661`, `rich_3061`). Causes seen:
  - `fastapi_14077`: `pydantic` needs `typing_inspection`, which is absent from the competition `wheels/`.
  - `requests_6592`: tests need an `httpbin` server and network access; sandbox is offline.
  - `rich_4079`: exact-color assertion differs with the Pygments version in the sandbox.
  - `httpx_3672`: `httpx.Stream` missing at test time; a different `httpx` is imported than the repo's (cause not pinned down).
- Some tasks may be unpassable in the official environment too. Next step: run the same reference-patch check in a
  Kaggle CPU notebook (the real scoring conditions) to get the true list of passable tasks.

## Plan

1. Reference-patch check on Kaggle (CPU, no model) to find sound tasks.
2. Baseline: score `sample_submission` unmodified.
3. Improve in order: prompts and tool use, sub-agent for code search, budgets in `eval_config.yaml`,
   best-of-N with self-verification, LoRA only if it measurably helps. Keep a held-out validation split.
