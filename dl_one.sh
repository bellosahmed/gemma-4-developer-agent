#!/bin/bash
f="$1"; size="$2"
cd ~/Documents/gemma/kaggle-data
[ -f "$f" ] && [ "$(stat -c %s "$f")" = "$size" ] && exit 0
d=$(dirname "$f"); mkdir -p "$d"
for try in 1 2 3; do
  ~/kaggle-venv/bin/kaggle competitions download -f "$f" -p "$d" -q >/dev/null 2>&1 && [ "$(stat -c %s "$f" 2>/dev/null)" = "$size" ] && exit 0
done
echo "FAIL $f" >> download_errors.log
