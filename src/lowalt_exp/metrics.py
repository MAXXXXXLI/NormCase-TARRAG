import math
import re
from typing import Any, Dict, List, Sequence


def _hit_match(item: Dict[str, Any], gold_article_ids: Sequence[str], gold_source_ids: Sequence[str]) -> bool:
    return item.get("article_id") in gold_article_ids or item.get("source_id") in gold_source_ids


def recall_at_k(hits: List[Dict[str, Any]], gold_article_ids: Sequence[str], gold_source_ids: Sequence[str], k: int) -> float:
    if not gold_article_ids and not gold_source_ids:
        return 0.0
    top = hits[:k]
    matched = set()
    gold_total = len(set(gold_article_ids) | set(gold_source_ids))
    for h in top:
        if h.get("article_id") in gold_article_ids:
            matched.add(h.get("article_id"))
        if h.get("source_id") in gold_source_ids:
            matched.add(h.get("source_id"))
    return len(matched) / max(1, gold_total)


def mrr_at_k(hits: List[Dict[str, Any]], gold_article_ids: Sequence[str], gold_source_ids: Sequence[str], k: int) -> float:
    for i, h in enumerate(hits[:k], start=1):
        if _hit_match(h, gold_article_ids, gold_source_ids):
            return 1.0 / i
    return 0.0


def ndcg_at_k(hits: List[Dict[str, Any]], gold_article_ids: Sequence[str], gold_source_ids: Sequence[str], k: int) -> float:
    gains = []
    for h in hits[:k]:
        gains.append(1.0 if _hit_match(h, gold_article_ids, gold_source_ids) else 0.0)
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(gains))
    ideal = sorted(gains, reverse=True)
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def facet_coverage(hits: List[Dict[str, Any]], must_cover_facets: Sequence[str]) -> float:
    if not must_cover_facets:
        return 0.0
    facets = {h.get("facet", "general") for h in hits}
    return len(set(must_cover_facets) & facets) / len(set(must_cover_facets))


def norm_type_coverage(hits: List[Dict[str, Any]], must_cover_norm_types: Sequence[str]) -> float:
    if not must_cover_norm_types:
        return 0.0
    norm_types = set()
    for h in hits:
        for norm_type in h.get("norm_types", []) or []:
            norm_types.add(norm_type)
    return len(set(must_cover_norm_types) & norm_types) / len(set(must_cover_norm_types))


def conflict_evidence_recall(hits: List[Dict[str, Any]], task: Dict[str, Any]) -> float:
    ctype = task.get("conflict_type")
    if not ctype:
        return 0.0
    sources = {h.get("source_id") for h in hits}
    gold_sources = set(task.get("gold_source_ids", []))
    if ctype in ["national_local", "data_flight", "current_future", "law_standard"]:
        return 1.0 if len(sources & gold_sources) >= min(2, len(gold_sources)) else 0.0
    if ctype == "evidence_gap":
        return 1.0 if len(sources & gold_sources) >= 1 else 0.0
    return 0.0


def workflow_step_coverage(answer: str, expected_steps: Sequence[str]) -> float:
    if not expected_steps:
        return 0.0
    matched = 0
    for s in expected_steps:
        if s and s in answer:
            matched += 1
    return matched / len(expected_steps)


def citation_precision(answer: str, hits: List[Dict[str, Any]]) -> float:
    cites = re.findall(r"\[([^\[\]]+::[^\[\]]+)\]", answer)
    if not cites:
        return 0.0
    allowed = {h.get("article_id") for h in hits}
    return sum(1 for c in cites if c in allowed) / len(cites)


def abstention_accuracy(answer: str, task: Dict[str, Any]) -> float:
    expected = bool(task.get("abstain_expected", False))
    # Strong refusal means the model does not give a final permission/conclusion.
    # Merely reminding users to verify real-time airspace is not counted as abstention
    # for normal workflow tasks.
    strong_markers = ["不能仅凭静态法规语料判断最终", "不能仅凭", "无法给出最终", "不能直接判断", "不应直接判断"]
    did = any(m in answer for m in strong_markers)
    return 1.0 if did == expected else 0.0


def future_rule_misuse(answer: str, hits: List[Dict[str, Any]]) -> float:
    def is_future_validity(value: str) -> bool:
        value = str(value or "").lower()
        return "future" in value or "not_yet_effective" in value or "尚未施行" in value

    has_future = any(is_future_validity(h.get("validity")) for h in hits)
    if not has_future:
        return 0.0
    safe_markers = ["未来施行", "前瞻", "不能直接", "尚未施行", "施行日期"]
    return 0.0 if any(m in answer for m in safe_markers) else 1.0


def compute_metrics(task: Dict[str, Any], hits: List[Dict[str, Any]], answer: str) -> Dict[str, float]:
    gold_a = task.get("gold_article_ids", [])
    gold_s = task.get("gold_source_ids", [])
    return {
        "recall_at_5": recall_at_k(hits, gold_a, gold_s, 5),
        "recall_at_10": recall_at_k(hits, gold_a, gold_s, 10),
        "mrr_at_10": mrr_at_k(hits, gold_a, gold_s, 10),
        "ndcg_at_10": ndcg_at_k(hits, gold_a, gold_s, 10),
        "facet_coverage": facet_coverage(hits, task.get("must_cover_facets", [])),
        "norm_type_coverage": norm_type_coverage(hits, task.get("must_cover_norm_types", [])),
        "conflict_evidence_recall": conflict_evidence_recall(hits, task),
        "workflow_step_coverage": workflow_step_coverage(answer, task.get("expected_workflow_steps", [])),
        "citation_precision": citation_precision(answer, hits),
        "abstention_accuracy": abstention_accuracy(answer, task),
        "future_rule_misuse": future_rule_misuse(answer, hits),
    }
