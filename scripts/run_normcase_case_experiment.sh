#!/usr/bin/env bash
set -euo pipefail

export CORPUS="${CORPUS:-data/processed/corpus_case_enhanced.jsonl}"
export EVAL="${EVAL:-data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl}"
export CASES="${CASES:-data/cases/lowalt_case_seed.jsonl}"
export MODE="${MODE:-tarrag}"
export MODEL="${MODEL:-Qwen/Qwen3-32B}"
export JUDGE_MODEL="${JUDGE_MODEL:-Qwen/Qwen3-32B}"
export WORKERS="${WORKERS:-4}"
export OUT_DIR="${OUT_DIR:-outputs/final}"
export TAG="${TAG:-normcase_tarrag_case}"
export MD_OUT="${MD_OUT:-paper/final/NormCase_TARRAG_Case_Experiment_Results.md}"

bash scripts/run_case_api_experiment.sh
