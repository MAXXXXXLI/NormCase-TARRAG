from typing import List

from .schema import EvidenceCell, ResolveResult, TraceResult


BASELINE_DISABLED_RULES = [
    "local_specific_over_general",
    "law_over_standard",
    "current_over_future",
    "role_separation",
    "abstain_when_realtime",
    "norm_type_completeness",
    "exception_rule_check",
    "hierarchy_conflict_order",
    "deductive_subsumption",
]


def _cell_facets(cells: List[EvidenceCell]) -> set[str]:
    return {c.facet for c in cells}


def _top_chunks(cells: List[EvidenceCell]):
    for cell in cells:
        if cell.hits:
            yield cell.hits[0].chunk


def resolve_conflicts(trace: TraceResult, cells: List[EvidenceCell], disabled_rules: List[str] = None) -> ResolveResult:
    disabled_rules = disabled_rules or []
    rules_applied: List[str] = []
    warnings: List[str] = []
    must_abstain = False
    abstain_reason = None

    has_local = any(c.jurisdiction not in ["", "CN", "全国"] and c.facet == "local" for c in cells)
    has_national = any(c.jurisdiction in ["CN", "全国"] for c in cells)
    has_standard = any("标准" in c.legal_level or "standard" in c.facet for c in cells)
    has_law_or_rule = any(c.legal_level in ["法律", "行政法规", "部门规章", "地方性法规", "经济特区法规", "地方政府规章"] for c in cells)
    has_future = any(c.validity == "future_effective" or "future" in c.validity for c in cells)
    facets = _cell_facets(cells)
    norm_types = {norm for chunk in _top_chunks(cells) for norm in chunk.norm_types}
    has_exception = "exception" in norm_types or any(chunk.exception_markers for chunk in _top_chunks(cells))
    broad_review = any(f.startswith("norm_") for f in trace.facets)

    if "local_specific_over_general" not in disabled_rules and has_local and has_national:
        rules_applied.append("local_specific_over_general")
        warnings.append("地方规则应作为属地执行要求，与国家规则共同适用，而不是替代国家底线。")

    if "law_over_standard" not in disabled_rules and has_standard and has_law_or_rule:
        rules_applied.append("law_over_standard")
        warnings.append("法律、行政法规和规章给出义务边界；技术标准主要补充技术实现、接口或流程细节。")

    if "current_over_future" not in disabled_rules and has_future:
        rules_applied.append("current_over_future")
        warnings.append("检索到未来施行规则；当前合规判断不能直接把未来施行文本当作现行依据。")

    if "role_separation" not in disabled_rules:
        roles = {c.role for c in cells}
        if len(roles - {"general"}) >= 2:
            rules_applied.append("role_separation")
            warnings.append("制造商、运营人、平台、操控员的义务应分开说明，避免职责混用。")

    if "norm_type_completeness" not in disabled_rules and broad_review:
        rules_applied.append("norm_type_completeness")
        missing = []
        required = {
            "norm_authorization": ("authorization", "授权/权利/可为事项"),
            "norm_obligation": ("obligation", "义务/命令性要求"),
            "norm_prohibition": ("prohibition", "禁止性要求"),
            "norm_responsibility": ("responsibility", "责任/处罚/救济后果"),
            "norm_exception": ("exception", "例外或但书"),
        }
        for facet, (norm_type, label) in required.items():
            if facet not in facets and norm_type not in norm_types:
                missing.append(label)
        if missing:
            warnings.append("完整规范审查不能只列义务；当前证据矩阵缺少：" + "、".join(missing) + "。")
        else:
            warnings.append("已按授权、义务、禁止、责任和例外五类规范组织证据，后续结论需逐项引用。")

    if "exception_rule_check" not in disabled_rules:
        if "norm_exception" in trace.facets or has_exception:
            rules_applied.append("exception_rule_check")
            warnings.append("存在但书、另有规定、除外或不适用结构；结论应先说明一般规则，再审查例外是否改变适用结果。")

    if "hierarchy_conflict_order" not in disabled_rules:
        if "hierarchy_conflict" in trace.facets or (has_local and has_national) or (has_standard and has_law_or_rule):
            rules_applied.append("hierarchy_conflict_order")
            warnings.append(
                "冲突处理顺序：先确认同地域、同主体、同事项、同期间是否构成真实冲突；真实冲突再按上位法优于下位法、特别规定优于一般规定、新规定优于旧规定处理。政策文件和规范性文件不得突破上位法或增设责任依据。"
            )

    if "deductive_subsumption" not in disabled_rules and broad_review:
        rules_applied.append("deductive_subsumption")
        warnings.append("最终结论应采用法律三段论：以已确认有效且适用的规范为大前提，以场景事实为小前提，经构成要件涵摄推出法律效果、责任或合规风险。")

    if "abstain_when_realtime" not in disabled_rules:
        if trace.warnings:
            rules_applied.append("abstain_when_realtime")
            must_abstain = True
            abstain_reason = "问题涉及具体时间、点位、临时管制、医院/机场周边或实时空域，静态法规语料不能直接判断是否允许起飞。"
            warnings.append(abstain_reason)

    return ResolveResult(rules_applied, warnings, must_abstain, abstain_reason)
