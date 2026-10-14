"""Sandbox sanity check: does grading work on this machine, with no model involved?

For each task id given, runs the harness's real Phase 2 verification twice:
  1. with the task's reference ("gold") patch  -> should be resolved=True
  2. with an empty patch                       -> should be resolved=False
Phase 1 (the LLM agent) is replaced by a stub that just returns the patch.

Usage: venv312/bin/python check_gold.py fastapi_15661 [more ids...]
"""
import asyncio
import os
import sys
from pathlib import Path

from swegemma.config import EvalConfig
from swegemma.evaluate import Evaluator
from swegemma.models import load_tasks

HOME = Path(__file__).resolve().parent
DATA = HOME / 'kaggle-data'


async def main(ids: list[str]) -> None:
    tasks = {t.instance_id: t for t in load_tasks(DATA / 'tasks.jsonl')}
    cfg = EvalConfig(
        tasks_path=DATA / 'tasks.jsonl',
        snapshots_dir=DATA / 'snapshots',
        results_dir=HOME / 'results' / 'gold_check',
        submission_dir=DATA / 'sample_submission',
        models={},
        sandbox=os.environ.get('SANDBOX', 'docker'),
        wheels_dir=DATA / 'wheels',
        graph_dir=str(DATA / 'graphs'),
        embeddings_dir=str(DATA / 'embeddings'),
        verbose=False,
    )
    ev = Evaluator(cfg)

    for iid in ids:
        task = tasks[iid]
        for label, patch in (('gold patch', task.patch), ('empty patch', '')):
            async def stub(*_a, _p=patch, **_k):
                from adk_eval_core import SessionTrace  # noqa: PLC0415
                return _p, None, SessionTrace()

            ev._run_agent_sandbox = stub
            res = await ev.evaluate_task(task)
            out_dir = HOME / 'results' / 'gold_check' / 'out'
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f'{iid}_{label.split()[0]}.log').write_text(res.test_output or '')
            print(
                f'{iid:<18} {label:<12} resolved={res.resolved!s:<5} '
                f'exit={res.test_exit_code} {res.duration_seconds:5.1f}s '
                f'error={(res.error or "")[:90]!r}',
                flush=True,
            )


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:] or ['fastapi_15661']))
