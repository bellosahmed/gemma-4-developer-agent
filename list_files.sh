#!/bin/bash
K=~/kaggle-venv/bin/kaggle
tok=""; : > files_all.csv
while :; do
  if [ -z "$tok" ]; then out=$($K competitions files --page-size 200 -v 2>&1); else out=$($K competitions files --page-size 200 --page-token "$tok" -v 2>&1); fi
  echo "$out" | grep -E '^[^ ]+,[0-9]+,' >> files_all.csv
  tok=$(echo "$out" | sed -n 's/^Next Page Token = //p')
  [ -z "$tok" ] && break
done
