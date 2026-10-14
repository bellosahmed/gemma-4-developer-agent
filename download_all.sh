#!/bin/bash
K=~/kaggle-venv/bin/kaggle
cd ~/Documents/gemma/kaggle-data
n=0; fail=0
while IFS=, read -r f size rest; do
  d=$(dirname "$f")
  [ -f "$f" ] && [ "$(stat -c %s "$f")" = "$size" ] && continue
  mkdir -p "$d"
  if $K competitions download -f "$f" -p "$d" -q >/dev/null 2>>download_errors.log; then n=$((n+1)); else fail=$((fail+1)); echo "FAIL $f" >> download_errors.log; fi
  echo "done=$n fail=$fail last=$f" > progress.txt
done < files_all.csv
echo "FINISHED done=$n fail=$fail" > progress.txt
