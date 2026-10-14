#!/bin/bash
# Live progress bar for the Kaggle data download.
# Usage: ./progress.sh          (updates until finished, Ctrl+C to quit)
#        ./progress.sh once     (print once and exit)
cd ~/Documents/gemma/kaggle-data || exit 1

total_bytes=$(awk -F, '{s+=$2} END{print s}' files_all.csv)
total_files=$(wc -l < files_all.csv)

draw() {
  local done_bytes=0 done_files=0 size
  # count only files that match the expected size, plus partial bytes of others
  while IFS=, read -r f size _; do
    if [ -f "$f" ]; then
      cur=$(stat -c %s "$f")
      done_bytes=$((done_bytes + cur))
      [ "$cur" = "$size" ] && done_files=$((done_files + 1))
    fi
  done < files_all.csv

  local pct=$((done_bytes * 100 / total_bytes))
  local width=40 filled=$((pct * 40 / 100))
  local bar
  bar=$(printf '%*s' "$filled" '' | tr ' ' '#')$(printf '%*s' $((width - filled)) '' | tr ' ' '-')
  printf '\r[%s] %3d%%  %.2f/%.2f GB  %d/%d files ' \
    "$bar" "$pct" "$(echo "$done_bytes/1000000000" | bc -l)" "$(echo "$total_bytes/1000000000" | bc -l)" \
    "$done_files" "$total_files"
  [ "$done_files" -ge "$total_files" ]
}

if [ "$1" = "once" ]; then draw; echo; exit 0; fi
until draw; do sleep 5; done
echo; echo "Download complete."
