"""Generate a Kaggle experiment notebook from a JSON spec.

Usage: python3 notebooks/make_exp.py experiments/exp02.json [more specs...]

A spec lists only what differs from the base config (experiments/best.json, the current best known-good
configuration). Merge rules: `sampling` is deep-merged; `system_prompt_append` / `analyzer_prompt_append` are
concatenated (base first); `extra_files`, `replace_files`, `budget` are dict-merged. Output goes to
notebooks/<name>/ (source .py, .ipynb, kernel-metadata.json). Push with:
    kaggle kernels push -p notebooks/<name>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'notebooks'))
from build_notebook import build  # noqa: E402

KERNEL_OWNER = 'bellosashmed'


def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def merge_specs(base: dict, spec: dict) -> dict:
    out = deep_merge(base, {k: v for k, v in spec.items() if k not in ('system_prompt_append', 'analyzer_prompt_append')})
    for key in ('system_prompt_append', 'analyzer_prompt_append'):
        parts = [p for p in (base.get(key), spec.get(key)) if p]
        if parts:
            out[key] = '\n\n'.join(parts)
    return out


def slugify(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')


def make(spec_path: Path) -> Path:
    spec = json.loads(spec_path.read_text())
    base_name = spec.get('base', 'best')
    base = json.loads((ROOT / 'experiments' / f'{base_name}.json').read_text()) if base_name else {}
    merged = merge_specs(base, spec)
    merged['name'] = spec['name']
    tasks_file = ROOT / spec.get('tasks_file', 'findings/baseline_tasks_20.txt')
    merged['tasks'] = tasks_file.read_text().split()
    merged.pop('base', None)
    kernel_meta_override = merged.pop('kernel_metadata', {})

    template = (ROOT / 'notebooks' / 'template' / 'exp_template.py').read_text()
    src = template.replace('__EXP_JSON__', repr(json.dumps(merged, sort_keys=True)))
    out_dir = ROOT / 'notebooks' / spec['name']
    out_dir.mkdir(parents=True, exist_ok=True)
    py = out_dir / f"{spec['name']}_kaggle.py"
    py.write_text(src)
    build(py)

    meta = json.loads((ROOT / 'notebooks' / 'baseline' / 'kernel-metadata.json').read_text())
    meta['title'] = spec['title']
    meta['id'] = f'{KERNEL_OWNER}/{slugify(spec["title"])}'
    meta['code_file'] = f"{spec['name']}_kaggle.ipynb"
    meta.update(kernel_meta_override)
    (out_dir / 'kernel-metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
    (out_dir / 'resolved_spec.json').write_text(json.dumps(merged, indent=2, sort_keys=True) + '\n')
    return out_dir


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(make(Path(p)))
