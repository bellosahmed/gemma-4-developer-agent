"""Local safety test for the template's concurrent run loop (stand-in agent returns the reference patch)."""
import asyncio, concurrent.futures, json, shutil, sys, tempfile, threading, time
from pathlib import Path
from adk_eval_core import SessionTrace
from swegemma.config import EvalConfig
from swegemma.evaluate import Evaluator
from swegemma.models import load_tasks

ROOT = Path(__file__).resolve().parent.parent
conc = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ids = ['rich_3454', 'rich_3905', 'rich_2725', 'rich_3718']
alltasks = {t.instance_id: t for t in load_tasks(ROOT / 'kaggle-data/tasks.jsonl')}
tasks = [alltasks[i] for i in ids]
tmp = Path(tempfile.mkdtemp())
cfg = EvalConfig(tasks_path=ROOT / 'kaggle-data/tasks.jsonl', snapshots_dir=ROOT / 'kaggle-data/snapshots', results_dir=tmp / 'results',
                 submission_dir=ROOT / 'kaggle-data/sample_submission', models={}, sandbox='subprocess', wheels_dir=ROOT / 'kaggle-data/wheels',
                 graph_dir=str(ROOT / 'kaggle-data/graphs'), embeddings_dir=str(ROOT / 'kaggle-data/embeddings'), verbose=False)
evaluator = Evaluator(cfg)

async def stub(task, *a, **k):
    return task.patch, None, SessionTrace()
evaluator._run_agent_sandbox = stub

src = (ROOT / 'notebooks/template/exp_template.py').read_text()
a = src.index('CONCURRENCY = int('); b = src.index('# %% [markdown]\n# ## 5. Summary')
code = src[a:b]
WORKING_DIR = tmp; RESULTS_JSONL = tmp / 'r.jsonl'
ns = dict(evaluator=evaluator, tasks=tasks, done=set(), RESULTS_JSONL=RESULTS_JSONL, WORKING_DIR=WORKING_DIR, SESSION_LIMIT_HOURS=10,
          EXP={'concurrency': conc}, json=json, time=time, threading=threading, concurrent=concurrent, asyncio=asyncio, Path=Path)
t = time.time(); exec(code, ns); wall = time.time() - t
rows = [json.loads(l) for l in RESULTS_JSONL.read_text().splitlines()]
print(f'\nconcurrency={conc}: wall {wall:.0f}s | rows {len(rows)} | resolved {sum(r["resolved"] for r in rows)}/{len(rows)} | crashes {sum(r["error"].startswith("CRASH") for r in rows)}')
print('patch files:', sorted(p.name for p in (tmp / 'patches').glob('*.patch')), '| sizes', [p.stat().st_size for p in sorted((tmp / 'patches').glob('*.patch'))])
print('errors:', [r['error'][:80] for r in rows if r['error']])
