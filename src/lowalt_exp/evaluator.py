import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean
from typing import Dict, List

from .align import build_evidence_matrix, select_aligned_hits
from .generator import llm_answer, offline_answer
from .io_utils import load_corpus, read_jsonl, save_json, write_jsonl
from .metrics import compute_metrics
from .resolve import BASELINE_DISABLED_RULES, resolve_conflicts
from .retrieve import Retriever
from .trace import trace_question


def run_one(task, retriever: Retriever, args):
    q = task["question"]
    trace = trace_question(q, disabled_facets=args.disable_facet or [])
    if args.mode == "bm25":
        hits = retriever.retrieve_plain(q, top_k=args.top_k)
        cells = build_evidence_matrix(hits, trace)
        disabled = BASELINE_DISABLED_RULES
    elif args.mode == "multiquery":
        hits = retriever.retrieve_trace(trace, prefetch_k=args.prefetch_k, final_k=args.top_k)
        cells = build_evidence_matrix(hits, trace)
        disabled = BASELINE_DISABLED_RULES
    elif args.mode == "trace_align":
        raw = retriever.retrieve_trace(trace, prefetch_k=args.prefetch_k, final_k=args.prefetch_k)
        if args.use_rerank:
            raw = retriever.rerank(q, raw, top_k=args.prefetch_k)
        cells = build_evidence_matrix(raw, trace)
        hits = select_aligned_hits(cells, top_k=args.top_k)
        disabled = BASELINE_DISABLED_RULES
    else:
        raw = retriever.retrieve_trace(trace, prefetch_k=args.prefetch_k, final_k=args.prefetch_k)
        if args.use_rerank:
            raw = retriever.rerank(q, raw, top_k=args.prefetch_k)
        cells = build_evidence_matrix(raw, trace)
        hits = select_aligned_hits(cells, top_k=args.top_k)
        disabled = args.disable_rule or []
    resolve = resolve_conflicts(trace, cells, disabled_rules=disabled)
    if args.no_llm:
        answer = offline_answer(q, trace, hits, cells, resolve)
    else:
        answer = llm_answer(q, trace, hits, cells, resolve, model=args.model, task=task)
    hit_dicts = [h.to_dict() for h in hits]
    metrics = compute_metrics(task, hit_dicts, answer)
    return {
        "task_id": task.get("task_id"),
        "case_id": task.get("case_id"),
        "task_type": task.get("task_type"),
        "question": q,
        "gold_source_ids": task.get("gold_source_ids", []),
        "gold_case_outcome": task.get("gold_case_outcome"),
        "expected_case_points": task.get("expected_case_points", []),
        "must_cover_facets": task.get("must_cover_facets", []),
        "must_cover_norm_types": task.get("must_cover_norm_types", []),
        "abstain_expected": task.get("abstain_expected"),
        "mode": args.mode,
        "trace": {"slots": trace.slots, "facets": trace.facets, "warnings": trace.warnings},
        "resolve": {"rules_applied": resolve.rules_applied, "warnings": resolve.warnings, "must_abstain": resolve.must_abstain, "abstain_reason": resolve.abstain_reason},
        "hits": hit_dicts,
        "answer": answer,
        "metrics": metrics,
    }


def aggregate(rows: List[Dict]) -> Dict:
    metrics = rows[0]["metrics"].keys() if rows else []
    agg = {m: mean([r["metrics"].get(m, 0.0) for r in rows]) for m in metrics}
    by_type = {}
    for r in rows:
        t = r.get("task_type", "unknown")
        by_type.setdefault(t, []).append(r)
    agg_by_type = {}
    for t, rs in by_type.items():
        agg_by_type[t] = {m: mean([r["metrics"].get(m, 0.0) for r in rs]) for m in metrics}
    return {"n": len(rows), "overall": agg, "by_task_type": agg_by_type}


def run_all(tasks: List[Dict], retriever: Retriever, args) -> List[Dict]:
    workers = max(1, int(args.workers))
    if workers == 1:
        rows = []
        for i, task in enumerate(tasks, start=1):
            row = run_one(task, retriever, args)
            rows.append(row)
            print(f"Completed {i}/{len(tasks)}: {row.get('task_id')}", flush=True)
        return rows

    rows = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, task, retriever, args): i for i, task in enumerate(tasks)}
        for done, future in enumerate(as_completed(futures), start=1):
            idx = futures[future]
            row = future.result()
            rows[idx] = row
            print(f"Completed {done}/{len(tasks)}: {row.get('task_id')}", flush=True)
    return [r for r in rows if r is not None]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default="data/processed/corpus.jsonl")
    p.add_argument("--eval", default="data/eval/xl/lowaltbench_xl_1200.jsonl")
    p.add_argument("--out", default="outputs/full/eval_tarrag.json")
    p.add_argument("--pred-out", default=None)
    p.add_argument("--mode", default="tarrag", choices=["bm25", "multiquery", "trace_align", "tarrag"])
    p.add_argument("--top-k", type=int, default=12)
    p.add_argument("--prefetch-k", type=int, default=50)
    p.add_argument("--use-rerank", action="store_true")
    p.add_argument("--model", default="Qwen/Qwen3-8B")
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--disable-facet", action="append", default=[])
    p.add_argument("--disable-rule", action="append", default=[])
    p.add_argument("--workers", type=int, default=1, help="Number of parallel tasks to run.")
    args = p.parse_args()

    corpus = load_corpus(args.corpus)
    tasks = read_jsonl(args.eval)
    retriever = Retriever(corpus)
    rows = run_all(tasks, retriever, args)
    report = aggregate(rows)
    save_json(args.out, report)
    pred_out = args.pred_out or args.out.replace(".json", "_predictions.jsonl")
    write_jsonl(pred_out, rows)
    print(f"Saved report to {args.out}")
    print(f"Saved predictions to {pred_out}")
    print(report)


if __name__ == "__main__":
    main()
