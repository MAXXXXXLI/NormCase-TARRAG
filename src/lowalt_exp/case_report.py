import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .io_utils import read_jsonl


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _index_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
    return {str(r.get(key)): r for r in rows if r.get(key) is not None}


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def _cell(text: Any, limit: int = 120) -> str:
    s = "" if text is None else str(text)
    s = s.replace("\n", " ").replace("|", "/")
    return s[:limit] + ("..." if len(s) > limit else "")


def _judge(row: Dict[str, Any]) -> Dict[str, Any]:
    judge = row.get("judge", {})
    return judge if isinstance(judge, dict) else {}


def build_report(args: argparse.Namespace) -> str:
    eval_report = read_json(args.eval_report)
    judge_summary = read_json(args.judge_summary)
    predictions = read_jsonl(args.pred)
    judged = read_jsonl(args.judge_scores)
    tasks = read_jsonl(args.eval)
    cases = read_jsonl(args.cases)

    pred_by_id = _index_by(predictions, "task_id")
    judge_by_id = _index_by(judged, "task_id")
    task_by_id = _index_by(tasks, "task_id")
    case_by_id = _index_by(cases, "case_id")
    overall = eval_report.get("overall", {})
    judge_means = judge_summary.get("score_means", {})
    errors = judge_summary.get("major_error_counts", {})

    lines = []
    lines.append("# 低空经济案例 RAG 验证实验设计与结果\n")
    lines.append(f"- 生成模型：`{args.generator_model}`")
    lines.append(f"- Judge 模型：`{args.judge_model}`")
    lines.append(f"- RAG 模式：`{args.mode}`")
    lines.append(f"- 语料：`{args.corpus}`")
    lines.append(f"- 案例评测集：`{args.eval}`")
    lines.append(f"- 生成时间：`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append("")

    lines.append("## 1. 实验目标\n")
    lines.append("本实验验证 NormCase-TARRAG 方法在真实/公开案例场景中的可用性：给定案情改写后的法律问题，系统先从低空经济规范语料中检索证据，再按场景—规范槽位追踪、规范—责任证据路由、法源证据矩阵和规则边界消解流程生成责任判断，最后与真实案例处理结果进行对比。实验关注的不是模型能否背诵案例，而是能否基于法规证据推导出与真实裁判/处罚/理赔方向一致的结论。")
    lines.append("")

    lines.append("## 2. 数据集\n")
    lines.append(f"- 案例种子集：`{args.cases}`，共 {len(cases)} 条。")
    lines.append(f"- 案例评测任务：`{args.eval}`，共 {len(tasks)} 条。")
    lines.append("- 覆盖类型：刑事黑飞、飞控破解、国家秘密、行政处罚、农药喷洒侵权、无人机相撞、产品责任、保险理赔。")
    lines.append("- 每条任务包含 `gold_case_outcome`、`expected_case_points`、`gold_source_ids`，用于结果对比和证据召回。")
    lines.append("")

    lines.append("## 3. 方法流程\n")
    lines.append("1. Trace：识别地点、主体、飞行活动、航空器类型、数据活动和风险 facet。")
    lines.append("2. Retrieve：在 full corpus 中检索全国规则、地方规则、运行安全、数据安全、技术标准和责任规则。")
    lines.append("3. Align：按规范类型、地域、法源层级、时效和场景角色对齐证据。")
    lines.append("4. Resolve：处理刑民行边界、地方/全国规则、现行/未来规则、标准/法律规则和责任例外。")
    lines.append("5. Generate：API 模型在证据约束下输出法律责任预测。")
    lines.append("6. Judge：案例专用 LLM-as-judge 对 RAG 答案与真实案例结果逐条评分。")
    lines.append("")

    lines.append("## 4. 复现命令\n")
    lines.append("```bash")
    lines.append("export SILICONFLOW_API_KEY=\"你的 key\"")
    lines.append("export MODEL=\"Qwen/Qwen3-32B\"")
    lines.append("export JUDGE_MODEL=\"Qwen/Qwen3-32B\"")
    lines.append(f"export WORKERS={args.workers}")
    if args.tag:
        lines.append(f"export TAG=\"{args.tag}\"")
    lines.append("bash scripts/run_case_api_experiment.sh")
    lines.append("```")
    lines.append("")

    lines.append("## 5. 输出文件\n")
    lines.append(f"- 自动指标报告：`{args.eval_report}`")
    lines.append(f"- RAG 逐条预测：`{args.pred}`")
    lines.append(f"- 案例 judge 逐条评分：`{args.judge_scores}`")
    lines.append(f"- 案例 judge 汇总：`{args.judge_summary}`")
    lines.append("")

    lines.append("## 6. 检索与自动指标\n")
    lines.append("| 指标 | 数值 |")
    lines.append("| --- | ---: |")
    for key in [
        "recall_at_5",
        "recall_at_10",
        "mrr_at_10",
        "ndcg_at_10",
        "facet_coverage",
        "norm_type_coverage",
        "citation_precision",
        "abstention_accuracy",
        "future_rule_misuse",
    ]:
        if key in overall:
            lines.append(f"| `{key}` | {_fmt(overall.get(key))} |")
    lines.append("")

    lines.append("## 7. 案例结果对比指标\n")
    lines.append("| 指标 | 数值 | 含义 |")
    lines.append("| --- | ---: | --- |")
    metric_names = {
        "outcome_match": "责任/处理结果方向是否匹配真实案例",
        "liability_allocation_accuracy": "责任主体、比例、连带或保险分配是否正确",
        "case_type_accuracy": "是否识别刑事、行政、民事、产品、保险等案件类型",
        "remedy_accuracy": "是否识别刑罚、罚款、赔偿、驳回、保险赔付等法律效果",
        "fact_issue_coverage": "关键事实争点覆盖度",
        "legal_issue_coverage": "关键法律争点覆盖度",
        "rule_application_quality": "法规适用到事实的质量，1-5",
        "subsumption_quality": "三段论涵摄质量，1-5",
        "exception_boundary_awareness": "责任例外和边界意识，1-5",
        "source_support_quality": "结论受检索证据支撑程度，1-5",
        "overall": "综合评分，1-5",
    }
    for key, desc in metric_names.items():
        if key in judge_means:
            lines.append(f"| `{key}` | {_fmt(judge_means.get(key))} | {desc} |")
    lines.append("")

    lines.append("## 8. 错误类型统计\n")
    if errors:
        lines.append("| 错误标签 | 次数 |")
        lines.append("| --- | ---: |")
        for key, count in errors.items():
            lines.append(f"| `{key}` | {count} |")
    else:
        lines.append("本次 judge 未返回主要错误标签。")
    lines.append("")

    lines.append("## 9. 逐案结果\n")
    lines.append("| 任务 | 案例 | 类型 | outcome | overall | 主要错误 | 真实结果摘要 |")
    lines.append("| --- | --- | --- | ---: | ---: | --- | --- |")
    for task in tasks:
        tid = task.get("task_id")
        pred = pred_by_id.get(str(tid), {})
        judged_row = judge_by_id.get(str(tid), {})
        judge = _judge(judged_row)
        case = case_by_id.get(str(task.get("case_id")), {})
        errors_text = ", ".join(judge.get("major_errors") or [])
        lines.append(
            f"| `{tid}` | {_cell(case.get('case_name'), 60)} | {_cell(case.get('case_type'), 24)} | "
            f"{_fmt(judge.get('outcome_match'), 2)} | {_fmt(judge.get('overall'), 2)} | "
            f"{_cell(errors_text, 80)} | {_cell(task.get('gold_case_outcome') or case.get('gold_result_summary'), 100)} |"
        )
        if not pred:
            lines.append(f"| `{tid}` | 未找到预测输出 |  |  |  |  |  |")
    lines.append("")

    lines.append("## 10. 结论\n")
    if judge_means:
        lines.append(
            "本次实验已经形成可量化的案例对比闭环：RAG 输出不仅接受常规检索指标检查，还与真实案例结果进行责任方向、案件类型、责任分配、救济方式和法律推理质量对比。后续论文实验可在当前 15 条 pilot 的基础上扩展到 80-150 条案例，并加入人工复核以校准 LLM-as-judge 偏差。"
        )
    else:
        lines.append("当前报告结构已就绪，但尚未写入 judge 分数；需要先完成 API 生成和案例 judge。")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--eval-report", required=True)
    p.add_argument("--pred", required=True)
    p.add_argument("--judge-scores", required=True)
    p.add_argument("--judge-summary", required=True)
    p.add_argument("--eval", default="data/eval/cases/lowalt_case_eval_tasks.jsonl")
    p.add_argument("--cases", default="data/cases/lowalt_case_seed.jsonl")
    p.add_argument("--corpus", default="data/processed/corpus.jsonl")
    p.add_argument("--out", required=True)
    p.add_argument("--generator-model", default="Qwen/Qwen3-32B")
    p.add_argument("--judge-model", default="Qwen/Qwen3-32B")
    p.add_argument("--mode", default="tarrag")
    p.add_argument("--workers", default="4")
    p.add_argument("--tag", default="")
    args = p.parse_args()

    report = build_report(args)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"Saved case experiment report to {args.out}")


if __name__ == "__main__":
    main()
