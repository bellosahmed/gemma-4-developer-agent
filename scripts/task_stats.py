"""Per-task pass consistency across all recorded runs, to see which tasks carry information.

Usage: python3 scripts/task_stats.py [--runs a_results b_results ...]
Reads findings/<name>.csv (columns: id, resolved, ...). Vacuous tasks (findings/vacuous_task_ids.txt) are excluded.

Why: a task that is never solved (or always solved) cannot distinguish two configurations. Only 'mixed' tasks do.
Prints the pass pattern per task, the never/always/mixed groups, and a paired exact sign test of every run against a reference.
"""
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUNS = ['baseline_20_results', 'exp01_results', 'exp02_results', 'exp03_results', 'exp04_results',
                'exp05_results', 'exp06_results', 'exp07_results', 'combo02_results']


def sign_test_p(gained: int, lost: int) -> float:
    n = gained + lost
    if n == 0:
        return 1.0
    k = min(gained, lost)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', nargs='*', default=DEFAULT_RUNS)
    ap.add_argument('--ref', default='exp01_results', help='reference run for the paired sign test')
    a = ap.parse_args()
    f = ROOT / 'findings'
    vac = set((f / 'vacuous_task_ids.txt').read_text().split()) if (f / 'vacuous_task_ids.txt').exists() else set()
    runs = [r for r in a.runs if (f / f'{r}.csv').exists()]
    res: dict[str, dict[str, bool]] = defaultdict(dict)
    for r in runs:
        for row in csv.DictReader((f / f'{r}.csv').open()):
            if row['id'] not in vac:
                res[row['id']][r] = row['resolved'] == 'True'
    ids = sorted(res)
    print(f'{len(runs)} runs x {len(ids)} valid tasks (vacuous excluded: {sorted(vac)})\n')
    groups = {'never': [], 'always': [], 'mixed': []}
    for t in ids:
        k = sum(res[t].get(r, False) for r in runs)
        groups['always' if k == len(runs) else 'never' if k == 0 else 'mixed'].append((t, k))
    for t, k in sorted(groups['mixed'], key=lambda x: -x[1]) + groups['always']:
        print(f"  {t:<16}{k:>2}/{len(runs)}  {''.join('#' if res[t].get(r) else '.' for r in runs)}")
    print(f"\nnever: {len(groups['never'])} | always: {len(groups['always'])} | mixed (the only informative tasks): {len(groups['mixed'])}")
    print('never solved:', ', '.join(t for t, _ in groups['never']))
    if a.ref in runs:
        print(f'\npaired exact sign test vs {a.ref} (discordant tasks only):')
        for r in runs:
            if r == a.ref:
                continue
            g = sum(1 for t in ids if res[t].get(r) and not res[t].get(a.ref))
            l = sum(1 for t in ids if res[t].get(a.ref) and not res[t].get(r))
            print(f'  {r:<22} gained {g} lost {l}  p = {sign_test_p(g, l):.2f}')


if __name__ == '__main__':
    main()
