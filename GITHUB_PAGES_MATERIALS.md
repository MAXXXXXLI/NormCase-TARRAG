# GitHub Pages 免费部署教材清单

本项目适合使用 GitHub Pages 的 `/docs` 目录发布方式。当前网页入口已经在：

```text
docs/index.html
```

## 推荐教材

1. GitHub 官方中文快速入门
   - https://docs.github.com/zh/pages/quickstart?library=true
   - 适合先了解 GitHub Pages 是什么、怎么创建仓库、怎么打开 Pages。

2. GitHub 官方创建 Pages 站点
   - https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
   - 重点看 `index.html`、仓库、发布后访问网址。

3. GitHub 官方配置发布源
   - https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
   - 重点看 `main` 分支和 `/docs` 文件夹发布。

4. 中文零基础教程
   - https://aimaker.dev/guide/getting-started/github-pages
   - 适合按截图一步步操作。

## 本项目最短部署路径

### 1. 准备 GitHub 账号

需要你登录：打开 https://github.com 并登录账号。

### 2. 新建仓库

需要你登录后操作：

- 点击右上角 `+`
- 选择 `New repository`
- 仓库名可以用 `NormCase-TARRAG`
- 选择 `Public`
- 创建仓库

### 3. 上传项目文件

需要你登录后操作：

- 进入新仓库
- 上传 `NormCase-TARRAG_Final_Project` 里面的全部文件
- 确保仓库根目录下面能看到 `docs/index.html`

### 4. 打开 GitHub Pages

需要你登录后操作：

- 进入仓库 `Settings`
- 左侧找到 `Pages`
- `Source` 选择 `Deploy from a branch`
- `Branch` 选择 `main`
- 文件夹选择 `/docs`
- 点击保存

### 5. 访问网站

等待 1 到 10 分钟，GitHub Pages 会生成网址，一般是：

```text
https://你的用户名.github.io/仓库名/
```

## 注意事项

- GitHub Free 免费账号可以用 public repository 发布 GitHub Pages。
- 本项目是静态网页，适合 GitHub Pages。
- 真实 API Key 不建议放到公开仓库；如果必须写死，公开访问者可能看到。
- 如果网站打开是 404，优先检查 `docs/index.html` 是否存在，以及 Pages 是否选了 `/docs`。
