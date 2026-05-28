import argparse
import json
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .io_utils import save_json


def _read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _load_source_vocab(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("source vocab must be a JSON list")
    return data


def audit(corpus_path: str, source_vocab_path: str, eval_path: str) -> Dict[str, Any]:
    sources: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    corpus_rows = 0
    corpus_category_counts = Counter()
    corpus_chunk_counts = Counter()
    for row in _read_jsonl(corpus_path):
        corpus_rows += 1
        sid = row.get("source_id", "")
        corpus_chunk_counts[sid] += 1
        if sid not in sources:
            sources[sid] = {
                "source_id": sid,
                "title_zh": row.get("title_zh", ""),
                "legal_level": row.get("legal_level", ""),
                "source_type": row.get("source_type", ""),
                "jurisdiction": row.get("jurisdiction", ""),
                "effective_date": row.get("effective_date", ""),
            }
        corpus_category_counts[row.get("legal_level") or row.get("source_type") or "unknown"] += 1

    vocab_rows = _load_source_vocab(source_vocab_path)
    vocab_by_id = OrderedDict((row["source_id"], row) for row in vocab_rows)
    vocab_category_counts = Counter(row.get("source_type", "unknown") for row in vocab_rows)

    missing_from_corpus = [sid for sid in vocab_by_id if sid not in sources]
    extra_in_corpus = [sid for sid in sources if sid not in vocab_by_id]
    chunk_count_mismatches = [
        {
            "source_id": sid,
            "vocab_chunk_count": vocab_by_id[sid].get("chunk_count"),
            "corpus_chunk_count": corpus_chunk_counts[sid],
        }
        for sid in vocab_by_id
        if sid in corpus_chunk_counts and vocab_by_id[sid].get("chunk_count") != corpus_chunk_counts[sid]
    ]

    eval_rows = 0
    task_types = Counter()
    gold_sources = set()
    for row in _read_jsonl(eval_path):
        eval_rows += 1
        task_types[row.get("task_type", "unknown")] += 1
        gold_sources.update(row.get("gold_source_ids", []) or [])

    gold_not_in_corpus = sorted(gold_sources.difference(sources))
    complete = (
        len(vocab_rows) == 88
        and len(sources) == 88
        and corpus_rows == 5173
        and not missing_from_corpus
        and not extra_in_corpus
        and not chunk_count_mismatches
        and not gold_not_in_corpus
    )

    return {
        "complete_lowaltbench_xl": complete,
        "corpus_path": corpus_path,
        "source_vocab_path": source_vocab_path,
        "eval_path": eval_path,
        "corpus_rows": corpus_rows,
        "corpus_source_count": len(sources),
        "source_vocab_count": len(vocab_rows),
        "eval_task_count": eval_rows,
        "eval_gold_source_count": len(gold_sources),
        "source_categories": dict(vocab_category_counts),
        "corpus_chunk_categories": dict(corpus_category_counts),
        "task_types": dict(task_types),
        "missing_from_corpus": missing_from_corpus,
        "extra_in_corpus": extra_in_corpus,
        "chunk_count_mismatches": chunk_count_mismatches,
        "gold_not_in_corpus": gold_not_in_corpus,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default="data/processed/corpus.jsonl")
    p.add_argument("--source-vocab", default="configs/source_id_vocab_full.json")
    p.add_argument("--eval", default="data/eval/xl/lowaltbench_xl_1200.jsonl")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    report = audit(args.corpus, args.source_vocab, args.eval)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        save_json(args.out, report)


if __name__ == "__main__":
    main()
