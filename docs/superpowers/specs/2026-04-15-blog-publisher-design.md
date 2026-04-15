# Blog Publisher 设计文档

## 概述

为不熟悉Git的用户提供一个Web界面，用于发布博客文章。用户只需在页面上填写表单和编写Markdown内容，系统自动完成Git操作并创建Merge Request供管理员审核。

## 需求

### 功能需求

- 无需登录认证，任何人可访问
- 提供Markdown编辑器，支持分栏实时预览
- 用户填写frontmatter字段和正文内容
- 自动从正文解析TOC，用户可编辑调整
- 提交后自动创建GitLab Merge Request
- MR合并到test分支后上线，源分支保留

### 技术要求

- 使用统一SSH key访问GitLab
- 使用uv管理Python依赖
- 本地服务器运行

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                      浏览器                              │
│  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  表单区域        │  │  Markdown预览区域            │  │
│  │  - Frontmatter  │  │  (marked.js实时渲染)         │  │
│  │  - CodeMirror   │  │                             │  │
│  └─────────────────┘  └─────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP POST
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI 后端                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 页面路由      │  │ 表单处理      │  │ Git服务      │  │
│  │ (Jinja2)     │  │ (验证/组装)   │  │ (GitPython)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │ SSH
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    GitLab 仓库                          │
│  - 持久化本地仓库副本                                    │
│  - 创建分支、写入文件、push                              │
│  - 通过GitLab API创建Merge Request                      │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
blog-publisher/
├── pyproject.toml          # uv项目配置
├── .python-version         # Python版本锁定
├── config.py               # 配置（GitLab地址、SSH key路径、仓库路径等）
├── main.py                 # FastAPI入口
│
├── services/
│   ├── __init__.py
│   ├── git_service.py      # Git操作（clone、branch、commit、push）
│   └── gitlab_service.py   # GitLab API（创建MR）
│
├── models/
│   ├── __init__.py
│   └── blog.py             # 博客数据模型（Pydantic）
│
├── templates/
│   ├── base.html           # 基础布局
│   ├── editor.html         # 博客编辑页面
│   └── success.html        # 提交成功页面
│
└── static/
    ├── css/
    │   └── style.css       # 样式
    └── js/
        └── editor.js       # 编辑器逻辑（CodeMirror初始化、预览、TOC解析）
```

### 模块职责

| 模块 | 职责 |
|------|------|
| `main.py` | 路由定义、页面渲染、表单接收 |
| `git_service.py` | 仓库同步、分支创建、文件写入、push |
| `gitlab_service.py` | 调用GitLab API创建Merge Request |
| `models/blog.py` | 表单数据验证、Markdown文件生成 |
| `editor.js` | Markdown编辑器、实时预览、TOC自动提取 |

## 数据模型

### BlogPost（Pydantic模型）

```python
class TocItem(BaseModel):
    title: str
    link: str

class BlogPost(BaseModel):
    # 基础信息
    page_h1_title: str          # 页面H1标题
    meta_title: str             # SEO标题
    url_slug: str               # URL路径（文件夹名）
    meta_description: str       # SEO描述
    summary: str                # 摘要
    
    # 媒体
    image: str                  # 封面图片URL
    
    # 元数据
    date: date                  # 发布日期
    editor_name: str            # 编辑者
    content_type: str           # 内容类型（自由输入）
    content_category: str       # 内容分类（自由输入）
    tags: list[str]             # 标签列表（自由输入，逗号分隔输入，后端解析为数组）
    
    # 目录
    custom_toc: list[TocItem]   # 自动解析+用户可编辑
    
    # 内容
    category_folder: str        # 所属目录
    content: str                # Markdown正文
```

### 博客存放路径

```
/content/{category_folder}/{url_slug}/index.md
```

**category_folder 可选值**（可新增）：
- 30-day-sprint
- dev-diaries
- industry-insights
- product-updates
- research-notes
- tutorials

### 生成的Markdown文件格式

```markdown
---
page_h1_title: "..."
meta_title: "..."
url_slug: "..."
meta_description: "..."
summary: "..."
image: "..."
date: 2026-04-15
editor_name: "..."
content_type: "..."
content_category: "..."
tags: ["...", "..."]
custom_toc:
  - title: "..."
    link: "#..."
---

{Markdown正文内容}
```

## Git操作流程

### 持久化仓库策略

服务器上保留一个持久化的仓库副本，每次操作前同步远程状态。

```
/data/blog-repo/              ← 持久化的仓库副本（配置文件指定路径）
└── {仓库名}/
    ├── content/
    └── ...
```

### 提交流程

```
1. 用户点击提交
       │
       ▼
2. 后端验证表单数据
       │ 失败 → 返回错误提示
       ▼
3. 获取仓库操作锁（防止并发冲突）
       │ 获取失败 → 提示"系统繁忙，请稍后重试"
       ▼
4. 同步远程仓库
       │  - git fetch origin
       │  - git checkout test
       │  - git reset --hard origin/test
       │ 失败 → 释放锁，返回错误
       ▼
5. 创建新分支：blog/{url_slug}-{timestamp}
       │
       ▼
6. 创建目录：content/{category_folder}/{url_slug}/
       │
       ▼
7. 写入文件：index.md
       │
       ▼
8. git add → git commit → git push origin {branch}
       │ 失败 → 释放锁，返回错误
       ▼
9. 调用GitLab API创建Merge Request
       │  - source_branch: blog/{url_slug}-{timestamp}
       │  - target_branch: test
       │  - title: "Add blog: {page_h1_title}"
       │  - remove_source_branch: false（保留分支）
       │ 失败 → 提示push成功但MR创建失败，提供手动链接
       ▼
10. 释放仓库操作锁
       │
       ▼
11. 返回成功页面（含MR链接）
```

### 并发控制

- 使用 `filelock` 库实现文件锁
- 锁文件路径：`/data/blog-repo/.blog-publisher.lock`
- 锁超时：60秒

### 首次初始化

应用启动时检查持久化目录是否存在，不存在则自动 `git clone`。

## 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 表单验证失败 | 返回表单页，显示具体错误字段 |
| Git clone/pull失败 | 提示网络或权限问题，建议检查SSH配置 |
| Git push失败 | 提示分支冲突或权限问题 |
| MR创建失败 | 提示push已成功，提供手动创建MR的GitLab链接 |
| url_slug已存在 | 提交前检查，提示用户修改slug |
| 获取锁失败 | 提示"系统繁忙，请稍后重试" |

## 前端设计

### 页面布局

```
┌─────────────────────────────────────────────────────────────────┐
│  博客发布系统                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ 基础信息 ──────────────────────────────────────────────────┐│
│  │ 页面标题: [________________________]                        ││
│  │ SEO标题:  [________________________]                        ││
│  │ URL Slug: [________________________]                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─ SEO信息 ───────────────────────────────────────────────────┐│
│  │ Meta描述: [________________________________________________]││
│  │ 摘要:     [________________________________________________]││
│  │ 封面图片: [________________________________________________]││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─ 元数据 ────────────────────────────────────────────────────┐│
│  │ 日期: [2026-04-15]  编辑者: [________]  目录: [▼ 选择类别 ] ││
│  │ 内容类型: [________]  分类: [________]  标签: [___________] ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─ Markdown编辑 ──────────────────────────────────────────────┐│
│  │ ┌─────────────────────┐  ┌─────────────────────┐           ││
│  │ │ (CodeMirror编辑器)  │  │ (marked.js预览)     │           ││
│  │ └─────────────────────┘  └─────────────────────┘           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─ 目录(TOC) [自动生成] ──────────────────────────────────────┐│
│  │ ☑ Title 1                         #link-1          [删除]  ││
│  │ ☑ Title 2                         #link-2          [删除]  ││
│  │ [+ 添加目录项]                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│                              [提交博客]                         │
└─────────────────────────────────────────────────────────────────┘
```

### TOC自动解析逻辑

1. 监听Markdown内容变化
2. 正则提取 `## 标题` 格式的二级标题
3. 生成link：标题转小写 → 空格转连字符 → 去除特殊字符
4. 示例："What Is the H-Index?" → "#what-is-the-h-index"

### 用户可调整TOC

- 勾选/取消勾选来包含或排除某个目录项
- 手动编辑title和link
- 添加/删除目录项

## 配置

### config.py

```python
# GitLab配置
GITLAB_URL = "https://gitlab.example.com"
GITLAB_PROJECT_ID = "123"  # 或 "group/project"
GITLAB_TOKEN = "glpat-xxxx"  # 用于创建MR的API Token

# Git配置
REPO_URL = "git@gitlab.example.com:group/project.git"
REPO_LOCAL_PATH = "/data/blog-repo"
SSH_KEY_PATH = "/home/user/.ssh/id_rsa"
TARGET_BRANCH = "test"

# 应用配置
HOST = "0.0.0.0"
PORT = 8000
```

## 依赖

### Python依赖（pyproject.toml）

| 包 | 用途 |
|-----|------|
| `fastapi` | Web框架 |
| `uvicorn` | ASGI服务器 |
| `jinja2` | 模板引擎 |
| `gitpython` | Git操作 |
| `python-gitlab` | GitLab API |
| `pydantic` | 数据验证 |
| `filelock` | 并发锁 |
| `python-multipart` | 表单解析 |

### 前端依赖（CDN引入）

| 库 | 用途 |
|-----|------|
| `codemirror` | Markdown编辑器 |
| `marked` | Markdown渲染 |
| `highlight.js` | 代码高亮（可选） |

## 部署

1. 服务器安装Python 3.11+和uv
2. 配置SSH key用于访问GitLab
3. 创建GitLab API Token（需要api权限）
4. 修改config.py中的配置项
5. 运行 `uv run uvicorn main:app --host 0.0.0.0 --port 8000`
