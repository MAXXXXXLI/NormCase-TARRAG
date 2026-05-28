#!/usr/bin/env python3
"""Build compact JSON assets for the GitHub Pages web app."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data/processed/corpus_case_enhanced.jsonl"
CASES_PATH = ROOT / "data/cases/lowalt_case_seed.jsonl"
TASKS_PATH = ROOT / "data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl"
OUT_DIR = ROOT / "docs/data"

LEGAL_LEVEL_PRIORITY = {
    "法律": 100,
    "行政法规": 90,
    "司法解释": 85,
    "部门规章": 80,
    "地方性法规": 75,
    "经济特区法规": 75,
    "设区的市地方性法规": 75,
    "地方政府规章": 70,
    "地方行政规范性文件": 60,
    "部门规范性文件": 60,
    "部门公告": 58,
    "部门公告/通告": 58,
    "强制性国家标准": 55,
    "民航行业标准": 50,
    "推荐性国家标准": 45,
    "国务院政策文件": 40,
    "部门政策文件": 35,
    "政策文件": 30,
}

NORM_PATTERNS = {
    "authorization": [r"有权", r"可以", r"可依法", r"申请", r"请求", r"投诉", r"举报", r"复评", r"异议", r"支持", r"推动"],
    "obligation": [r"应当", r"必须", r"需要", r"须", r"应依法", r"应遵守", r"应取得", r"应履行", r"应建立", r"应采取", r"应提交", r"应申报", r"应核验", r"应开展", r"依法.*履行", r"建立", r"采取"],
    "prohibition": [r"不得", r"禁止", r"严禁", r"不得.*从事", r"不得.*利用", r"不得.*提供"],
    "responsibility": [r"承担.*责任", r"主体责任", r"法律责任", r"民事责任", r"刑事责任", r"处罚", r"罚款", r"警告", r"责令", r"追究", r"处分"],
    "exception": [r"但是", r"但书", r"除.*外", r"另有规定", r"不适用", r"可以不", r"从其规定", r"依照其规定"],
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def infer_norm_types(text: str) -> list[str]:
    found: list[str] = []
    for norm_type, patterns in NORM_PATTERNS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            found.append(norm_type)
    return found or ["general_rule"]


def infer_exception_markers(text: str) -> list[str]:
    markers: list[str] = []
    for marker in ["但是", "法律另有规定", "行政法规另有规定", "另有规定", "除", "不适用", "从其规定", "依照其规定", "可以不"]:
        if marker in text:
            markers.append(marker)
    return list(dict.fromkeys(markers))


def compact_chunk(row: dict[str, Any], idx: int) -> dict[str, Any]:
    text = str(row.get("text", ""))
    legal_level = row.get("legal_level", "")
    norm_types = row.get("norm_types") or infer_norm_types(text)
    exception_markers = row.get("exception_markers") or infer_exception_markers(text)
    return {
        "idx": idx,
        "article_id": row.get("article_id", ""),
        "source_id": row.get("source_id", ""),
        "title_zh": row.get("title_zh", ""),
        "jurisdiction": row.get("jurisdiction", ""),
        "issuing_authority": row.get("issuing_authority", ""),
        "source_type": row.get("source_type", ""),
        "legal_level": legal_level,
        "url": row.get("url", ""),
        "landing_url": row.get("landing_url", ""),
        "promulgation_date": row.get("promulgation_date", ""),
        "publication_date": row.get("publication_date", ""),
        "effective_date": str(row.get("effective_date", "")),
        "validity": row.get("validity", ""),
        "coverage_role": row.get("coverage_role", ""),
        "themes": row.get("themes") or [],
        "article_no": row.get("article_no", ""),
        "text": text,
        "char_len": int(row.get("char_len") or len(text)),
        "norm_types": norm_types,
        "exception_markers": exception_markers,
        "authority_rank": int(row.get("authority_rank") or LEGAL_LEVEL_PRIORITY.get(legal_level, 0)),
    }


def build_sources(corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in corpus:
        grouped[item["source_id"]].append(item)

    sources: list[dict[str, Any]] = []
    for source_id, rows in grouped.items():
        first = rows[0]
        theme_counter = Counter(theme for row in rows for theme in row.get("themes", []))
        norm_counter = Counter(norm for row in rows for norm in row.get("norm_types", []))
        sources.append(
            {
                "source_id": source_id,
                "title_zh": first.get("title_zh", ""),
                "jurisdiction": first.get("jurisdiction", ""),
                "issuing_authority": first.get("issuing_authority", ""),
                "source_type": first.get("source_type", ""),
                "legal_level": first.get("legal_level", ""),
                "url": first.get("url", ""),
                "landing_url": first.get("landing_url", ""),
                "promulgation_date": first.get("promulgation_date", ""),
                "publication_date": first.get("publication_date", ""),
                "effective_date": first.get("effective_date", ""),
                "validity": first.get("validity", ""),
                "coverage_role": first.get("coverage_role", ""),
                "article_count": len(rows),
                "char_len": sum(row.get("char_len", 0) for row in rows),
                "themes": [name for name, _ in theme_counter.most_common(12)],
                "norm_types": [name for name, _ in norm_counter.most_common(6)],
                "first_article_id": rows[0].get("article_id", ""),
            }
        )
    sources.sort(key=lambda s: (-LEGAL_LEVEL_PRIORITY.get(s["legal_level"], 0), s["jurisdiction"], s["title_zh"]))
    return sources


def build_stats(corpus: list[dict[str, Any]], sources: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "chunk_count": len(corpus),
        "source_count": len(sources),
        "case_count": len(cases),
        "char_count": sum(row.get("char_len", 0) for row in corpus),
        "legal_levels": Counter(row.get("legal_level", "") for row in corpus).most_common(),
        "jurisdictions": Counter(row.get("jurisdiction", "") for row in corpus).most_common(),
        "validity": Counter(row.get("validity", "") for row in corpus).most_common(),
        "source_types": Counter(row.get("source_type", "") for row in corpus).most_common(),
        "norm_types": Counter(norm for row in corpus for norm in row.get("norm_types", [])).most_common(),
        "generated_from": "data/processed/corpus_case_enhanced.jsonl",
    }


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    corpus = [compact_chunk(row, idx) for idx, row in enumerate(read_jsonl(CORPUS_PATH))]
    cases = read_jsonl(CASES_PATH)
    tasks = read_jsonl(TASKS_PATH)
    sources = build_sources(corpus)
    stats = build_stats(corpus, sources, cases)

    write_json(OUT_DIR / "corpus.json", corpus)
    write_json(OUT_DIR / "sources.json", sources)
    write_json(OUT_DIR / "stats.json", stats)
    write_json(OUT_DIR / "cases.json", cases)
    write_json(OUT_DIR / "case_tasks.json", tasks)
    print(f"wrote {len(corpus)} chunks, {len(sources)} sources, {len(cases)} cases to {OUT_DIR}")


if __name__ == "__main__":
    main()
