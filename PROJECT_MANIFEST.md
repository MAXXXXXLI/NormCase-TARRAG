# NormCase-TARRAG 项目清单

## 主线目录

| 路径 | 内容 |
| --- | --- |
| `README.md` | 最终项目入口说明 |
| `REPRODUCE_NORMCASE_TARRAG.md` | 从环境安装到复现实验的完整步骤 |
| `pyproject.toml` / `requirements.txt` | 项目元信息与 Python 依赖 |
| `src/lowalt_exp/` | NormCase-TARRAG 可执行代码，包名保留兼容旧脚本 |
| `scripts/` | 数据检查、demo、benchmark、case experiment 和 judge 脚本 |
| `prompts/` | 生成器和 judge 提示词 |
| `configs/` | 实验配置和 88 项来源词表 |

## 数据目录

| 路径 | 内容 |
| --- | --- |
| `data/processed/corpus.jsonl` | 低空经济完整规范语料，5173 chunk，88 来源 |
| `data/processed/corpus_case_enhanced.jsonl` | 加入案例责任规则后的案例增强语料 |
| `data/supplemental/case_responsibility_rules.jsonl` | 案例责任规则补充语料 |
| `data/eval/xl/lowaltbench_xl_1200.jsonl` | LowAltBench XL 全量任务集 |
| `data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl` | 15 条案例责任预测评测任务 |
| `data/cases/lowalt_case_seed.jsonl` | 15 条案例种子数据、案情和真实结果 |

## 最终论文与结果

| 路径 | 内容 |
| --- | --- |
| `paper/final/NormCase_TARRAG_Final_Paper.docx` | 最终 Word 论文 |
| `paper/final/NormCase_TARRAG_Final_Paper.md` | 从 Word 提取的 Markdown 版本 |
| `outputs/final/normcase_tarrag_case.json` | 最终案例自动指标 |
| `outputs/final/normcase_tarrag_case_judge_summary.json` | 最终案例 judge 汇总 |
| `outputs/final/normcase_tarrag_case_predictions.jsonl` | 最终案例逐条预测 |
| `outputs/final/normcase_tarrag_case_judge_scores.jsonl` | 最终案例逐条 judge 评分 |

## 最终方法名

全文统一使用 **NormCase-TARRAG**。模块命名如下：

1. `LowAlt-LawBase`：低空经济规范语料库。
2. `Scenario-Norm Trace`：场景-规范槽位追踪。
3. `NormCase Evidence Router`：规范-责任证据路由。
4. `Legal Source Matrix`：法源证据矩阵。
5. `Boundary Resolver`：规则边界消解器。
6. `Citation-Guided Generator`：引用约束生成器。
