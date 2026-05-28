#!/usr/bin/env bash
set -euo pipefail
CORPUS=${1:-data/processed/corpus.jsonl}
EVAL=${2:-data/eval/xl/lowaltbench_xl_1200.jsonl}
WORKERS=${3:-16}
PYTHONPATH=src python3 -m lowalt_exp.evaluator \
  --corpus "$CORPUS" \
  --eval "$EVAL" \
  --out outputs/full/eval_tarrag.json \
  --pred-out outputs/full/eval_tarrag_predictions.jsonl \
  --mode tarrag \
  --workers "$WORKERS" \
  --no-llm
