from pathlib import Path
from typing import Any, Dict, List, Optional

from .align import matrix_to_markdown
from .schema import EvidenceCell, ResolveResult, RetrievalHit, TraceResult
from .siliconflow import SiliconFlowClient


def format_evidence(hits: List[RetrievalHit]) -> str:
    lines = []
    for h in hits:
        c = h.chunk
        lines.append(
            f"[{c.article_id}] {c.title_zh}｜{c.legal_level}｜{c.jurisdiction}｜{c.validity}｜{c.article_no}｜norm={','.join(c.norm_types)}\n{c.text}"
        )
    return "\n\n".join(lines)


def _citations_for(hits: List[RetrievalHit], facets: List[str], limit: int = 3) -> str:
    norm_type_names = {"authorization", "obligation", "prohibition", "responsibility", "exception"}
    cites = []
    for h in hits:
        if any(norm in h.chunk.norm_types for norm in facets):
            cites.append(f"[{h.chunk.article_id}]")
            continue
        if any(facet in norm_type_names for facet in facets):
            continue
        if h.facet in facets:
            cites.append(f"[{h.chunk.article_id}]")
    return ", ".join(list(dict.fromkeys(cites))[:limit])


def _location_compatible(hit: RetrievalHit, trace: TraceResult) -> bool:
    loc = str(trace.slots.get("location", ""))
    jurisdiction = hit.chunk.jurisdiction
    if not loc or loc == "全国":
        return True
    return jurisdiction in ["", "CN", "全国", loc]


def _step_hits(hits: List[RetrievalHit], trace: TraceResult, facets: List[str]) -> List[RetrievalHit]:
    loc = str(trace.slots.get("location", ""))
    rows = []
    for h in hits:
        if not _location_compatible(h, trace):
            continue
        c = h.chunk
        themes = set(c.themes)
        if h.facet in facets:
            rows.append(h)
        elif "local" in facets and (c.jurisdiction == loc or "local" in themes):
            rows.append(h)
        elif "standard" in facets and ("标准" in c.legal_level or "standard" in themes):
            rows.append(h)
        elif "data_security" in facets and themes & {"data_security", "personal_information", "surveying_mapping", "geographic_information"}:
            rows.append(h)
        elif "registration" in facets and ("registration" in themes or "登记" in c.text):
            rows.append(h)
        elif "operation" in facets and themes & {"operation", "operator", "safety"}:
            rows.append(h)
        elif "airspace" in facets and (themes & {"airspace", "flight_application"} or "空域" in c.text):
            rows.append(h)
    deduped = []
    seen = set()
    for h in rows:
        if h.chunk.article_id in seen:
            continue
        deduped.append(h)
        seen.add(h.chunk.article_id)
    return deduped


def offline_answer(question: str, trace: TraceResult, hits: List[RetrievalHit], cells: List[EvidenceCell], resolve: ResolveResult) -> str:
    slots = trace.slots
    lines = []
    lines.append("## 1. 场景识别")
    lines.append(f"地点：{slots.get('location')}；角色：{slots.get('actor')}；航空器：{slots.get('aircraft')}；场景：{slots.get('scenario')}；数据活动：{', '.join(slots.get('data_activity') or []) or '未明确'}。")
    lines.append("\n## 2. 结论摘要")
    if resolve.must_abstain:
        lines.append(f"不能仅凭静态法规语料判断最终能否执行；原因：{resolve.abstain_reason}")
    else:
        lines.append("该场景通常需要先确认规则层级和适用条件，再分别核验可为事项、义务、禁止、责任、例外，以及航空器登记/运行识别、空域或飞行计划、运营安全管理、地方属地要求、数据安全和技术标准要求。")
    lines.append("\n## 3. 法律规范结构审查")
    norm_rows = [
        ("授权/权利/可为事项", ["norm_authorization", "authorization"]),
        ("义务/命令性要求", ["norm_obligation", "obligation"]),
        ("禁止性要求", ["norm_prohibition", "prohibition"]),
        ("责任/处罚/救济后果", ["norm_responsibility", "responsibility"]),
        ("例外/但书/不适用", ["norm_exception", "exception"]),
    ]
    for label, facets in norm_rows:
        cites = _citations_for(hits, facets)
        if cites:
            lines.append(f"- {label}：需要在相应证据下单独判断，避免把全部规则压缩成义务清单。{cites}")
    if _citations_for(hits, ["hierarchy_conflict"]):
        lines.append(f"- 位阶与冲突：先确认是否存在同地域、同主体、同事项、同期间的真实冲突，再处理上位法/特别法/新旧法关系。{_citations_for(hits, ['hierarchy_conflict'])}")
    lines.append("\n## 4. 分步骤合规工作流")
    step_map = [
        ("航空器与主体准备", ["registration", "operation"]),
        ("空域/飞行计划/审批核验", ["airspace"]),
        ("运行安全管理", ["operation"]),
        ("地方属地规则核验", ["local"]),
        ("数据安全与测绘/个人信息评估", ["data_security"]),
        ("技术标准/接口/航线设计", ["standard"]),
    ]
    step_no = 1
    for name, facets in step_map:
        evs = _step_hits(hits, trace, facets)
        if not evs:
            continue
        cites = ", ".join(f"[{h.chunk.article_id}]" for h in evs[:2])
        lines.append(f"{step_no}. {name}：依据相关证据进行核验和准备。{cites}")
        step_no += 1
    lines.append("\n## 5. 法律三段论涵摄")
    lines.append("大前提：仅采用已检索到且经层级、地域、时间和例外审查后的有效规范。")
    lines.append("小前提：以场景中的地点、主体、航空器、业务活动、数据活动和时间为事实要素。")
    lines.append("涵摄结论：逐项判断事实是否落入授权、义务、禁止和责任规范的构成要件；证据不足时保留人工核验或拒答。")
    lines.append("\n## 6. 关键证据")
    display_hits = [h for h in hits if _location_compatible(h, trace)] or hits
    for h in display_hits[:8]:
        c = h.chunk
        norm = "、".join(c.norm_types)
        lines.append(f"- [{c.article_id}] {c.title_zh}（{c.legal_level}，{c.jurisdiction}，{c.validity}，{norm}）：{c.text[:120]}")
    lines.append("\n## 7. 规则冲突与边界")
    if resolve.warnings:
        for w in resolve.warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- 未发现明显的层级、地方或施行时间冲突；仍需结合实际点位和主管部门平台核验。")
    lines.append("\n## 8. 需要人工核验的事项")
    if resolve.must_abstain:
        lines.append(f"- {resolve.abstain_reason}")
    lines.append("- 实际飞行前应核验实时空域、临时管制、属地平台入口、审批结果、具体起降点周边敏感区域。")
    lines.append("\n## 9. 免责声明")
    lines.append("以上为基于给定静态语料的合规研究与工作流建议，不替代正式法律意见或主管部门审批结果。")
    return "\n".join(lines)


def llm_answer(question: str, trace: TraceResult, hits: List[RetrievalHit], cells: List[EvidenceCell], resolve: ResolveResult, model: str, prompt_path: str = "prompts/generator_normcase_tarrag.txt", task: Optional[Dict[str, Any]] = None) -> str:
    system_prompt = Path(prompt_path).read_text(encoding="utf-8") if Path(prompt_path).exists() else "你是低空经济合规助手。"
    task = task or {}
    case_instruction = ""
    if task.get("task_type") == "case_outcome_prediction":
        case_instruction = """
这是案例责任预测任务。请不要停留在一般合规提醒，要在证据约束下给出可与真实案例对比的责任预测：
- 明确案件类型：刑事/行政处罚/民事侵权/产品责任/保险理赔。
- 明确责任主体：操作者、运营人、定作人、承揽人、所有人、生产者、保险公司或受害人自担。
- 明确法律效果：刑罚、罚款、赔偿、驳回诉请、保险限额内先赔、免赔部分承担等。
- 对民事案件必须分析因果关系、过错、责任比例或免责边界；对刑事案件必须分析普通违法与犯罪升级边界。
- 如果无法从证据得出具体金额，不要编造金额；但要给出责任方向和裁判逻辑。
""".strip()
    user = f"""
问题：{question}
任务类型：{task.get('task_type', 'general')}
案例场景槽位：{task.get('scenario_slots', {})}
{case_instruction}

场景槽位：{trace.slots}
触发 facets：{trace.facets}
Resolve 规则：{resolve.rules_applied}
Resolve 警告：{resolve.warnings}

Evidence matrix:
{matrix_to_markdown(cells)}

证据：
{format_evidence(hits)}
""".strip()
    client = SiliconFlowClient()
    return client.chat(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user}], temperature=0.1, max_tokens=2500)
