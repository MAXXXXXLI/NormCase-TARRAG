# GitHub Pages 网页部署说明

本项目已经新增 `docs/` 静态网页目录，可直接使用 GitHub Pages 免费发布。

## 本地预览

在项目根目录运行：

```bash
python3 -m http.server 8000 --directory docs
```

然后打开：

```text
http://localhost:8000
```

## 发布到 GitHub Pages

1. 在 GitHub 新建仓库，例如 `NormCase-TARRAG`。
2. 将 `NormCase-TARRAG_Final_Project` 目录中的文件提交到仓库。
3. 进入仓库 `Settings` -> `Pages`。
4. `Source` 选择 `Deploy from a branch`。
5. `Branch` 选择 `main`，目录选择 `/docs`。
6. 保存后等待 GitHub Pages 构建完成。

发布后网页入口通常是：

```text
https://<你的 GitHub 用户名>.github.io/<仓库名>/
```

本项目当前已部署到：

```text
https://maxxxxxli.github.io/NormCase-TARRAG/
```

## 网页功能

- `法律问答`：支持快速找法、NormCase-TARRAG 低空经济合规问答、合规摘要和报告复制。
- `法规库`：按法规来源浏览 93 项来源、5191 个条文切片，并可打开原始页面或文件链接。
- `案例研判`：内置 15 个低空经济责任案例，可一键送入法律问答。

## API 与密钥安全

当前网页不再提供用户可见的 API 配置页。模型名已在前端固定为 `deepseekv4pro`，接口按 OpenAI-compatible `chat/completions` 调用。

GitHub Pages 是纯静态托管，不能安全保存服务端密钥。如果把 API Key 写入 `docs/assets/app.js`，公开仓库和网页访问者都能看到该 Key，适合私有演示，不适合公开生产使用。

正式公开使用时，建议：

- 自建一个后端代理或 serverless endpoint；
- 由代理保存真实 API Key；
- GitHub Pages 前端只调用代理地址；
- 代理限制域名、频率和模型参数。

## 重新生成网页数据

如果更新了 `data/processed/corpus_case_enhanced.jsonl`、案例或任务数据，运行：

```bash
python3 scripts/build_web_data.py
```

脚本会更新：

- `docs/data/corpus.json`
- `docs/data/sources.json`
- `docs/data/stats.json`
- `docs/data/cases.json`
- `docs/data/case_tasks.json`
