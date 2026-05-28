#!/usr/bin/env bash
set -euo pipefail

DEFAULT_CORPUS="data/processed/corpus_case_enhanced.jsonl"
if [ ! -f "$DEFAULT_CORPUS" ]; then
  DEFAULT_CORPUS="data/processed/corpus.jsonl"
fi

DEFAULT_EVAL="data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl"
if [ ! -f "$DEFAULT_EVAL" ]; then
  DEFAULT_EVAL="data/eval/cases/lowalt_case_eval_tasks.jsonl"
fi

CORPUS=${CORPUS:-$DEFAULT_CORPUS}
EVAL=${EVAL:-$DEFAULT_EVAL}
CASES=${CASES:-data/cases/lowalt_case_seed.jsonl}
MODE=${MODE:-tarrag}
MODEL=${MODEL:-Qwen/Qwen3-32B}
JUDGE_MODEL=${JUDGE_MODEL:-Qwen/Qwen3-32B}
WORKERS=${WORKERS:-4}
TOP_K=${TOP_K:-12}
PREFETCH_K=${PREFETCH_K:-50}
OUT_DIR=${OUT_DIR:-outputs/final}
TAG=${TAG:-normcase_${MODE}_qwen3_32b}

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

mkdir -p "$OUT_DIR"

EVAL_REPORT="$OUT_DIR/${TAG}.json"
PRED_OUT="$OUT_DIR/${TAG}_predictions.jsonl"
JUDGE_OUT="$OUT_DIR/${TAG}_judge_scores.jsonl"
JUDGE_SUMMARY="$OUT_DIR/${TAG}_judge_summary.json"
MD_OUT=${MD_OUT:-paper/final/NormCase_TARRAG_Case_Experiment_Results.md}

eval_args=(
  --corpus "$CORPUS"
  --eval "$EVAL"
  --out "$EVAL_REPORT"
  --pred-out "$PRED_OUT"
  --mode "$MODE"
  --top-k "$TOP_K"
  --prefetch-k "$PREFETCH_K"
  --model "$MODEL"
  --workers "$WORKERS"
)

if [ "${USE_RERANK:-0}" = "1" ]; then
  eval_args+=(--use-rerank)
fi

PYTHONPATH=src python3 -m lowalt_exp.evaluator "${eval_args[@]}"

PYTHONPATH=src python3 -m lowalt_exp.case_judge \
  --pred "$PRED_OUT" \
  --eval "$EVAL" \
  --cases "$CASES" \
  --out "$JUDGE_OUT" \
  --summary-out "$JUDGE_SUMMARY" \
  --judge-model "$JUDGE_MODEL" \
  --workers "$WORKERS"

PYTHONPATH=src python3 -m lowalt_exp.case_report \
  --eval-report "$EVAL_REPORT" \
  --pred "$PRED_OUT" \
  --judge-scores "$JUDGE_OUT" \
  --judge-summary "$JUDGE_SUMMARY" \
  --eval "$EVAL" \
  --cases "$CASES" \
  --corpus "$CORPUS" \
  --out "$MD_OUT" \
  --generator-model "$MODEL" \
  --judge-model "$JUDGE_MODEL" \
  --mode "$MODE" \
  --workers "$WORKERS" \
  --tag "$TAG"
