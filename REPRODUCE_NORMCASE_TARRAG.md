# NormCase-TARRAG 复现说明

本文档说明如何复现最终项目中的数据核验、离线问答和案例责任预测实验。

## 1. 环境准备

```bash
cd /Users/maxxxxx/Desktop/NormCase-TARRAG_Final_Project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD/src
```

## 2. 数据完整性检查

```bash
bash scripts/check_full_dataset.sh
```

检查对象：

- `data/processed/corpus.jsonl`
- `data/processed/corpus_case_enhanced.jsonl`
- `configs/source_id_vocab_full.json`
- `data/eval/xl/lowaltbench_xl_1200.jsonl`
- `data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl`

## 3. 离线单问题问答

```bash
bash scripts/run_normcase_demo.sh "深圳做无人机城市配送试点，需要从哪些方面做合规准备？"
```

该命令不调用外部 API，用于验证 Trace、Retrieve、Align、Resolve 和离线模板生成链路。

## 4. 案例责任预测实验

需要 API key。复制环境变量模板：

```bash
cp .env.example .env
vim .env
```

运行最终案例实验：

```bash
bash scripts/run_normcase_case_experiment.sh
```

默认配置：

```bash
CORPUS=data/processed/corpus_case_enhanced.jsonl
EVAL=data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl
CASES=data/cases/lowalt_case_seed.jsonl
MODEL=Qwen/Qwen3-32B
JUDGE_MODEL=Qwen/Qwen3-32B
OUT_DIR=outputs/final
TAG=normcase_tarrag_case
MD_OUT=paper/final/NormCase_TARRAG_Case_Experiment_Results.md
```

## 5. 已保存的最终结果

项目中已经保留一份最终实验结果，位于 `outputs/final/`：

| 文件 | 内容 |
| --- | --- |
| `normcase_tarrag_case.json` | 自动检索与引用指标 |
| `normcase_tarrag_case_predictions.jsonl` | 15 条案例逐条 RAG 预测 |
| `normcase_tarrag_case_judge_scores.jsonl` | 15 条案例逐条 judge 评分 |
| `normcase_tarrag_case_judge_summary.json` | 案例 judge 汇总 |

核心结果：

| 指标 | 最终值 |
| --- | ---: |
| R@10 | 0.9167 |
| nDCG@10 | 0.9498 |
| citation precision | 0.9849 |
| outcome match | 0.7000 |
| liability allocation accuracy | 0.7333 |
| remedy accuracy | 0.8000 |
| overall judge score | 3.6000 |

## 6. 写作边界

论文中建议将 LowAltBench XL 的 200 条验证结果表述为“当前可执行包上的方法验证”，不要外推为完整语料 SOTA。15 条案例责任预测任务适合作为初步验证和模块消融，不宜外推为所有低空经济案件的普遍结论。
