import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .io_utils import read_jsonl, write_jsonl


def _key(row: Dict[str, Any]) -> str:
    return str(row.get("article_id") or "")


def merge_rows(base_rows: Iterable[Dict[str, Any]], supplemental_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()
    for row in list(base_rows) + list(supplemental_rows):
        key = _key(row)
        if not key or key in seen:
            continue
        rows.append(row)
        seen.add(key)
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="data/processed/corpus.jsonl")
    p.add_argument("--supplemental", default="data/supplemental/case_responsibility_rules.jsonl")
    p.add_argument("--out", default="data/processed/corpus_case_enhanced.jsonl")
    p.add_argument("--manifest-out", default="outputs/final/corpus_case_enhanced_manifest.json")
    args = p.parse_args()

    base_rows = read_jsonl(args.base)
    supplemental_rows = read_jsonl(args.supplemental)
    merged = merge_rows(base_rows, supplemental_rows)
    write_jsonl(args.out, merged)
    Path(args.manifest_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest_out).write_text(
        json.dumps(
            {
                "base": args.base,
                "supplemental": args.supplemental,
                "out": args.out,
                "base_rows": len(base_rows),
                "supplemental_rows": len(supplemental_rows),
                "merged_rows": len(merged),
                "supplemental_source_ids": sorted({r.get("source_id") for r in supplemental_rows}),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved enhanced corpus to {args.out} ({len(merged)} rows)")


if __name__ == "__main__":
    main()
