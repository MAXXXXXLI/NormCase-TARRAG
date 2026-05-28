import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict

from .io_utils import read_jsonl, write_jsonl
from .siliconflow import SiliconFlowClient


def safe_json_parse(text: str) -> Dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end+1]
    try:
        return json.loads(text)
    except Exception:
        return {"parse_error": True, "raw": text}


def judge_one(row: Dict, prompt: str, judge_model: str) -> Dict:
    evidence = []
    for h in row.get("hits", [])[:12]:
        evidence.append(f"[{h.get('article_id')}] {h.get('title_zh')}｜{h.get('legal_level')}｜{h.get('jurisdiction')}\n{h.get('text')}")
    user = f"""
问题：{row.get('question')}
任务类型：{row.get('task_type')}
Trace：{row.get('trace')}
Resolve：{row.get('resolve')}

检索证据：
{chr(10).join(evidence)}

模型答案：
{row.get('answer')}
""".strip()
    client = SiliconFlowClient()
    resp = client.chat(judge_model, [{"role":"system", "content":prompt}, {"role":"user", "content":user}], temperature=0.0, max_tokens=800)
    score = safe_json_parse(resp)
    return {"task_id": row.get("task_id"), "mode": row.get("mode"), "judge": score}


def judge_all(rows, prompt: str, judge_model: str, workers: int):
    workers = max(1, int(workers))
    if workers == 1:
        out_rows = []
        for i, row in enumerate(rows, start=1):
            out = judge_one(row, prompt, judge_model)
            out_rows.append(out)
            print(f"Judged {i}/{len(rows)}: {out.get('task_id')}", flush=True)
        return out_rows

    out_rows = [None] * len(rows)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(judge_one, row, prompt, judge_model): i for i, row in enumerate(rows)}
        for done, future in enumerate(as_completed(futures), start=1):
            idx = futures[future]
            out = future.result()
            out_rows[idx] = out
            print(f"Judged {done}/{len(rows)}: {out.get('task_id')}", flush=True)
    return [r for r in out_rows if r is not None]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pred", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--judge-model", default="Qwen/Qwen3-32B")
    p.add_argument("--prompt", default="prompts/judge_legal_workflow.txt")
    p.add_argument("--workers", type=int, default=1, help="Number of parallel judge calls.")
    args = p.parse_args()

    rows = read_jsonl(args.pred)
    prompt = Path(args.prompt).read_text(encoding="utf-8")
    out_rows = judge_all(rows, prompt, args.judge_model, args.workers)
    write_jsonl(args.out, out_rows)
    print(f"Saved judge scores to {args.out}")


if __name__ == "__main__":
    main()
