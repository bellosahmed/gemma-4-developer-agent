"""Compare experiment results against reference results (per task and by failure cause).

Usage: python3 scripts/compare.py <experiment_results.jsonl> [--ref <reference.jsonl>] [--name NAME]

The reference defaults to the baseline CSV/JSONL stored in findings/. Failure causes come from the harness error string.
"""
import argparse
import csv
import json
import statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path) -> dict:
    if path.suffix == '.csv':
        rows = list(csv.DictReader(path.open()))
        for r in rows:
            r['resolved'] = r['resolved'] == 'True'
            for k in ('patch_chars', 'seconds'):
                r[k] = float(r[k] or 0)
            r['tool_calls'] = float(r['tool_calls']) if r.get('tool_calls') not in (None, '') else 0
            r['error'] = r.get('error') or ''
    else:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return {r['id']: r for r in rows}


def cause(r: dict) -> str:
    e = r['error']
    if r['resolved']:
        return 'resolved'
    if 'ContextWindowExceeded' in e:
        return 'context-window error'
    if 'session timeout' in e:
        return 'out of time'
    if 'tool call budget' in e:
        return 'out of tool calls'
    if e.startswith('CRASH'):
        return 'crash'
    return 'patch submitted, tests failed'


def summary(name: str, d: dict) -> None:
    n = len(d)
    print(f"{name}: resolved {sum(r['resolved'] for r in d.values())}/{n} | mean sec {st.mean(r['seconds'] for r in d.values()):.0f} | "
          f"mean tools {st.mean(r['tool_calls'] or 0 for r in d.values()):.1f} | empty patches {sum(r['patch_chars'] == 0 for r in d.values())}")
    for k, v in Counter(cause(r) for r in d.values()).most_common():
        print(f'   {v:>2} {k}')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('--ref', default=str(ROOT / 'findings' / 'exp01_results.csv'))
    ap.add_argument('--name', default='experiment')
    ap.add_argument('--exclude', default=str(ROOT / 'findings' / 'vacuous_task_ids.txt'),
                    help='task ids that pass with an empty patch; excluded from the adjusted score')
    a = ap.parse_args()
    new, ref = load(Path(a.results)), load(Path(a.ref))
    missing = sorted(set(ref) - set(new))
    print(f"tasks: experiment {len(new)}, reference {len(ref)}, missing from experiment: {missing or 'none'}\n")
    print(f"{'task':<16}{'ref':>5}{'new':>5}   new: cause / patch chars / tools / sec")
    for i in ref:
        r = new.get(i)
        if r is None:
            print(f'{i:<16}  (missing)')
            continue
        print(f"{i:<16}{('PASS' if ref[i]['resolved'] else '-'):>5}{('PASS' if r['resolved'] else '-'):>5}   "
              f"{cause(r)} / {int(r['patch_chars'])} / {int(r['tool_calls'] or 0)} / {r['seconds']}")
    gained = [i for i in new if new[i]['resolved'] and i in ref and not ref[i]['resolved']]
    lost = [i for i in new if i in ref and ref[i]['resolved'] and not new[i]['resolved']]
    print(f'\ngained: {gained or "none"} | lost: {lost or "none"}\n')
    ex = set(Path(a.exclude).read_text().split()) if Path(a.exclude).exists() else set()
    valid = [i for i in ref if i not in ex and i in new]
    adj = lambda d: sum(d[i]['resolved'] for i in valid)
    print(f'ADJUSTED (excluding vacuous {sorted(ex & set(ref))}): reference {adj(ref)}/{len(valid)} | {a.name} {adj(new)}/{len(valid)}\n')
    summary('reference', ref)
    print()
    summary(a.name, new)


if __name__ == '__main__':
    main()
