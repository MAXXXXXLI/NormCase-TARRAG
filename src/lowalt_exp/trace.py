import re
from typing import Any, Dict, List

from .schema import TraceResult


CITY_ALIASES = [
    "北京",
    "上海",
    "深圳",
    "广州",
    "珠海",
    "苏州",
    "无锡",
    "南京",
    "武汉",
    "重庆",
    "四川",
    "山东",
    "湖南",
    "厦门",
    "黄石",
    "芜湖",
    "济南",
    "自贡",
    "达州",
    "共青城",
    "绍兴",
    "唐山",
    "河北",
    "余姚",
    "凤阳",
    "青田",
    "仙桃",
    "瓜州",
    "四平",
]

FACET_KEYWORDS = {
    "registration": ["登记", "实名", "激活", "国籍", "运行识别", "remote id"],
    "airspace": ["空域", "起飞", "飞行计划", "飞行申请", "禁飞", "临时管制", "审批", "航线", "机场", "医院"],
    "operation": ["运营", "运行", "操控员", "培训", "安全", "应急", "运行控制", "配送", "巡检", "文旅"],
    "airworthiness": ["适航", "生产", "制造", "型号", "审定", "合格证", "中型", "多旋翼", "动力提升"],
    "data_security": ["数据", "视频", "轨迹", "个人信息", "测绘", "地理信息", "隐私", "保密", "遥感", "存证"],
    "local": CITY_ALIASES,
    "standard": ["标准", "接口", "技术规范", "服务系统", "航行服务", "物流航线", "测试", "数据接口"],
    "policy": ["补贴", "产业", "低空经济", "试点", "扶持", "政策", "发展"],
    "future_rule": ["2025", "2026", "修订", "施行", "未来", "前瞻"],
    "norm_authorization": ["可以", "有权", "权利", "申请", "请求", "投诉", "举报", "复评", "异议"],
    "norm_obligation": ["应当", "必须", "需要", "义务", "履行", "合规准备", "清单", "要求"],
    "norm_prohibition": ["不得", "禁止", "不能", "不可以", "禁飞", "限制"],
    "norm_responsibility": ["责任", "处罚", "罚款", "警告", "责令", "追究", "后果", "风险"],
    "norm_exception": ["但是", "除外", "另有规定", "不适用", "从其规定", "例外"],
    "hierarchy_conflict": ["上位法", "下位法", "特别规定", "一般规定", "新规定", "旧规定", "国家", "地方", "标准", "政策", "冲突", "优先"],
    "legal_reasoning": ["适用", "构成要件", "法律后果", "涵摄", "三段论", "大前提", "小前提", "结论", "依据"],
    "case_public_safety": ["黑飞", "军方", "民航改航", "机场", "航道", "公共安全", "严重后果", "空防"],
    "case_cyber": ["破解", "后台", "限高", "电子围栏", "飞控", "计算机信息系统", "程序", "工具"],
    "case_secret": ["军事", "导弹", "战斗机", "国家秘密", "涉密", "军事设施", "军事管理区"],
    "case_admin": ["行政处罚", "罚款", "责令改正", "轨道交通", "高架线路", "100米", "禁飞区域", "报备"],
    "case_civil_tort": ["侵权", "赔偿", "损害", "受损", "减产", "碰撞", "剐蹭", "坠落", "误伤", "过错", "因果关系"],
    "case_agri_spray": ["农药", "除草剂", "喷洒", "植保", "飞防", "水稻", "蔬菜", "瓜苗", "作物"],
    "case_allocation": ["责任比例", "比例", "分配", "连带", "平均承担", "分别", "无法区分", "各自致害", "定作人", "承揽", "操作者", "所有人", "自担"],
    "case_product": ["产品", "缺陷", "大疆", "产品说明", "说明书", "警示", "APP", "视觉系统", "暗光", "生产者"],
    "case_insurance": ["保险", "第三者责任险", "免赔", "先行赔付", "保险公司", "责任险"],
}

SCENARIO_HINTS = {
    "黑飞/公共安全": ["黑飞", "军方", "民航改航", "机场", "航道", "公共安全"],
    "飞控破解/网络安全": ["破解", "限高", "禁飞区", "飞控", "电子围栏", "计算机信息系统"],
    "军事设施/保密": ["军事", "导弹", "战斗机", "国家秘密", "涉密"],
    "行政处罚": ["行政处罚", "罚款", "责令改正", "轨道交通", "报备"],
    "无人机民事侵权": ["侵权", "赔偿", "碰撞", "剐蹭", "坠落", "受损", "减产"],
    "农用无人机喷洒": ["农药", "除草剂", "植保", "飞防", "水稻", "蔬菜", "瓜苗"],
    "产品责任": ["产品", "缺陷", "大疆", "产品说明", "说明书", "警示", "APP", "视觉系统"],
    "保险理赔": ["保险", "第三者责任险", "免赔", "先行赔付"],
    "城市配送": ["配送", "物流", "快递", "外卖", "货运"],
    "城市巡检": ["巡检", "电力", "桥梁", "道路", "管线", "城市治理"],
    "文旅载人/观光": ["文旅", "观光", "载人", "eVTOL", "空中游览"],
    "应急救援": ["应急", "救援", "消防", "灾害", "医疗"],
    "农业植保": ["农业", "植保", "农用"],
    "制造适航": ["制造", "生产", "适航", "型号", "审定"],
}


def detect_location(q: str) -> str:
    for city in CITY_ALIASES:
        if city in q:
            return city
    return "全国"


def detect_scenario(q: str) -> str:
    for name, kws in SCENARIO_HINTS.items():
        if any(k in q for k in kws):
            return name
    return "一般低空飞行/合规咨询"


def detect_facets(q: str) -> List[str]:
    facets = []
    for facet, kws in FACET_KEYWORDS.items():
        if any(k.lower() in q.lower() for k in kws):
            facets.append(facet)
    # Low-altitude economy questions usually need these default facets.
    for default in ["operation", "airspace", "registration"]:
        if default not in facets:
            facets.append(default)
    if detect_location(q) != "全国" and "local" not in facets:
        facets.append("local")
    # Scenario-specific expansions.
    if any(k in q for k in ["视频", "轨迹", "数据", "测绘", "巡检"]):
        if "data_security" not in facets:
            facets.append("data_security")
    if any(k in q for k in ["配送", "物流", "航线", "服务系统"]):
        if "standard" not in facets:
            facets.append("standard")

    # Full legal review should not collapse statutes into an obligation list.
    # For broad compliance questions, retrieve by norm structure as well:
    # authorization, obligation, prohibition, responsibility, exceptions,
    # hierarchy/conflict and final subsumption reasoning.
    broad_review = any(k in q for k in ["合规", "准备", "哪些", "如何", "怎么", "是否", "能不能", "可不可以", "风险", "责任", "权利", "清单"])
    if broad_review:
        for norm_facet in [
            "norm_authorization",
            "norm_obligation",
            "norm_prohibition",
            "norm_responsibility",
            "norm_exception",
            "legal_reasoning",
        ]:
            if norm_facet not in facets:
                facets.append(norm_facet)
    if any(k in q for k in ["冲突", "层级", "优先", "上位", "下位", "国家", "地方", "标准", "政策", "当前", "未来"]):
        if "hierarchy_conflict" not in facets:
            facets.append("hierarchy_conflict")
    if any(k in q for k in ["责任", "处罚", "赔偿", "判", "法院", "案", "罪", "构成", "法律上应如何评价"]):
        for case_facet in ["case_civil_tort", "case_allocation"]:
            if case_facet not in facets and any(k in q for k in FACET_KEYWORDS[case_facet]):
                facets.append(case_facet)
    if "case_cyber" in facets and not any(k in q for k in ["为他人", "提供", "程序", "工具", "服务", "牟利", "后台", "电子围栏"]):
        # Self-use cracking in an airport/black-flight case is usually better
        # routed as public-safety flight risk. The cyber-crime facet is reserved
        # for providing cracking tools/services or clearly attacking a computer
        # information system.
        facets.remove("case_cyber")
    return facets


def build_subqueries(q: str, slots: Dict[str, Any], facets: List[str]) -> Dict[str, List[str]]:
    loc = slots.get("location", "全国")
    scenario = slots.get("scenario", "")
    sub: Dict[str, List[str]] = {}
    templates = {
        "registration": [f"{q} 实名登记 激活 运行识别", f"民用无人驾驶航空器 实名登记 运行识别 {scenario}"],
        "airspace": [f"{q} 空域 飞行申请 飞行计划 管制", f"{loc} 无人机 空域 飞行安全 临时管制"],
        "operation": [f"{q} 运行安全 运营人 操控员 应急", f"民用无人驾驶航空器 运行安全 管理规则 {scenario}"],
        "airworthiness": [f"{q} 适航 审定 合格证 生产 制造", "无人驾驶航空器 适航 审定 分级分类"],
        "data_security": [f"{q} 数据安全 个人信息 测绘 保密", f"无人机 {scenario} 视频 轨迹 数据 合规"],
        "local": [f"{loc} 无人驾驶航空器 管理 低空经济 条例", f"{loc} 低空经济 无人机 飞行安全"],
        "standard": [f"{q} 技术标准 低空飞行服务 数据接口 航线", f"无人机 {scenario} 行业标准 技术规范"],
        "policy": [f"{q} 低空经济 政策 试点 扶持", "低空经济 标准体系 产业政策"],
        "future_rule": [f"{q} 施行日期 未来 修订 当前有效", "民用航空法 2025 2026 施行 当前有效"],
        "norm_authorization": [f"{q} 可以 有权 申请 请求 投诉 举报 复评 权利", f"低空经济 无人机 权利 救济 申请 投诉 举报 {scenario}"],
        "norm_obligation": [f"{q} 应当 必须 义务 履行 建立 采取 提交 申报", f"民用无人驾驶航空器 应当 义务 合规要求 {scenario}"],
        "norm_prohibition": [f"{q} 不得 禁止 限制 不适用 禁飞", f"无人驾驶航空器 不得 禁止 限制 活动 {scenario}"],
        "norm_responsibility": [f"{q} 责任 处罚 罚款 警告 责令 追究 法律后果", f"无人驾驶航空器 法律责任 主体责任 处罚 风险 {scenario}"],
        "norm_exception": [f"{q} 但是 除外 另有规定 不适用 从其规定 例外", f"低空经济 无人机 一般规则 例外规则 另有规定 {scenario}"],
        "hierarchy_conflict": [f"{q} 法律 行政法规 部门规章 地方性法规 标准 政策 上位法 特别规定 新旧规定", f"{loc} 国家规则 地方规则 强制标准 行业标准 政策文件 冲突处理"],
        "legal_reasoning": [f"{q} 适用 条件 构成要件 法律后果 涵摄 结论", f"低空经济 法律三段论 事实 条件 法律效果 {scenario}"],
        "case_public_safety": [f"{q} 以危险方法危害公共安全 刑法 第一百一十四条 第一百一十五条", "无人驾驶航空器 黑飞 未申请空域 飞行计划 公共安全 刑事责任", "无人驾驶航空器飞行管理暂行条例 第三十四条 第五十六条 公共安全"],
        "case_cyber": [f"{q} 提供侵入 非法控制 计算机信息系统 程序 工具 第二百八十五条", "破解无人机 禁飞 限高 电子围栏 飞控系统 网络安全 刑事责任", "计算机信息系统安全 司法解释 程序 工具 情节严重"],
        "case_secret": [f"{q} 非法获取国家秘密 刑法 第二百八十二条 军事设施", "无人机 违法拍摄 军事设施 涉密场所 国家秘密 保密义务", "军事设施保护法 保守国家秘密法 无人机 航拍 传播"],
        "case_admin": [f"{q} 行政处罚 责令改正 罚款 无人机", "城市轨道交通运营管理规定 第三十四条 第五十三条 100米 无人机", f"{loc} 民用无人机 禁飞 报备 超高 罚款"],
        "case_civil_tort": [f"{q} 民法典 过错 侵权责任 因果关系 赔偿", "无人机 运行安全 注意义务 财产损害 民事赔偿", "受害人过错 因果关系 事故调查报告 赔偿责任"],
        "case_agri_spray": [f"{q} 农药 喷洒 作业 勘察 安全处理 有毒药品 因果关系", "农林喷洒 作业负责人 农药 作物 受损 赔偿", "植保无人机 飞防 农药漂移 相邻农田 损害"],
        "case_allocation": [f"{q} 民法典 承揽 定作人 选任 指示 过错 责任", "分别实施侵权 平均承担 连带责任 过错比例 受害人过错", "责任主体 操作者 所有人 定作人 承揽人 保险公司"],
        "case_product": [f"{q} 民法典 产品责任 产品缺陷 生产者 说明 警示", "无人机 产品质量 说明书 APP 提示 暗光 视觉系统 缺陷", "产品缺陷 生产者责任 用户操作 免责 证据"],
        "case_insurance": [f"{q} 保险法 责任保险 第三者 直接赔偿 免赔 保险限额", "低空保险 第三者责任险 无人机 保险公司 先行赔付", "责任保险 被保险人 第三者损害 保险金"],
    }
    for f in facets:
        sub[f] = templates.get(f, [q])
    return sub


def trace_question(q: str, disabled_facets: List[str] = None) -> TraceResult:
    disabled_facets = disabled_facets or []
    loc = detect_location(q)
    scenario = detect_scenario(q)
    data_activity = []
    for kw in ["视频", "轨迹", "测绘", "个人信息", "遥感", "平台调度数据"]:
        if kw in q:
            data_activity.append(kw)
    actor = "运营企业" if any(k in q for k in ["企业", "运营", "试点", "配送", "巡检"]) else "个人或单位"
    aircraft = "民用无人驾驶航空器" if any(k in q for k in ["无人机", "无人驾驶航空器", "UAV"]) else "低空航空器"
    facets = [f for f in detect_facets(q) if f not in disabled_facets]
    slots = {"location": loc, "actor": actor, "aircraft": aircraft, "scenario": scenario, "data_activity": data_activity}
    warnings = []
    if any(k in q for k in ["明天", "今天", "上午", "下午", "医院", "机场", "能不能起飞", "可以起飞"]):
        warnings.append("question_requires_realtime_airspace_or_site_specific_check")
    return TraceResult(q, slots, facets, build_subqueries(q, slots, facets), warnings)
