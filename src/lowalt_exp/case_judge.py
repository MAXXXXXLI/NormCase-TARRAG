import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from .io_utils import read_jsonl, save_json, write_jsonl
from .judge import safe_json_parse
from .siliconflow import SiliconFlowClient


SCORE_FIELDS = [
    "outcome_match",
    "liability_allocation_accuracy",
    "case_type_accuracy",
    "remedy_accuracy",
    "fact_issue_coverage",
    "legal_issue_coverage",
    "rule_application_quality",
    "subsumption_quality",
    "exception_boundary_awareness",
    "source_support_quality",
    "overall",
]


def _index_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
    return {str(r.get(key)): r for r in rows if r.get(key) is not None}


def _format_hits(row: Dict[str, Any], limit: int = 12) -> str:
    lines = []
    for h in row.get("hits", [])[:limit]:
        lines.append(
            f"[{h.get('article_id')}] {h.get('title_zh')}｜{h.get('legal_level')}｜"
            f"{h.get('jurisdiction')}｜{h.get('validity')}\n{h.get('text')}"
        )
    return "\n\n".join(lines)


def build_user_payload(row: Dict[str, Any], task: Dict[str, Any], case: Dict[str, Any]) -> str:
    expected = task.get("expected_case_points") or row.get("expected_case_points") or []
    gold_outcome = task.get("gold_case_outcome") or row.get("gold_case_outcome") or case.get("gold_result_summary")
    return f"""
任务ID：{row.get('task_id')}
案例ID：{task.get('case_id') or row.get('case_id') or case.get('case_id')}
任务类型：{task.get('task_type') or row.get('task_type')}

问题：
{row.get('question') or task.get('question')}

真实案例案情：
{case.get('facts', '')}

真实裁判/处理规则：
{case.get('court_rule', '')}

真实结果：
{case.get('outcome', '')}

Gold 结果摘要：
{gold_outcome}

期望覆盖要点：
{json.dumps(expected, ensure_ascii=False)}

RAG Trace：
{json.dumps(row.get('trace', {}), ensure_ascii=False)}

RAG Resolve：
{json.dumps(row.get('resolve', {}), ensure_ascii=False)}

RAG 检索证据：
{_format_hits(row)}

RAG 答案：
{row.get('answer', '')}
""".strip()


def judge_one(row: Dict[str, Any], task_by_id: Dict[str, Dict[str, Any]], case_by_id: Dict[str, Dict[str, Any]], prompt: str, model: str) -> Dict[str, Any]:
    task = task_by_id.get(str(row.get("task_id")), {})
    case_id = task.get("case_id") or row.get("case_id")
    case = case_by_id.get(str(case_id), {})
    user = build_user_payload(row, task, case)
    client = SiliconFlowClient()
    resp = client.chat(
        model,
        [{"role": "system", "content": prompt}, {"role": "user", "content": user}],
        temperature=0.0,
        max_tokens=900,
    )
    score = safe_json_parse(resp)
    return {
        "task_id": row.get("task_id"),
        "case_id": case_id,
        "mode": row.get("mode"),
        "judge_model": model,
        "judge": score,
    }


def judge_all(rows: List[Dict[str, Any]], tasks: List[Dict[str, Any]], cases: List[Dict[str, Any]], prompt: str, model: str, workers: int) -> List[Dict[str, Any]]:
    task_by_id = _index_by(tasks, "task_id")
    case_by_id = _index_by(cases, "case_id")
    workers = max(1, int(workers))
    if workers == 1:
        out = []
        for i, row in enumerate(rows, start=1):
            judged = judge_one(row, task_by_id, case_by_id, prompt, model)
            out.append(judged)
            print(f"Case judged {i}/{len(rows)}: {judged.get('task_id')}", flush=True)
        return out

    out: List[Any] = [None] * len(rows)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(judge_one, row, task_by_id, case_by_id, prompt, model): i for i, row in enumerate(rows)}
        for done, future in enumerate(as_completed(futures), start=1):
            idx = futures[future]
            judged = future.result()
            out[idx] = judged
            print(f"Case judged {done}/{len(rows)}: {judged.get('task_id')}", flush=True)
    return [r for r in out if r is not None]


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def aggregate(judged_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    parsed = [r.get("judge", {}) for r in judged_rows if isinstance(r.get("judge"), dict) and not r.get("judge", {}).get("parse_error")]
    parse_errors = len(judged_rows) - len(parsed)
    scores = {}
    for field in SCORE_FIELDS:
        vals = [_as_float(j.get(field)) for j in parsed if j.get(field) is not None]
        scores[field] = mean(vals) if vals else 0.0

    error_counts: Dict[str, int] = {}
    for j in parsed:
        for err in j.get("major_errors") or []:
            error_counts[str(err)] = error_counts.get(str(err), 0) + 1

    return {
        "n": len(judged_rows),
        "valid_judge_rows": len(parsed),
        "parse_errors": parse_errors,
        "score_means": scores,
        "major_error_counts": dict(sorted(error_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pred", required=True)
    p.add_argument("--eval", default="data/eval/cases/lowalt_case_eval_tasks.jsonl")
    p.add_argument("--cases", default="data/cases/lowalt_case_seed.jsonl")
    p.add_argument("--out", required=True)
    p.add_argument("--summary-out", required=True)
    p.add_argument("--prompt", default="prompts/judge_case_outcome.txt")
    p.add_argument("--judge-model", default="Qwen/Qwen3-32B")
    p.add_argument("--workers", type=int, default=1)
    args = p.parse_args()

    rows = read_jsonl(args.pred)
    tasks = read_jsonl(args.eval)
    cases = read_jsonl(args.cases)
    prompt = Path(args.prompt).read_text(encoding="utf-8")
    judged = judge_all(rows, tasks, cases, prompt, args.judge_model, args.workers)
    summary = aggregate(judged)
    write_jsonl(args.out, judged)
    save_json(args.summary_out, summary)
    print(f"Saved case judge scores to {args.out}")
    print(f"Saved case judge summary to {args.summary_out}")
    print(summary)


if __name__ == "__main__":
    main()
