import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    "obligation": [r"应当", r"应依法", r"应遵守", r"应考虑", r"应区分", r"应取得", r"应履行", r"应建立", r"应采取", r"应提交", r"应申报", r"应核验", r"应开展", r"必须", r"需要", r"须", r"按照.*规定", r"依法.*履行", r"建立", r"采取"],
    "prohibition": [r"不得", r"禁止", r"严禁", r"不得.*从事", r"不得.*利用", r"不得.*提供"],
    "responsibility": [r"承担.*责任", r"主体责任", r"法律责任", r"民事责任", r"刑事责任", r"处罚", r"罚款", r"警告", r"责令", r"追究", r"处分"],
    "exception": [r"但是", r"但书", r"除.*外", r"另有规定", r"不适用", r"可以不", r"从其规定", r"依照其规定"],
}


def infer_norm_types(text: str) -> List[str]:
    found = []
    for norm_type, patterns in NORM_PATTERNS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            found.append(norm_type)
    return found or ["general_rule"]


def infer_exception_markers(text: str) -> List[str]:
    markers = []
    for marker in ["但是", "法律另有规定", "行政法规另有规定", "另有规定", "除", "不适用", "从其规定", "依照其规定", "可以不"]:
        if marker in text:
            markers.append(marker)
    return list(dict.fromkeys(markers))


@dataclass
class Chunk:
    article_id: str
    source_id: str
    title_zh: str
    jurisdiction: str
    issuing_authority: str
    source_type: str
    legal_level: str
    effective_date: str
    validity: str
    themes: List[str]
    article_no: str
    text: str
    norm_types: List[str] = field(default_factory=list)
    exception_markers: List[str] = field(default_factory=list)
    authority_rank: int = 0
    char_len: int = 0
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Chunk":
        return cls(
            article_id=d.get("article_id", ""),
            source_id=d.get("source_id", ""),
            title_zh=d.get("title_zh", ""),
            jurisdiction=d.get("jurisdiction", ""),
            issuing_authority=d.get("issuing_authority", ""),
            source_type=d.get("source_type", ""),
            legal_level=d.get("legal_level", ""),
            effective_date=str(d.get("effective_date", "")),
            validity=d.get("validity", ""),
            themes=d.get("themes", []) or [],
            article_no=d.get("article_no", ""),
            text=d.get("text", ""),
            norm_types=d.get("norm_types", []) or infer_norm_types(d.get("text", "")),
            exception_markers=d.get("exception_markers", []) or infer_exception_markers(d.get("text", "")),
            authority_rank=int(d.get("authority_rank", LEGAL_LEVEL_PRIORITY.get(d.get("legal_level", ""), 0))),
            char_len=int(d.get("char_len", len(d.get("text", "")))),
            raw=d,
        )

    def searchable_text(self) -> str:
        parts = [
            self.title_zh,
            self.issuing_authority,
            self.legal_level,
            self.source_type,
            self.jurisdiction,
            " ".join(self.themes),
            " ".join(self.norm_types),
            " ".join(self.exception_markers),
            self.article_no,
            self.text,
        ]
        return " ".join([p for p in parts if p])


@dataclass
class RetrievalHit:
    chunk: Chunk
    score: float
    rank: int
    query: str = ""
    facet: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "score": self.score,
            "query": self.query,
            "facet": self.facet,
            "article_id": self.chunk.article_id,
            "source_id": self.chunk.source_id,
            "title_zh": self.chunk.title_zh,
            "legal_level": self.chunk.legal_level,
            "source_type": self.chunk.source_type,
            "jurisdiction": self.chunk.jurisdiction,
            "effective_date": self.chunk.effective_date,
            "validity": self.chunk.validity,
            "themes": self.chunk.themes,
            "norm_types": self.chunk.norm_types,
            "exception_markers": self.chunk.exception_markers,
            "authority_rank": self.chunk.authority_rank,
            "article_no": self.chunk.article_no,
            "text": self.chunk.text,
        }


@dataclass
class TraceResult:
    original_question: str
    slots: Dict[str, Any]
    facets: List[str]
    subqueries: Dict[str, List[str]]
    warnings: List[str] = field(default_factory=list)


@dataclass
class EvidenceCell:
    facet: str
    legal_level: str
    jurisdiction: str
    source_type: str
    validity: str
    role: str
    hits: List[RetrievalHit]


@dataclass
class ResolveResult:
    rules_applied: List[str]
    warnings: List[str]
    must_abstain: bool = False
    abstain_reason: Optional[str] = None
