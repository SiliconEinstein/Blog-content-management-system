# Blog Publisher

Web界面博客发布系统，自动处理Git操作并创建GitLab Merge Request。

## 功能

- Markdown编辑器，支持实时预览
- 自动从内容解析目录(TOC)
- 表单填写博客元数据
- 自动Git操作（clone、branch、commit、push）
- 自动创建GitLab Merge Request

## 安装

```bash
# 安装依赖
uv sync

# 安装开发依赖
uv sync --extra dev
```

## 配置

复制 `.env.example` 为 `.env`，并配置以下项目：

```bash
# GitLab 配置
GITLAB_URL=https://gitlab.example.com
GITLAB_PROJECT_ID=group/project
GITLAB_TOKEN=glpat-xxxx

# Git HTTPS 配置
REPO_URL=https://gitlab.example.com/group/project.git
REPO_LOCAL_PATH=/data/blog-repo
GIT_USERNAME=oauth2
GIT_TOKEN=glpat-xxxx
GIT_COMMIT_NAME=Blog Publisher
GIT_COMMIT_EMAIL=blog-publisher@example.com
TARGET_BRANCH=test

# 应用配置
HOST=0.0.0.0
PORT=8000
```

说明：

- `GITLAB_TOKEN` 用于 GitLab API 创建 Merge Request
- `GIT_TOKEN` 用于通过 HTTPS clone/fetch/push 仓库
- 如 GitLab 配置允许，`GIT_USERNAME` 通常可使用 `oauth2`
- `GIT_COMMIT_NAME` 和 `GIT_COMMIT_EMAIL` 用于设置提交者身份（显示在 commit 记录中）

## 运行

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

或直接运行：

```bash
uv run python main.py
```

## 测试

```bash
uv run pytest tests/ -v
```

## 使用

1. 访问 http://localhost:8000
2. 填写博客元数据表单
3. 在Markdown编辑器中编写内容
4. 点击"刷新"生成目录，可手动调整
5. 点击"提交博客"
6. 等待管理员审核Merge Request
