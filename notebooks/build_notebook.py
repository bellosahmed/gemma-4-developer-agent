"""Convert a '# %%' percent-format .py file into a .ipynb (no extra dependencies).

Usage: python3 notebooks/build_notebook.py notebooks/gold_check_kaggle.py
Writes the .ipynb next to the .py file.
"""
import json
import re
import sys
from pathlib import Path


def build(src: Path) -> Path:
    cells, kind, buf = [], None, []

    def flush():
        if kind is None:
            return
        lines = buf[:]
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            return
        if kind == 'markdown':
            text = [re.sub(r'^# ?', '', ln) for ln in lines]
            cell = {'cell_type': 'markdown', 'metadata': {}, 'source': [t + '\n' for t in text]}
        else:
            cell = {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [],
                    'source': [ln + '\n' for ln in lines]}
        cell['source'][-1] = cell['source'][-1].rstrip('\n')
        cells.append(cell)

    for line in src.read_text().splitlines():
        m = re.match(r'^# %%( \[markdown\])?\s*$', line)
        if m:
            flush()
            kind, buf = ('markdown' if m.group(1) else 'code'), []
        elif kind is not None:
            buf.append(line)
    flush()

    nb = {
        'cells': cells,
        'metadata': {
            'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
            'language_info': {'name': 'python'},
        },
        'nbformat': 4,
        'nbformat_minor': 5,
    }
    out = src.with_suffix('.ipynb')
    out.write_text(json.dumps(nb, indent=1) + '\n')
    return out


if __name__ == '__main__':
    print(build(Path(sys.argv[1])))
