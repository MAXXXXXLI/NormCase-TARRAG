#!/usr/bin/env bash
set -euo pipefail

QUESTION="${1:-深圳做无人机城市配送试点，需要从哪些方面做合规准备？}"

PYTHONPATH=src python3 -m lowalt_exp.run_single \
  --question "$QUESTION" \
  --corpus data/processed/corpus_case_enhanced.jsonl \
  --mode tarrag \
  --no-llm
