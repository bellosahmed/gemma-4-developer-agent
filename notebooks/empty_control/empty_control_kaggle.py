# %% [markdown]
# # Empty-patch audit on the 52 sound tasks (CPU only): which tasks pass with NO patch?
#
# For every public task, run the harness's real Phase 2 verification with the task's **reference ("gold") patch**.
# A sound task passes. A task whose correct fix fails cannot be solved by any agent in this environment.
# The first `CONTROL_N` tasks also run with an **empty patch**, which must fail (proves the tests detect the bug).
#
# No model and no GPU are used: Phase 1 (the agent) is replaced by a stub that returns the patch.
#
# Attach: the competition data and the dataset `metric/gemma-4-developer-agent-wheelhouse`.
# Settings: Accelerator = None, Internet = Off.

# %% [markdown]
# ## 1. Install the harness (GPU packages skipped)

# %%
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['TRANSFORMERS_NO_FLAX'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'
os.environ['LITELLM_TELEMETRY'] = 'False'
os.environ['OTEL_SDK_DISABLED'] = 'true'

WHEELHOUSE_DIR = Path('/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse')
# Serving/GPU wheels: large and unused here (no model is run).
SKIP_PREFIXES = ('vllm', 'flashinfer', 'bitsandbytes', 'apache_tvm', 'nvidia', 'quack', 'xgrammar', 'cutlass')

tmp_whl = Path('/tmp/wheelhouse')
tmp_whl.mkdir(parents=True, exist_ok=True)
for w in WHEELHOUSE_DIR.glob('*.whl'):
    if w.name.lower().startswith(SKIP_PREFIXES):
        continue
    # Kaggle dataset uploads strip the '+' from local version tags such as '+cu128'; restore it.
    name = w.name.replace('cu128', '+cu128') if ('cu128' in w.name and '+' not in w.name) else w.name
    target = tmp_whl / name
    if not target.exists():
        try:
            os.symlink(w, target)
        except OSError:
            shutil.copyfile(w, target)

# The wheelhouse targets the GPU image (CPython 3.12); CPU notebooks may run a newer Python, where
# 3.12-only compiled wheels are rejected. Install only wheels this interpreter supports.
from packaging.tags import sys_tags  # noqa: E402
from packaging.utils import parse_wheel_filename  # noqa: E402

supported = set(sys_tags())
wheels, skipped = [], []
for w in sorted(tmp_whl.glob('*.whl')):
    tags = parse_wheel_filename(w.name)[3]
    (wheels if any(t in supported for t in tags) else skipped).append(w)
print(f'Python {sys.version.split()[0]}: installing {len(wheels)} wheels, '
      f'skipping {len(skipped)} incompatible: {[w.name.split("-")[0] for w in skipped]}')

required = ('swegemma', 'adk_submission', 'adk_eval_core', 'google_adk')
missing = [r for r in required if not any(w.name.startswith(r + '-') for w in wheels)]
assert not missing, f'Required harness wheels not installable on this Python: {missing}'

subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-deps', '--force-reinstall',
                *map(str, wheels)], check=True)
importlib.invalidate_caches()

import swegemma  # noqa: E402

print('swegemma imported OK:', getattr(swegemma, '__version__', 'unknown version'))

# %% [markdown]
# ## 2. Configure

# %%
import asyncio  # noqa: E402
import concurrent.futures  # noqa: E402
import time  # noqa: E402

from adk_eval_core import SessionTrace  # noqa: E402
from swegemma.config import EvalConfig  # noqa: E402
from swegemma.evaluate import Evaluator  # noqa: E402
from swegemma.models import load_tasks  # noqa: E402

DATA_DIR = Path('/kaggle/input/competitions/gemma-4-developer-agent')
WORKING_DIR = Path('/kaggle/working')
RESULTS_JSONL = WORKING_DIR / 'empty_results.jsonl'

CONTROL_N = 10        # also run an empty-patch control on the first N tasks
MAX_TASKS = None      # None = all tasks; set to e.g. 5 for a quick trial
SANDBOX = 'subprocess'  # same backend the official starter notebook uses

tasks = load_tasks(DATA_DIR / 'tasks.jsonl')
SOUND = set("""
fastapi_15661 fastapi_15588 fastapi_15589 fastapi_15280 fastapi_14986 requests_7427 requests_7315 requests_7309 rich_4077 rich_4076 rich_4075 rich_4006 fastapi_14258 fastapi_14851 fastapi_14873 fastapi_14372 rich_3718 rich_3934 rich_3953 rich_3944 rich_3942 rich_3938 rich_3882 rich_3894 rich_3935 rich_3905 rich_3930 fastapi_15800 rich_3180 rich_3777 rich_3468 rich_3772 rich_3675 rich_3676 rich_3518 rich_3535 rich_3521 rich_3506 rich_3480 rich_3454 rich_3471 rich_3470 rich_3052 rich_3278 rich_2943 rich_2725 rich_3105 rich_3043 rich_3067 rich_3006 rich_3063 rich_3061
""".split())
tasks = [t for t in tasks if t.instance_id in SOUND]
if MAX_TASKS:
    tasks = tasks[:MAX_TASKS]
print(f'{len(tasks)} tasks to check; sandbox={SANDBOX}')

cfg = EvalConfig(
    tasks_path=DATA_DIR / 'tasks.jsonl',
    snapshots_dir=DATA_DIR / 'snapshots',
    results_dir=WORKING_DIR / 'results',
    submission_dir=DATA_DIR / 'sample_submission',
    models={},
    sandbox=SANDBOX,
    wheels_dir=DATA_DIR / 'wheels',
    graph_dir=str(DATA_DIR / 'graphs'),
    embeddings_dir=str(DATA_DIR / 'embeddings'),
    verbose=False,
)
evaluator = Evaluator(cfg)


def run_sync(fn, *args, **kwargs):
    """Run an async call from inside a notebook's already-running event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(fn(*args, **kwargs))
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(fn(*args, **kwargs))).result()


# %% [markdown]
# ## 3. Run the checks (resumable)
# Each result is appended to `gold_results.jsonl` as soon as it finishes. If the session stops, re-run this cell:
# finished (task, case) pairs are skipped.

# %%
done = set()
if RESULTS_JSONL.exists():
    for line in RESULTS_JSONL.read_text().splitlines():
        r = json.loads(line)
        done.add((r['id'], r['case']))
print(f'{len(done)} results already on disk')

t_start = time.time()
for idx, task in enumerate(tasks):
    cases = [('empty', '')]
    for case, patch in cases:
        if (task.instance_id, case) in done:
            continue

        async def stub(*_a, _p=patch, **_k):
            return _p, None, SessionTrace()

        evaluator._run_agent_sandbox = stub
        try:
            res = run_sync(evaluator.evaluate_task, task)
            row = {
                'id': task.instance_id, 'repo': task.repo, 'case': case,
                'resolved': bool(res.resolved), 'exit_code': res.test_exit_code,
                'seconds': round(res.duration_seconds, 1), 'error': res.error or '',
                'output_tail': (res.test_output or '')[-1500:],
            }
        except Exception as exc:  # keep going; record the crash
            row = {
                'id': task.instance_id, 'repo': task.repo, 'case': case, 'resolved': False,
                'exit_code': None, 'seconds': 0.0, 'error': f'CRASH {type(exc).__name__}: {exc}'[:500],
                'output_tail': '',
            }
        with RESULTS_JSONL.open('a') as f:
            f.write(json.dumps(row) + '\n')
        print(f'[{idx + 1}/{len(tasks)}] {row["id"]:<18} {case:<5} resolved={row["resolved"]!s:<5} '
              f'exit={row["exit_code"]} {row["seconds"]}s  (elapsed {(time.time() - t_start) / 60:.1f} min)',
              flush=True)

# %% [markdown]
# ## 4. Summary

# %%
import pandas as pd  # noqa: E402

df = pd.DataFrame([json.loads(line) for line in RESULTS_JSONL.read_text().splitlines()])
gold = df[df.case == 'empty']
empty = df[df.case == 'empty']

print(f'EMPTY patch passes (vacuous tasks, should be ~0): {int(gold.resolved.sum())} / {len(gold)}')
if len(empty):
    print('vacuous ids:', list(empty[empty.resolved].id))
print()
print(gold.groupby('repo').resolved.agg(passed='sum', total='count'))

# Tasks whose correct fix fails: unsolvable here, whatever the agent does.
bad = gold[~gold.resolved]
print(f'\n{len(bad)} tasks correctly FAIL with an empty patch (good):')
for _, r in bad.iterrows():
    last = next((ln for ln in reversed(r.output_tail.splitlines()) if ln.strip()), '')[:140]
    print(f'  {r.id:<18} exit={r.exit_code}  {r.error[:60] or last}')

df.drop(columns=['output_tail']).to_csv(WORKING_DIR / 'empty_summary.csv', index=False)
(WORKING_DIR / 'vacuous_task_ids.txt').write_text('\n'.join(empty[empty.resolved].id) + '\n')
print('\nWrote gold_summary.csv and sound_task_ids.txt to /kaggle/working')
