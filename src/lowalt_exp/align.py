from collections import defaultdict
from typing import Dict, List

from .schema import EvidenceCell, RetrievalHit, TraceResult


ROLE_KEYWORDS = {
    "manufacturer": ["生产", "制造", "适航", "型号", "审定"],
    "operator": ["运营", "运行", "飞行", "操控员", "配送", "巡检"],
    "platform": ["平台", "服务系统", "数据接口", "航行服务"],
    "pilot": ["操控员", "飞手", "培训"],
    "regulator": ["监管", "公安", "民航", "空管"],
}

LEVEL_PRIORITY = {
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
    "国务院政策文件": 40,
    "部门政策文件": 35,
    "政策文件": 30,
}

NORM_FACET_PRIORITY = {
    "case_public_safety": -10,
    "case_cyber": -9,
    "case_secret": -8,
    "case_admin": -7,
    "case_civil_tort": -6,
    "case_agri_spray": -5,
    "case_allocation": -4,
    "case_product": -3,
    "case_insurance": -2,
    "hierarchy_conflict": 0,
    "norm_exception": 1,
    "norm_responsibility": 2,
    "norm_authorization": 3,
    "norm_prohibition": 4,
    "norm_obligation": 5,
    "legal_reasoning": 6,
}


def infer_role(text: str) -> str:
    for role, kws in ROLE_KEYWORDS.items():
        if any(k in text for k in kws):
            return role
    return "general"


def build_evidence_matrix(hits: List[RetrievalHit], trace: TraceResult) -> List[EvidenceCell]:
    groups = defaultdict(list)
    for h in hits:
        c = h.chunk
        role = infer_role(c.searchable_text())
        key = (h.facet, c.legal_level, c.jurisdiction, c.source_type, c.validity, role)
        groups[key].append(h)
    cells = []
    for (facet, level, jurisdiction, source_type, validity, role), hs in groups.items():
        hs.sort(key=lambda x: x.score, reverse=True)
        cells.append(EvidenceCell(facet, level, jurisdiction, source_type, validity, role, hs))
    cells.sort(
        key=lambda cell: (
            NORM_FACET_PRIORITY.get(cell.facet, 20),
            cell.facet,
            -LEVEL_PRIORITY.get(cell.legal_level, 0),
            cell.jurisdiction,
        )
    )
    return cells


def select_aligned_hits(cells: List[EvidenceCell], top_k: int = 12) -> List[RetrievalHit]:
    selected = []
    seen = set()
    # One pass: keep best evidence from each facet-level group. Norm-structure
    # facets are intentionally represented because the answer must cover rights,
    # duties, prohibitions, responsibilities and exceptions, not just obligations.
    for cell in cells:
        router_hits = [h for h in cell.hits if h.query == "case_source_router"]
        if cell.facet.startswith("case_") and len(router_hits) > 1:
            ordered_hits = router_hits + [h for h in cell.hits if h.query != "case_source_router"]
            per_cell = 2
        else:
            ordered_hits = cell.hits
            per_cell = 1
        picked = 0
        for h in ordered_hits:
            if h.chunk.article_id in seen:
                continue
            selected.append(h)
            seen.add(h.chunk.article_id)
            picked += 1
            if picked >= per_cell:
                break
    # Fill remaining by score.
    all_hits = []
    for cell in cells:
        all_hits.extend(cell.hits)
    all_hits.sort(key=lambda x: x.score, reverse=True)
    for h in all_hits:
        if len(selected) >= top_k:
            break
        if h.chunk.article_id not in seen:
            selected.append(h)
            seen.add(h.chunk.article_id)
    for i, h in enumerate(selected[:top_k], start=1):
        h.rank = i
    return selected[:top_k]


def matrix_to_markdown(cells: List[EvidenceCell]) -> str:
    lines = [
        "| facet | legal_level | jurisdiction | validity | role | norm_types | top evidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in cells:
        top = cell.hits[0].chunk if cell.hits else None
        ev = f"{top.article_id}: {top.title_zh} {top.article_no}" if top else ""
        norm_types = ", ".join(top.norm_types) if top else ""
        lines.append(f"| {cell.facet} | {cell.legal_level} | {cell.jurisdiction} | {cell.validity} | {cell.role} | {norm_types} | {ev} |")
    return "\n".join(lines)
