from collections import OrderedDict, defaultdict
from typing import Dict, Iterable, List, Optional

from .bm25 import BM25
from .schema import Chunk, RetrievalHit, TraceResult
from .siliconflow import SiliconFlowClient


class Retriever:
    def __init__(self, corpus: List[Chunk]):
        self.corpus = corpus
        self.bm25 = BM25([c.searchable_text() for c in corpus])
        self.by_source: Dict[str, List[Chunk]] = defaultdict(list)
        for c in corpus:
            self.by_source[c.source_id].append(c)

    def bm25_search(self, query: str, top_k: int = 12, facet: str = "general") -> List[RetrievalHit]:
        hits = []
        for rank, (idx, score) in enumerate(self.bm25.search(query, top_k=top_k), start=1):
            hits.append(RetrievalHit(self.corpus[idx], float(score), rank, query=query, facet=facet))
        return hits

    def retrieve_plain(self, query: str, top_k: int = 12) -> List[RetrievalHit]:
        return self.bm25_search(query, top_k=top_k, facet="general")

    def retrieve_trace(self, trace: TraceResult, prefetch_k: int = 20, final_k: int = 12) -> List[RetrievalHit]:
        merged: Dict[str, RetrievalHit] = OrderedDict()
        for facet, queries in trace.subqueries.items():
            for q in queries:
                for h in self.bm25_search(q, top_k=prefetch_k, facet=facet):
                    key = h.chunk.article_id
                    # Keep the highest score, but add a small facet bonus. When
                    # a query facet asks for a legal norm type, prefer chunks
                    # whose text actually contains that norm structure.
                    h.score += (
                        0.1
                        + self._norm_facet_bonus(facet, h.chunk)
                        + self._semantic_facet_bonus(facet, h.chunk, trace)
                        + self._validity_bonus(facet, h.chunk)
                    )
                    if key not in merged or h.score > merged[key].score:
                        merged[key] = h
        ranked_all = sorted(merged.values(), key=lambda h: h.score, reverse=True)
        ranked = self._apply_case_coverage(ranked_all, trace, final_k)
        for i, h in enumerate(ranked, start=1):
            h.rank = i
        return ranked

    def rerank(self, query: str, hits: List[RetrievalHit], model: str = "BAAI/bge-reranker-v2-m3", top_k: int = 12) -> List[RetrievalHit]:
        if not hits:
            return []
        client = SiliconFlowClient()
        docs = [self._doc_for_rerank(h.chunk) for h in hits]
        results = client.rerank(model=model, query=query, documents=docs, top_n=min(top_k, len(docs)))
        reranked: List[RetrievalHit] = []
        for rank, item in enumerate(results, start=1):
            idx = int(item.get("index", rank - 1))
            if idx < 0 or idx >= len(hits):
                continue
            h = hits[idx]
            h.score = float(item.get("relevance_score", h.score))
            h.rank = rank
            reranked.append(h)
        return reranked or hits[:top_k]

    @staticmethod
    def _doc_for_rerank(c: Chunk) -> str:
        return f"{c.title_zh}｜{c.legal_level}｜{c.jurisdiction}｜{c.article_no}\n{c.text}"

    @staticmethod
    def _norm_facet_bonus(facet: str, chunk: Chunk) -> float:
        norm_map = {
            "norm_authorization": "authorization",
            "norm_obligation": "obligation",
            "norm_prohibition": "prohibition",
            "norm_responsibility": "responsibility",
            "norm_exception": "exception",
        }
        expected = norm_map.get(facet)
        if expected and expected in chunk.norm_types:
            return 12.0
        if facet == "hierarchy_conflict":
            return 8.0 if chunk.authority_rank >= 70 or chunk.exception_markers else 0.0
        if facet == "legal_reasoning":
            return 5.0 if chunk.norm_types else 0.0
        return 0.0

    @staticmethod
    def _semantic_facet_bonus(facet: str, chunk: Chunk, trace: TraceResult) -> float:
        themes = set(chunk.themes)
        text = chunk.searchable_text()
        source_id = chunk.source_id
        if facet == "local":
            loc = str(trace.slots.get("location", ""))
            if loc and loc != "全国" and (chunk.jurisdiction == loc or loc in chunk.jurisdiction or loc in chunk.title_zh or loc in text):
                return 80.0
            if chunk.jurisdiction not in ["", "CN", "全国"]:
                return 12.0
        if facet == "standard":
            return 20.0 if "标准" in chunk.legal_level or "standard" in themes or "规范" in chunk.title_zh else 0.0
        if facet == "data_security":
            return 20.0 if themes & {"data_security", "personal_information", "surveying_mapping", "geographic_information"} else 0.0
        if facet == "operation":
            return 15.0 if themes & {"operation", "operator", "safety"} else 0.0
        if facet == "registration":
            return 15.0 if "registration" in themes or "登记" in text or "运行识别" in text else 0.0
        if facet == "airspace":
            return 15.0 if themes & {"airspace", "flight_application"} or "空域" in text else 0.0
        if facet == "case_public_safety":
            score = 0.0
            if source_id in {"criminal_law_case_supplement", "uas_interim_reg_2023", "general_flight_rules_current", "public_security_administration_law_2025"}:
                score += 65.0
            if any(k in text for k in ["公共安全", "严重后果", "飞行计划", "管制空域", "危及公共"]):
                score += 35.0
            return score
        if facet == "case_cyber":
            score = 0.0
            if source_id in {"criminal_law_case_supplement", "cybercrime_interpretation_2011", "cybersecurity_law_2025_current", "public_security_administration_law_2025"}:
                score += 65.0
            if any(k in text for k in ["计算机信息系统", "侵入", "非法控制", "程序", "工具", "网络安全"]):
                score += 35.0
            return score
        if facet == "case_secret":
            score = 0.0
            if source_id in {"criminal_law_case_supplement", "state_secrets_law_2024", "military_facilities_protection_law_2021", "uas_interim_reg_2023"}:
                score += 65.0
            if any(k in text for k in ["军事设施", "国家秘密", "涉密", "违法拍摄"]):
                score += 35.0
            return score
        if facet == "case_admin":
            score = 0.0
            if source_id in {"urban_rail_operation_reg_2018", "shenzhen_micro_light_uav_interim_2019", "uas_interim_reg_2023"}:
                score += 65.0
            if any(k in text for k in ["城市轨道交通", "100米", "无人机等低空飞行器", "责令改正", "罚款", "报备"]):
                score += 35.0
            return score
        if facet == "case_civil_tort":
            score = 0.0
            if source_id in {"civil_code_tort_case_supplement", "uas_interim_reg_2023", "ccar91_general_operation_flight_rules_2019", "ccar92_uas_operation_safety_2024"}:
                score += 55.0
            if any(k in text for k in ["侵权责任", "过错", "损害", "赔偿", "因果关系", "安全注意义务"]):
                score += 35.0
            if "product_liability" in themes and not any(k in trace.original_question for k in ["产品", "缺陷", "大疆", "说明", "APP", "视觉系统"]):
                score -= 45.0
            return score
        if facet == "case_agri_spray":
            score = 0.0
            if source_id in {"civil_code_tort_case_supplement", "ccar91_general_operation_flight_rules_2019", "ccar92_uas_operation_safety_2024"}:
                score += 55.0
            if any(k in text for k in ["农林喷洒", "农药", "有毒药品", "作业区", "作业负责人", "植保"]):
                score += 45.0
            return score
        if facet == "case_allocation":
            score = 0.0
            if source_id in {"civil_code_tort_case_supplement", "insurance_law_case_supplement"}:
                score += 65.0
            if any(k in text for k in ["承揽", "定作人", "分别实施", "过错", "责任保险", "第三者"]):
                score += 35.0
            return score
        if facet == "case_product":
            score = 0.0
            if source_id in {"civil_code_tort_case_supplement", "uas_interim_reg_2023"}:
                score += 60.0
            if any(k in text for k in ["产品责任", "产品缺陷", "生产者", "缺陷", "警示", "说明"]):
                score += 40.0
            return score
        if facet == "case_insurance":
            score = 0.0
            if source_id in {"insurance_law_case_supplement", "low_altitude_insurance_2026", "civil_aviation_law_2021_current", "civil_aviation_law_2025"}:
                score += 60.0
            if any(k in text for k in ["责任保险", "保险人", "被保险人", "第三者", "保险金", "免赔"]):
                score += 40.0
            return score
        return 0.0

    @staticmethod
    def _validity_bonus(facet: str, chunk: Chunk) -> float:
        validity = str(chunk.validity or "").lower()
        is_future = "future" in validity or "not_yet_effective" in validity or "尚未施行" in validity
        if not is_future:
            return 0.0
        return 15.0 if facet == "future_rule" else -45.0

    def _apply_case_coverage(self, ranked_all: List[RetrievalHit], trace: TraceResult, final_k: int) -> List[RetrievalHit]:
        if not any(f.startswith("case_") for f in trace.facets):
            return ranked_all[:final_k]

        promoted = self._case_source_router(trace)
        facet_fill = self._facet_fillers(ranked_all, trace)
        out: List[RetrievalHit] = []
        seen = set()

        def add(hit: RetrievalHit) -> None:
            if len(out) >= final_k:
                return
            validity = str(hit.chunk.validity or "").lower()
            is_future = "future" in validity or "not_yet_effective" in validity or "尚未施行" in validity
            if is_future and "future_rule" not in trace.facets:
                return
            aid = hit.chunk.article_id
            if aid in seen:
                return
            out.append(hit)
            seen.add(aid)

        for h in promoted[:9]:
            add(h)
        for h in facet_fill:
            add(h)
        for h in ranked_all:
            add(h)
        return out[:final_k]

    def _facet_fillers(self, ranked_all: List[RetrievalHit], trace: TraceResult) -> List[RetrievalHit]:
        preferred = ["airspace", "operation", "registration", "local", "policy"]
        out = []
        seen_facets = set()
        for facet in preferred:
            if facet not in trace.facets:
                continue
            for h in ranked_all:
                if h.facet == facet and h.facet not in seen_facets:
                    out.append(h)
                    seen_facets.add(h.facet)
                    break
        return out

    def _case_source_router(self, trace: TraceResult) -> List[RetrievalHit]:
        q = trace.original_question
        facets = set(trace.facets)
        specs = []

        def spec(source_id: str, facet: str, articles: List[str], max_items: int = 1) -> None:
            specs.append((source_id, facet, articles, max_items))

        if "case_public_safety" in facets:
            spec("criminal_law_case_supplement", "case_public_safety", ["第一百一十四条", "第一百一十五条"], 2)
            spec("uas_interim_reg_2023", "case_public_safety", ["第二十六条", "第三十四条", "第五十一条", "第十六条"], 2)
            spec("general_flight_rules_current", "airspace", ["第二条", "第三条", "第八条"], 1)
            spec("public_security_administration_law_2025", "case_public_safety", ["第三条", "第八条"], 1)
        if "case_cyber" in facets:
            spec("criminal_law_case_supplement", "case_cyber", ["第二百八十五条"], 1)
            spec("cybercrime_interpretation_2011", "case_cyber", ["第二条", "第三条"], 2)
            spec("cybersecurity_law_2025_current", "case_cyber", ["第六条", "第二十七条", "第六十三条"], 1)
            spec("uas_interim_reg_2023", "case_cyber", ["第三十四条"], 1)
        if "case_secret" in facets:
            spec("criminal_law_case_supplement", "case_secret", ["第二百八十二条"], 1)
            spec("military_facilities_protection_law_2021", "case_secret", ["第二十二条", "第六十条"], 2)
            spec("state_secrets_law_2024", "case_secret", ["第五条", "第五十九条"], 1)
            spec("uas_interim_reg_2023", "case_secret", ["第三十四条"], 1)
        if "case_admin" in facets:
            spec("urban_rail_operation_reg_2018", "case_admin", ["第三十四条", "第五十三条"], 2)
            spec("uas_interim_reg_2023", "case_admin", ["第二十六条", "第五十一条", "第五十二条"], 1)
            if "深圳" in q:
                spec("shenzhen_micro_light_uav_interim_2019", "local", ["第二十四条", "第四十条", "第三十四条"], 2)
        if "case_civil_tort" in facets or "case_agri_spray" in facets or "case_allocation" in facets:
            spec("civil_code_tort_case_supplement", "case_civil_tort", ["第一千一百六十五条", "第一千一百七十二条", "第一千一百七十三条", "第一千一百九十三条"], 3)
            spec("uas_interim_reg_2023", "airspace", ["第二十六条", "第三十四条", "第五十一条"], 1)
            spec("ccar92_uas_operation_safety_2024", "operation", ["第92.1条", "第92.1103条"], 1)
            if any(k in q for k in ["农药", "除草剂", "喷药", "喷洒", "飞防", "植保"]):
                spec("ccar91_general_operation_flight_rules_2019", "case_agri_spray", ["chunk_186", "chunk_187"], 2)
        if "case_product" in facets:
            spec("civil_code_tort_case_supplement", "case_product", ["第一千二百零二条", "第一千二百零三条", "第一千二百零六条"], 3)
            spec("uas_interim_reg_2023", "case_product", ["第九条"], 1)
            spec("uas_production_management_2024", "case_product", ["第四条"], 1)
            spec("caac_uas_airworthiness_class_safety_2022", "airworthiness", ["chunk_001"], 1)
        if "case_insurance" in facets:
            spec("insurance_law_case_supplement", "case_insurance", ["第六十五条", "第六十六条"], 2)
            spec("civil_code_tort_case_supplement", "case_civil_tort", ["第一千一百六十五条"], 1)

        hits: List[RetrievalHit] = []
        ranked_score = 0.0
        for source_id, facet, articles, max_items in specs:
            candidates = self._best_source_hits(source_id, facet, articles, trace, max_items=max_items)
            for h in candidates:
                ranked_score += 1.0
                h.score = 10000.0 - ranked_score
                hits.append(h)
        return hits

    def _best_source_hits(self, source_id: str, facet: str, articles: List[str], trace: TraceResult, max_items: int = 1) -> List[RetrievalHit]:
        chunks = self.by_source.get(source_id, [])
        if not chunks:
            return []

        scored = []
        q = trace.original_question
        for c in chunks:
            article_score = 0
            for i, marker in enumerate(articles):
                if marker and (marker in c.article_no or marker in c.article_id or marker in c.text):
                    article_score = max(article_score, 100 - i)
            if article_score == 0 and articles:
                continue
            text = c.searchable_text()
            kw_score = sum(1 for kw in self._case_keywords(trace) if kw and kw in text)
            score = article_score + kw_score + self._semantic_facet_bonus(facet, c, trace) + self._norm_facet_bonus("norm_responsibility", c)
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        seen = set()
        for score, c in scored:
            if c.article_id in seen:
                continue
            out.append(RetrievalHit(c, float(score), 0, query="case_source_router", facet=facet))
            seen.add(c.article_id)
            if len(out) >= max_items:
                break
        return out

    @staticmethod
    def _case_keywords(trace: TraceResult) -> List[str]:
        q = trace.original_question
        keys = []
        for kw in ["无人机", "无人驾驶航空器", "空域", "飞行计划", "公共安全", "军事设施", "国家秘密", "破解", "计算机信息系统", "轨道交通", "农药", "除草剂", "承揽", "定作人", "产品缺陷", "警示", "保险", "第三者责任险", "赔偿", "过错", "因果关系"]:
            if kw in q:
                keys.append(kw)
        return keys
