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

编辑 `config.py` 配置以下项目：

```python
# GitLab配置
GITLAB_URL = "https://gitlab.example.com"
GITLAB_PROJECT_ID = "123"
GITLAB_TOKEN = "glpat-xxxx"

# Git配置
REPO_URL = "git@gitlab.example.com:group/project.git"
REPO_LOCAL_PATH = "/data/blog-repo"
SSH_KEY_PATH = "/home/user/.ssh/id_rsa"
TARGET_BRANCH = "test"

# 应用配置
HOST = "0.0.0.0"
PORT = 8000
```

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
