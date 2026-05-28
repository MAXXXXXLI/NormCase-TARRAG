# NormCase-TARRAG Final Project

这是低空经济合规问答与案例责任预测的最终项目包。项目已按论文《面向低空经济合规问答与案例责任预测的 NormCase-TARRAG 方法研究》的命名重新整理，主方法统一为 **NormCase-TARRAG**。

代码包名暂保留 `lowalt_exp`，用于保证既有脚本和评测流程可直接运行；论文、说明文档、复现入口和最终结果均使用 NormCase-TARRAG 命名。

## 最终方法

NormCase-TARRAG 是“规范结构化与案例感知的事实追踪-证据对齐-规则消解 RAG”框架。最终论文中使用以下模块名：

| 英文模块名 | 中文论文名 | 作用 |
| --- | --- | --- |
| `LowAlt-LawBase` | 低空经济规范语料库 | 组织法规、标准、政策、地方规则和案例责任规则 |
| `Scenario-Norm Trace` | 场景-规范槽位追踪 | 识别地点、主体、航空器、业务场景、数据活动和责任维度 |
| `NormCase Evidence Router` | 规范-责任证据路由 | 针对空域、数据、标准、民事侵权、刑事、保险等 facet 定向检索 |
| `Legal Source Matrix` | 法源证据矩阵 | 按法源层级、地域、效力、角色和规范类型组织证据 |
| `Boundary Resolver` | 规则边界消解器 | 处理上位法/下位法、当前/未来、法律/标准、一般/例外和多主体责任边界 |
| `Citation-Guided Generator` | 引用约束生成器 | 在证据矩阵约束下输出三段论式答案和 article_id 引用 |

## 关键结论

- 完整低空经济规范语料：`data/processed/corpus.jsonl`，5173 个 chunk，88 项来源。
- 案例增强语料：`data/processed/corpus_case_enhanced.jsonl`。
- 全量任务集：`data/eval/xl/lowaltbench_xl_1200.jsonl`，1200 条任务。
- 案例责任预测任务：`data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl`，15 条任务。
- 案例最终结果：R@10 = 0.9167，nDCG@10 = 0.9498，引用精度 = 0.9849，案例责任方向一致性 = 0.7000，综合评分 = 3.6000。

## 最终论文与方案

- 最终 Word 论文：`paper/final/NormCase_TARRAG_Final_Paper.docx`
- 最终论文 Markdown 文本：`paper/final/NormCase_TARRAG_Final_Paper.md`
- 最终项目清单：`PROJECT_MANIFEST.md`
- 复现说明：`REPRODUCE_NORMCASE_TARRAG.md`

中间过程稿、历史实验版本、服务器下载归档和临时输出已从最终交付目录中删除。

## 安装

```bash
cd /Users/maxxxxx/Desktop/NormCase-TARRAG_Final_Project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD/src
```

## 核验数据完整性

```bash
bash scripts/check_full_dataset.sh
```

成功时应看到：

```text
complete_lowaltbench_xl: true
corpus_rows: 5173
corpus_source_count: 88
source_vocab_count: 88
eval_task_count: 1200
```

## 单问题演示

```bash
bash scripts/run_normcase_demo.sh "深圳做无人机城市配送试点，需要从哪些方面做合规准备？"
```

## GitHub Pages 网页版

项目已新增 `docs/` 静态网页，可部署到 GitHub Pages：

- 网页入口：`docs/index.html`
- 网页数据：`docs/data/*.json`
- 数据构建脚本：`scripts/build_web_data.py`
- 部署说明：`GITHUB_PAGES_DEPLOY.md`

本地预览：

```bash
python3 -m http.server 8000 --directory docs
```

然后访问 `http://localhost:8000`。

网页包含法规库浏览、快速找法、NormCase-TARRAG 低空经济法律问答、案例责任研判、合规摘要和报告复制。模型名已在前端固定为 `deepseekv4pro`，用户可见的 API 配置页已移除。GitHub Pages 为静态托管，公开部署时建议通过后端代理保存 API Key。

## 案例责任预测实验

复制 `.env.example` 为 `.env` 并填入 API key 后运行：

```bash
cp .env.example .env
vim .env
bash scripts/run_normcase_case_experiment.sh
```

默认输入输出：

- 输入语料：`data/processed/corpus_case_enhanced.jsonl`
- 输入任务：`data/eval/cases/lowalt_case_eval_tasks_caseaware.jsonl`
- 案例数据：`data/cases/lowalt_case_seed.jsonl`
- 自动指标：`outputs/final/normcase_tarrag_case.json`
- 逐条预测：`outputs/final/normcase_tarrag_case_predictions.jsonl`
- judge 汇总：`outputs/final/normcase_tarrag_case_judge_summary.json`
- 结果报告：`paper/final/NormCase_TARRAG_Case_Experiment_Results.md`

已跑出的最终结果已另存为：

- `outputs/final/normcase_tarrag_case.json`
- `outputs/final/normcase_tarrag_case_predictions.jsonl`
- `outputs/final/normcase_tarrag_case_judge_scores.jsonl`
- `outputs/final/normcase_tarrag_case_judge_summary.json`
