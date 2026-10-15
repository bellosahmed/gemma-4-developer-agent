#!/bin/bash
# Download a Kaggle notebook's output with retries; reject Kaggle's HTML error pages (502s saved under real file names).
# Usage: scripts/fetch_output.sh <owner/kernel> <dest_dir> <expected_results_file>
K=~/kaggle-venv/bin/kaggle
kernel="$1"; dest="$2"; probe="$3"
for try in 1 2 3 4 5; do
  rm -rf "$dest"; mkdir -p "$dest"
  timeout 240 "$K" kernels output "$kernel" -p "$dest" >/dev/null 2>&1
  f="$dest/$probe"
  if [ -s "$f" ] && ! head -c 200 "$f" | grep -qi '<html'; then
    echo "ok on try $try: $(wc -l < "$f") lines in $probe"; exit 0
  fi
  echo "try $try failed ($( [ -f "$f" ] && stat -c %s "$f" || echo missing ) bytes); retrying in 30s"; sleep 30
done
echo "giving up after 5 tries"; exit 1
