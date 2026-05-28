import argparse
import json

from .align import build_evidence_matrix, select_aligned_hits
from .generator import llm_answer, offline_answer
from .io_utils import load_corpus
from .resolve import BASELINE_DISABLED_RULES, resolve_conflicts
from .retrieve import Retriever
from .trace import trace_question


def run_pipeline(args):
    corpus = load_corpus(args.corpus)
    retriever = Retriever(corpus)
    trace = trace_question(args.question, disabled_facets=args.disable_facet or [])

    if args.mode == "bm25":
        hits = retriever.retrieve_plain(args.question, top_k=args.top_k)
        cells = build_evidence_matrix(hits, trace)
    elif args.mode == "multiquery":
        hits = retriever.retrieve_trace(trace, prefetch_k=args.prefetch_k, final_k=args.top_k)
        cells = build_evidence_matrix(hits, trace)
    elif args.mode == "trace_align":
        raw_hits = retriever.retrieve_trace(trace, prefetch_k=args.prefetch_k, final_k=args.prefetch_k)
        if args.use_rerank:
            raw_hits = retriever.rerank(args.question, raw_hits, top_k=args.prefetch_k)
        cells = build_evidence_matrix(raw_hits, trace)
        hits = select_aligned_hits(cells, top_k=args.top_k)
    elif args.mode == "tarrag":
        raw_hits = retriever.retrieve_trace(trace, prefetch_k=args.prefetch_k, final_k=args.prefetch_k)
        if args.use_rerank:
            raw_hits = retriever.rerank(args.question, raw_hits, top_k=args.prefetch_k)
        cells = build_evidence_matrix(raw_hits, trace)
        hits = select_aligned_hits(cells, top_k=args.top_k)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")

    resolve = resolve_conflicts(trace, cells, disabled_rules=args.disable_rule or []) if args.mode == "tarrag" else resolve_conflicts(trace, cells, disabled_rules=BASELINE_DISABLED_RULES)

    if args.no_llm:
        answer = offline_answer(args.question, trace, hits, cells, resolve)
    else:
        answer = llm_answer(args.question, trace, hits, cells, resolve, model=args.model)

    result = {
        "question": args.question,
        "mode": args.mode,
        "trace": {"slots": trace.slots, "facets": trace.facets, "subqueries": trace.subqueries, "warnings": trace.warnings},
        "resolve": {"rules_applied": resolve.rules_applied, "warnings": resolve.warnings, "must_abstain": resolve.must_abstain, "abstain_reason": resolve.abstain_reason},
        "hits": [h.to_dict() for h in hits],
        "answer": answer,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(answer)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default="data/processed/corpus.jsonl")
    p.add_argument("--question", required=True)
    p.add_argument("--mode", default="tarrag", choices=["bm25", "multiquery", "trace_align", "tarrag"])
    p.add_argument("--top-k", type=int, default=12)
    p.add_argument("--prefetch-k", type=int, default=50)
    p.add_argument("--use-rerank", action="store_true")
    p.add_argument("--model", default="Qwen/Qwen3-8B")
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--disable-facet", action="append", default=[])
    p.add_argument("--disable-rule", action="append", default=[])
    args = p.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
