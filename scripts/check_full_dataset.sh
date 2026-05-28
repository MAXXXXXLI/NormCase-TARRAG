#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m lowalt_exp.dataset_audit \
  --corpus "${1:-data/processed/corpus.jsonl}" \
  --source-vocab "${2:-configs/source_id_vocab_full.json}" \
  --eval "${3:-data/eval/xl/lowaltbench_xl_1200.jsonl}" \
  --out "${4:-outputs/full_dataset_audit.json}"
