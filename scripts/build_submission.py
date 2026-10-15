"""Build submission.zip for an experiment by executing the experiment notebook's own setup code.

Usage: venv312/bin/python scripts/build_submission.py <experiment_name> [--out DIR]

Why: the Kaggle notebook builds the agent directory (copy sample, set model, budget, apply overrides) and evaluates that
directory. To submit exactly what was evaluated, this script runs the SAME code (extracted from
notebooks/<name>/<name>_kaggle.py) against the local competition data, then validates and zips the result.
Outputs: <out>/agent/ (the directory), <out>/submission.zip, <out>/MANIFEST.txt (files, sizes, sha256).
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path

import yaml
from adk_submission import validate_directory
from swegemma.config import ALLOWED_SUBMISSION_EXTENSIONS, MAX_SUBMISSION_SIZE_BYTES, build_submission_limits
from swegemma.models import load_tasks

ROOT = Path(__file__).resolve().parent.parent
SECRET_PATTERNS = [re.compile(p) for p in (r'KGAT_[0-9a-f]{20,}', r'gho_[A-Za-z0-9]{20,}', r'sk-[A-Za-z0-9]{20,}', r'AIza[0-9A-Za-z_\-]{30,}')]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    nb_py = ROOT / 'notebooks' / a.name / f'{a.name}_kaggle.py'
    src = nb_py.read_text()
    out = Path(a.out) if a.out else ROOT / 'build' / a.name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # Execute the notebook's configuration section (EXP spec ... overrides) with local paths.
    start = src.index('EXP = json.loads(')
    end_marker = "print('files in agent dir:'"
    end = src.index('\n', src.index(end_marker)) + 1
    code = src[start:end]
    code = code.replace("print('EXPERIMENT:', EXP['name'])", "")
    # point the notebook's Kaggle paths at the local data and the build directory
    kaggle_data = "Path('/kaggle/input/competitions/gemma-4-developer-agent')"
    kaggle_work = "Path('/kaggle/working')"
    assert kaggle_data in code and kaggle_work in code, 'notebook path definitions changed; update this script'
    code = code.replace(kaggle_data, f"Path({str(ROOT / 'kaggle-data')!r})").replace(kaggle_work, f"Path({str(out)!r})")
    ns = {'json': json, 'yaml': yaml, 're': re, 'shutil': shutil, 'Path': Path, 'load_tasks': load_tasks, 'sorted': sorted, 'time': time}
    exec(code, ns)  # noqa: S102 (our own generated notebook code)

    agent_dir = out / 'sample_submission'
    final_dir = out / 'agent'
    agent_dir.rename(final_dir)

    limits, _ = build_submission_limits()
    for p in final_dir.rglob('*'):
        assert not p.is_symlink(), f'symlink not allowed: {p}'
    validate_directory(final_dir, limits=limits)

    leaked = [(str(p.relative_to(final_dir)), pat.pattern) for p in final_dir.rglob('*') if p.is_file()
              for pat in SECRET_PATTERNS if pat.search(p.read_text(errors='ignore'))]
    assert not leaked, f'possible secrets in package: {leaked}'

    zip_path = Path(shutil.make_archive(str(out / 'submission'), 'zip', root_dir=final_dir))
    with zipfile.ZipFile(zip_path) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        assert 'agent.yaml' in zf.namelist(), 'agent.yaml must be at the archive root'
        assert sum(i.file_size for i in infos) <= MAX_SUBMISSION_SIZE_BYTES
        bad = [i.filename for i in infos if Path(i.filename).suffix.lower() not in ALLOWED_SUBMISSION_EXTENSIONS]
        assert not bad, f'disallowed extensions: {bad}'
        lines = [f'{i.file_size:>8}  {hashlib.sha256(zf.read(i)).hexdigest()[:12]}  {i.filename}' for i in infos]
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (out / 'MANIFEST.txt').write_text(f'experiment: {a.name}\nzip sha256: {sha}\nzip bytes: {zip_path.stat().st_size}\n\n' + '\n'.join(lines) + '\n')
    print(f'built {zip_path}\n  sha256 {sha}\n  {len(infos)} files; model(s): '
          f'{sorted(set(re.findall(r"model:\\s*(\\S+)", (final_dir / "agent.yaml").read_text())))}')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
