# Blog Publisher 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为不熟悉Git的用户提供Web界面发布博客，自动创建GitLab Merge Request

**Architecture:** FastAPI后端 + Jinja2模板渲染 + 原生JS前端。持久化本地Git仓库，使用文件锁处理并发，通过GitLab API创建MR。

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, GitPython, python-gitlab, CodeMirror, marked.js

---

## 文件结构

```
blog-publisher/
├── pyproject.toml              # Task 1: 项目配置
├── .python-version             # Task 1: Python版本
├── config.py                   # Task 1: 应用配置
├── models/
│   ├── __init__.py             # Task 2: 模块初始化
│   └── blog.py                 # Task 2: 数据模型
├── services/
│   ├── __init__.py             # Task 3: 模块初始化
│   ├── git_service.py          # Task 3: Git操作服务
│   └── gitlab_service.py       # Task 4: GitLab API服务
├── main.py                     # Task 5: FastAPI应用
├── templates/
│   ├── base.html               # Task 6: 基础模板
│   ├── editor.html             # Task 6: 编辑器页面
│   └── success.html            # Task 6: 成功页面
└── static/
    ├── css/
    │   └── style.css           # Task 7: 样式
    └── js/
        └── editor.js           # Task 8: 编辑器逻辑
```

---

## Task 1: 项目初始化

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `config.py`

- [ ] **Step 1: 创建项目目录结构**

```bash
mkdir -p models services templates static/css static/js
```

- [ ] **Step 2: 创建 .python-version**

```
3.11
```

- [ ] **Step 3: 创建 pyproject.toml**

```toml
[project]
name = "blog-publisher"
version = "0.1.0"
description = "Web interface for publishing blog posts to GitLab"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "jinja2>=3.1.0",
    "gitpython>=3.1.0",
    "python-gitlab>=4.0.0",
    "pydantic>=2.0.0",
    "filelock>=3.13.0",
    "python-multipart>=0.0.6",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 4: 创建 config.py**

```python
"""应用配置"""

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

# 预定义的博客类别目录
CATEGORY_FOLDERS = [
    "30-day-sprint",
    "dev-diaries",
    "industry-insights",
    "product-updates",
    "research-notes",
    "tutorials",
]
```

- [ ] **Step 5: 安装依赖**

Run: `uv sync`
Expected: 依赖安装成功

- [ ] **Step 6: 验证安装**

Run: `uv run python -c "import fastapi; import git; import gitlab; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git init
git add pyproject.toml .python-version config.py
git commit -m "chore: initialize project with dependencies and config"
```

---

## Task 2: 数据模型

**Files:**
- Create: `models/__init__.py`
- Create: `models/blog.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: 创建 models/__init__.py**

```python
from .blog import BlogPost, TocItem

__all__ = ["BlogPost", "TocItem"]
```

- [ ] **Step 2: 创建测试文件 tests/test_models.py**

```bash
mkdir -p tests
```

```python
"""测试数据模型"""
import pytest
from datetime import date


def test_toc_item_creation():
    """测试TOC项创建"""
    from models.blog import TocItem
    
    item = TocItem(title="Test Title", link="#test-title")
    assert item.title == "Test Title"
    assert item.link == "#test-title"


def test_blog_post_creation():
    """测试博客文章创建"""
    from models.blog import BlogPost, TocItem
    
    post = BlogPost(
        page_h1_title="Test Blog",
        meta_title="Test Blog | Site",
        url_slug="test-blog",
        meta_description="A test blog post",
        summary="Test summary",
        image="https://example.com/image.png",
        date=date(2026, 4, 15),
        editor_name="Test Editor",
        content_type="tutorial",
        content_category="tech",
        tags=["python", "test"],
        custom_toc=[TocItem(title="Section 1", link="#section-1")],
        category_folder="tutorials",
        content="# Hello\n\nThis is content.",
    )
    assert post.url_slug == "test-blog"
    assert len(post.tags) == 2


def test_blog_post_to_markdown():
    """测试生成Markdown文件内容"""
    from models.blog import BlogPost, TocItem
    
    post = BlogPost(
        page_h1_title="Test Blog",
        meta_title="Test Blog | Site",
        url_slug="test-blog",
        meta_description="A test blog post",
        summary="Test summary",
        image="https://example.com/image.png",
        date=date(2026, 4, 15),
        editor_name="Test Editor",
        content_type="tutorial",
        content_category="tech",
        tags=["python", "test"],
        custom_toc=[TocItem(title="Section 1", link="#section-1")],
        category_folder="tutorials",
        content="# Hello\n\nThis is content.",
    )
    
    markdown = post.to_markdown()
    
    assert "---" in markdown
    assert 'page_h1_title: "Test Blog"' in markdown
    assert 'url_slug: "test-blog"' in markdown
    assert "# Hello" in markdown
    assert "This is content." in markdown


def test_blog_post_file_path():
    """测试生成文件路径"""
    from models.blog import BlogPost, TocItem
    
    post = BlogPost(
        page_h1_title="Test Blog",
        meta_title="Test Blog | Site",
        url_slug="test-blog",
        meta_description="A test blog post",
        summary="Test summary",
        image="https://example.com/image.png",
        date=date(2026, 4, 15),
        editor_name="Test Editor",
        content_type="tutorial",
        content_category="tech",
        tags=["python"],
        custom_toc=[],
        category_folder="tutorials",
        content="Content",
    )
    
    path = post.get_file_path()
    assert path == "content/tutorials/test-blog/index.md"
```

- [ ] **Step 3: 运行测试验证失败**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'models'"

- [ ] **Step 4: 创建 models/blog.py**

```python
"""博客数据模型"""
from datetime import date
from pydantic import BaseModel
import yaml


class TocItem(BaseModel):
    """目录项"""
    title: str
    link: str


class BlogPost(BaseModel):
    """博客文章"""
    # 基础信息
    page_h1_title: str
    meta_title: str
    url_slug: str
    meta_description: str
    summary: str
    
    # 媒体
    image: str
    
    # 元数据
    date: date
    editor_name: str
    content_type: str
    content_category: str
    tags: list[str]
    
    # 目录
    custom_toc: list[TocItem]
    
    # 内容
    category_folder: str
    content: str
    
    def get_file_path(self) -> str:
        """获取博客文件存放路径"""
        return f"content/{self.category_folder}/{self.url_slug}/index.md"
    
    def to_markdown(self) -> str:
        """生成完整的Markdown文件内容（包含frontmatter）"""
        frontmatter = {
            "page_h1_title": self.page_h1_title,
            "meta_title": self.meta_title,
            "url_slug": self.url_slug,
            "meta_description": self.meta_description,
            "summary": self.summary,
            "image": self.image,
            "date": self.date.isoformat(),
            "editor_name": self.editor_name,
            "content_type": self.content_type,
            "content_category": self.content_category,
            "tags": self.tags,
            "custom_toc": [item.model_dump() for item in self.custom_toc],
        }
        
        yaml_str = yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        return f"---\n{yaml_str}---\n\n{self.content}"
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_models.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add models/ tests/
git commit -m "feat: add BlogPost and TocItem data models"
```

---

## Task 3: Git服务

**Files:**
- Create: `services/__init__.py`
- Create: `services/git_service.py`
- Create: `tests/test_git_service.py`

- [ ] **Step 1: 创建 services/__init__.py**

```python
from .git_service import GitService
from .gitlab_service import GitLabService

__all__ = ["GitService", "GitLabService"]
```

- [ ] **Step 2: 创建测试文件 tests/test_git_service.py**

```python
"""测试Git服务"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_git_service_init():
    """测试GitService初始化"""
    from services.git_service import GitService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        service = GitService(
            repo_url="git@example.com:test/repo.git",
            local_path=tmpdir,
            ssh_key_path="/fake/key",
        )
        assert service.repo_url == "git@example.com:test/repo.git"
        assert service.local_path == Path(tmpdir)


def test_generate_branch_name():
    """测试分支名生成"""
    from services.git_service import GitService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        service = GitService(
            repo_url="git@example.com:test/repo.git",
            local_path=tmpdir,
            ssh_key_path="/fake/key",
        )
        
        branch_name = service.generate_branch_name("my-blog-post")
        
        assert branch_name.startswith("blog/my-blog-post-")
        assert len(branch_name) > len("blog/my-blog-post-")


def test_write_file():
    """测试写入文件"""
    from services.git_service import GitService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个假的git仓库目录
        repo_dir = Path(tmpdir) / "repo"
        repo_dir.mkdir()
        
        service = GitService(
            repo_url="git@example.com:test/repo.git",
            local_path=str(repo_dir),
            ssh_key_path="/fake/key",
        )
        
        file_path = "content/tutorials/test/index.md"
        content = "# Test\n\nContent here."
        
        service.write_file(file_path, content)
        
        full_path = repo_dir / file_path
        assert full_path.exists()
        assert full_path.read_text() == content
```

- [ ] **Step 3: 运行测试验证失败**

Run: `uv run pytest tests/test_git_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 4: 创建 services/git_service.py**

```python
"""Git操作服务"""
import os
from pathlib import Path
from datetime import datetime
from filelock import FileLock, Timeout
from git import Repo, GitCommandError


class GitServiceError(Exception):
    """Git服务错误"""
    pass


class GitService:
    """Git操作服务"""
    
    def __init__(
        self,
        repo_url: str,
        local_path: str,
        ssh_key_path: str,
        target_branch: str = "test",
    ):
        self.repo_url = repo_url
        self.local_path = Path(local_path)
        self.ssh_key_path = ssh_key_path
        self.target_branch = target_branch
        self._repo: Repo | None = None
        
        # 设置SSH命令环境变量
        self._git_ssh_cmd = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
    
    @property
    def lock_file(self) -> Path:
        """锁文件路径"""
        return self.local_path.parent / ".blog-publisher.lock"
    
    @property
    def repo(self) -> Repo:
        """获取仓库对象"""
        if self._repo is None:
            if not self.local_path.exists():
                raise GitServiceError(f"仓库目录不存在: {self.local_path}")
            self._repo = Repo(self.local_path)
        return self._repo
    
    def generate_branch_name(self, slug: str) -> str:
        """生成分支名"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"blog/{slug}-{timestamp}"
    
    def ensure_repo_exists(self) -> None:
        """确保仓库存在，不存在则clone"""
        if not self.local_path.exists():
            self.local_path.parent.mkdir(parents=True, exist_ok=True)
            env = {"GIT_SSH_COMMAND": self._git_ssh_cmd}
            Repo.clone_from(
                self.repo_url,
                self.local_path,
                env=env,
            )
            self._repo = None
    
    def sync_repo(self) -> None:
        """同步远程仓库到本地"""
        env = {"GIT_SSH_COMMAND": self._git_ssh_cmd}
        
        with self.repo.git.custom_environment(**env):
            self.repo.git.fetch("origin")
            self.repo.git.checkout(self.target_branch)
            self.repo.git.reset("--hard", f"origin/{self.target_branch}")
    
    def create_branch(self, branch_name: str) -> None:
        """创建并切换到新分支"""
        self.repo.git.checkout("-b", branch_name)
    
    def write_file(self, relative_path: str, content: str) -> Path:
        """写入文件到仓库"""
        full_path = self.local_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return full_path
    
    def check_path_exists(self, relative_path: str) -> bool:
        """检查路径是否已存在"""
        return (self.local_path / relative_path).exists()
    
    def commit_and_push(self, file_path: str, message: str, branch_name: str) -> None:
        """提交并推送到远程"""
        env = {"GIT_SSH_COMMAND": self._git_ssh_cmd}
        
        self.repo.git.add(file_path)
        self.repo.git.commit("-m", message)
        
        with self.repo.git.custom_environment(**env):
            self.repo.git.push("origin", branch_name)
    
    def acquire_lock(self, timeout: int = 60) -> FileLock:
        """获取仓库操作锁"""
        lock = FileLock(self.lock_file, timeout=timeout)
        try:
            lock.acquire()
            return lock
        except Timeout:
            raise GitServiceError("系统繁忙，请稍后重试")
    
    def publish_blog(
        self,
        file_path: str,
        content: str,
        slug: str,
        title: str,
    ) -> str:
        """
        发布博客完整流程
        
        Returns:
            分支名
        """
        lock = self.acquire_lock()
        
        try:
            # 确保仓库存在
            self.ensure_repo_exists()
            
            # 同步远程
            self.sync_repo()
            
            # 检查路径是否已存在
            dir_path = str(Path(file_path).parent)
            if self.check_path_exists(dir_path):
                raise GitServiceError(f"路径已存在: {dir_path}，请修改URL Slug")
            
            # 创建分支
            branch_name = self.generate_branch_name(slug)
            self.create_branch(branch_name)
            
            # 写入文件
            self.write_file(file_path, content)
            
            # 提交并推送
            commit_message = f"Add blog: {title}"
            self.commit_and_push(file_path, commit_message, branch_name)
            
            return branch_name
            
        except GitCommandError as e:
            raise GitServiceError(f"Git操作失败: {e}")
        finally:
            lock.release()
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_git_service.py -v`
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add services/git_service.py tests/test_git_service.py
git commit -m "feat: add GitService for git operations"
```

---

## Task 4: GitLab服务

**Files:**
- Create: `services/gitlab_service.py`
- Create: `tests/test_gitlab_service.py`

- [ ] **Step 1: 创建测试文件 tests/test_gitlab_service.py**

```python
"""测试GitLab服务"""
import pytest
from unittest.mock import patch, MagicMock


def test_gitlab_service_init():
    """测试GitLabService初始化"""
    from services.gitlab_service import GitLabService
    
    service = GitLabService(
        url="https://gitlab.example.com",
        token="test-token",
        project_id="123",
    )
    assert service.url == "https://gitlab.example.com"
    assert service.project_id == "123"


def test_create_merge_request():
    """测试创建MR"""
    from services.gitlab_service import GitLabService
    
    service = GitLabService(
        url="https://gitlab.example.com",
        token="test-token",
        project_id="123",
    )
    
    # Mock gitlab client
    mock_project = MagicMock()
    mock_mr = MagicMock()
    mock_mr.web_url = "https://gitlab.example.com/group/project/-/merge_requests/1"
    mock_project.mergerequests.create.return_value = mock_mr
    
    with patch.object(service, "_get_project", return_value=mock_project):
        mr_url = service.create_merge_request(
            source_branch="blog/test-123",
            target_branch="test",
            title="Add blog: Test Blog",
        )
    
    assert mr_url == "https://gitlab.example.com/group/project/-/merge_requests/1"
    mock_project.mergerequests.create.assert_called_once_with({
        "source_branch": "blog/test-123",
        "target_branch": "test",
        "title": "Add blog: Test Blog",
        "remove_source_branch": False,
    })


def test_get_manual_mr_url():
    """测试获取手动创建MR的URL"""
    from services.gitlab_service import GitLabService
    
    service = GitLabService(
        url="https://gitlab.example.com",
        token="test-token",
        project_id="group/project",
    )
    
    url = service.get_manual_mr_url("blog/test-123", "test")
    
    assert "gitlab.example.com" in url
    assert "blog/test-123" in url or "blog%2Ftest-123" in url
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_gitlab_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 创建 services/gitlab_service.py**

```python
"""GitLab API服务"""
import gitlab
from urllib.parse import quote


class GitLabServiceError(Exception):
    """GitLab服务错误"""
    pass


class GitLabService:
    """GitLab API服务"""
    
    def __init__(self, url: str, token: str, project_id: str):
        self.url = url
        self.token = token
        self.project_id = project_id
        self._client: gitlab.Gitlab | None = None
        self._project = None
    
    @property
    def client(self) -> gitlab.Gitlab:
        """获取GitLab客户端"""
        if self._client is None:
            self._client = gitlab.Gitlab(self.url, private_token=self.token)
        return self._client
    
    def _get_project(self):
        """获取项目对象"""
        if self._project is None:
            self._project = self.client.projects.get(self.project_id)
        return self._project
    
    def create_merge_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
    ) -> str:
        """
        创建Merge Request
        
        Returns:
            MR的Web URL
        """
        try:
            project = self._get_project()
            mr = project.mergerequests.create({
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "remove_source_branch": False,
            })
            return mr.web_url
        except gitlab.exceptions.GitlabError as e:
            raise GitLabServiceError(f"创建MR失败: {e}")
    
    def get_manual_mr_url(self, source_branch: str, target_branch: str) -> str:
        """
        获取手动创建MR的URL（当API创建失败时使用）
        """
        encoded_source = quote(source_branch, safe="")
        encoded_target = quote(target_branch, safe="")
        project_path = self.project_id.replace("/", "%2F") if "/" in str(self.project_id) else self.project_id
        
        return (
            f"{self.url}/{self.project_id}/-/merge_requests/new"
            f"?merge_request[source_branch]={encoded_source}"
            f"&merge_request[target_branch]={encoded_target}"
        )
```

- [ ] **Step 4: 更新 services/__init__.py**

```python
from .git_service import GitService, GitServiceError
from .gitlab_service import GitLabService, GitLabServiceError

__all__ = ["GitService", "GitServiceError", "GitLabService", "GitLabServiceError"]
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_gitlab_service.py -v`
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add services/ tests/test_gitlab_service.py
git commit -m "feat: add GitLabService for MR creation"
```

---

## Task 5: FastAPI主应用

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: 创建测试文件 tests/test_main.py**

```python
"""测试主应用"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """创建测试应用"""
    from main import app
    return app


@pytest.mark.asyncio
async def test_index_page(app):
    """测试首页渲染"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    
    assert response.status_code == 200
    assert "博客发布系统" in response.text


@pytest.mark.asyncio
async def test_get_categories(app):
    """测试获取类别列表"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/categories")
    
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "tutorials" in data["categories"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_main.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 创建 main.py**

```python
"""博客发布系统主应用"""
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
from models import BlogPost, TocItem
from services import GitService, GitServiceError, GitLabService, GitLabServiceError

app = FastAPI(title="博客发布系统")

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 服务实例
git_service = GitService(
    repo_url=config.REPO_URL,
    local_path=config.REPO_LOCAL_PATH,
    ssh_key_path=config.SSH_KEY_PATH,
    target_branch=config.TARGET_BRANCH,
)

gitlab_service = GitLabService(
    url=config.GITLAB_URL,
    token=config.GITLAB_TOKEN,
    project_id=config.GITLAB_PROJECT_ID,
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """编辑器页面"""
    return templates.TemplateResponse(
        "editor.html",
        {
            "request": request,
            "categories": config.CATEGORY_FOLDERS,
            "today": date.today().isoformat(),
        },
    )


@app.get("/api/categories")
async def get_categories():
    """获取类别列表"""
    return {"categories": config.CATEGORY_FOLDERS}


@app.post("/api/publish")
async def publish_blog(
    page_h1_title: Annotated[str, Form()],
    meta_title: Annotated[str, Form()],
    url_slug: Annotated[str, Form()],
    meta_description: Annotated[str, Form()],
    summary: Annotated[str, Form()],
    image: Annotated[str, Form()],
    post_date: Annotated[str, Form()],
    editor_name: Annotated[str, Form()],
    content_type: Annotated[str, Form()],
    content_category: Annotated[str, Form()],
    tags: Annotated[str, Form()],
    category_folder: Annotated[str, Form()],
    content: Annotated[str, Form()],
    toc_json: Annotated[str, Form()],
):
    """发布博客"""
    import json
    
    # 解析tags
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    # 解析TOC
    try:
        toc_data = json.loads(toc_json) if toc_json else []
        custom_toc = [TocItem(**item) for item in toc_data]
    except (json.JSONDecodeError, TypeError):
        custom_toc = []
    
    # 创建BlogPost
    try:
        post = BlogPost(
            page_h1_title=page_h1_title,
            meta_title=meta_title,
            url_slug=url_slug,
            meta_description=meta_description,
            summary=summary,
            image=image,
            date=date.fromisoformat(post_date),
            editor_name=editor_name,
            content_type=content_type,
            content_category=content_category,
            tags=tags_list,
            custom_toc=custom_toc,
            category_folder=category_folder,
            content=content,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"数据验证失败: {e}")
    
    # 生成Markdown内容
    markdown_content = post.to_markdown()
    file_path = post.get_file_path()
    
    # Git操作
    try:
        branch_name = git_service.publish_blog(
            file_path=file_path,
            content=markdown_content,
            slug=url_slug,
            title=page_h1_title,
        )
    except GitServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 创建MR
    mr_url = None
    manual_mr_url = gitlab_service.get_manual_mr_url(branch_name, config.TARGET_BRANCH)
    
    try:
        mr_url = gitlab_service.create_merge_request(
            source_branch=branch_name,
            target_branch=config.TARGET_BRANCH,
            title=f"Add blog: {page_h1_title}",
        )
    except GitLabServiceError:
        # MR创建失败，返回手动创建链接
        pass
    
    return {
        "success": True,
        "branch": branch_name,
        "mr_url": mr_url,
        "manual_mr_url": manual_mr_url,
        "file_path": file_path,
    }


@app.get("/success", response_class=HTMLResponse)
async def success_page(
    request: Request,
    branch: str = "",
    mr_url: str = "",
    manual_mr_url: str = "",
):
    """成功页面"""
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "branch": branch,
            "mr_url": mr_url,
            "manual_mr_url": manual_mr_url,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_main.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add FastAPI main application with routes"
```

---

## Task 6: HTML模板

**Files:**
- Create: `templates/base.html`
- Create: `templates/editor.html`
- Create: `templates/success.html`

- [ ] **Step 1: 创建 templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}博客发布系统{% endblock %}</title>
    
    <!-- CodeMirror -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/default.min.css">
    
    <!-- Highlight.js -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    
    <!-- Custom styles -->
    <link rel="stylesheet" href="/static/css/style.css">
    
    {% block head %}{% endblock %}
</head>
<body>
    <header>
        <h1>博客发布系统</h1>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <!-- CodeMirror -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/markdown/markdown.min.js"></script>
    
    <!-- Marked.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.1/marked.min.js"></script>
    
    <!-- Highlight.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: 创建 templates/editor.html**

```html
{% extends "base.html" %}

{% block title %}编辑博客 - 博客发布系统{% endblock %}

{% block content %}
<form id="blog-form" method="post" action="/api/publish">
    <!-- 基础信息 -->
    <section class="form-section">
        <h2>基础信息</h2>
        <div class="form-row">
            <label for="page_h1_title">页面标题 *</label>
            <input type="text" id="page_h1_title" name="page_h1_title" required>
        </div>
        <div class="form-row">
            <label for="meta_title">SEO标题 *</label>
            <input type="text" id="meta_title" name="meta_title" required>
        </div>
        <div class="form-row">
            <label for="url_slug">URL Slug *</label>
            <input type="text" id="url_slug" name="url_slug" required 
                   pattern="[a-z0-9\-]+" 
                   title="只能包含小写字母、数字和连字符">
        </div>
    </section>
    
    <!-- SEO信息 -->
    <section class="form-section">
        <h2>SEO信息</h2>
        <div class="form-row">
            <label for="meta_description">Meta描述 *</label>
            <textarea id="meta_description" name="meta_description" rows="2" required></textarea>
        </div>
        <div class="form-row">
            <label for="summary">摘要 *</label>
            <textarea id="summary" name="summary" rows="2" required></textarea>
        </div>
        <div class="form-row">
            <label for="image">封面图片URL *</label>
            <input type="url" id="image" name="image" required>
        </div>
    </section>
    
    <!-- 元数据 -->
    <section class="form-section">
        <h2>元数据</h2>
        <div class="form-grid">
            <div class="form-row">
                <label for="post_date">日期 *</label>
                <input type="date" id="post_date" name="post_date" value="{{ today }}" required>
            </div>
            <div class="form-row">
                <label for="editor_name">编辑者 *</label>
                <input type="text" id="editor_name" name="editor_name" required>
            </div>
            <div class="form-row">
                <label for="category_folder">目录 *</label>
                <select id="category_folder" name="category_folder" required>
                    {% for category in categories %}
                    <option value="{{ category }}">{{ category }}</option>
                    {% endfor %}
                    <option value="__new__">+ 新建目录</option>
                </select>
                <input type="text" id="new_category" placeholder="输入新目录名" style="display:none;">
            </div>
        </div>
        <div class="form-grid">
            <div class="form-row">
                <label for="content_type">内容类型 *</label>
                <input type="text" id="content_type" name="content_type" required>
            </div>
            <div class="form-row">
                <label for="content_category">内容分类 *</label>
                <input type="text" id="content_category" name="content_category" required>
            </div>
            <div class="form-row">
                <label for="tags">标签（逗号分隔）*</label>
                <input type="text" id="tags" name="tags" required placeholder="tag1, tag2, tag3">
            </div>
        </div>
    </section>
    
    <!-- Markdown编辑 -->
    <section class="form-section">
        <h2>Markdown内容</h2>
        <div class="editor-container">
            <div class="editor-pane">
                <h3>编辑</h3>
                <textarea id="content" name="content"></textarea>
            </div>
            <div class="preview-pane">
                <h3>预览</h3>
                <div id="preview"></div>
            </div>
        </div>
    </section>
    
    <!-- TOC -->
    <section class="form-section">
        <h2>目录 (TOC) <button type="button" id="refresh-toc" class="btn-small">刷新</button></h2>
        <div id="toc-container">
            <p class="hint">从Markdown内容中自动解析二级标题生成目录</p>
            <div id="toc-list"></div>
            <button type="button" id="add-toc" class="btn-small">+ 添加目录项</button>
        </div>
        <input type="hidden" id="toc_json" name="toc_json" value="[]">
    </section>
    
    <!-- 提交 -->
    <section class="form-actions">
        <button type="submit" class="btn-primary" id="submit-btn">提交博客</button>
        <span id="submit-status"></span>
    </section>
</form>
{% endblock %}

{% block scripts %}
<script src="/static/js/editor.js"></script>
{% endblock %}
```

- [ ] **Step 3: 创建 templates/success.html**

```html
{% extends "base.html" %}

{% block title %}发布成功 - 博客发布系统{% endblock %}

{% block content %}
<div class="success-container">
    <div class="success-icon">✓</div>
    <h2>博客发布成功！</h2>
    
    <div class="success-details">
        <p><strong>分支名：</strong> {{ branch }}</p>
        
        {% if mr_url %}
        <p>
            <strong>Merge Request：</strong>
            <a href="{{ mr_url }}" target="_blank">{{ mr_url }}</a>
        </p>
        {% else %}
        <p class="warning">
            MR自动创建失败，请手动创建：
            <a href="{{ manual_mr_url }}" target="_blank">点击这里创建MR</a>
        </p>
        {% endif %}
    </div>
    
    <div class="success-actions">
        <a href="/" class="btn-primary">发布新博客</a>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: 验证模板渲染**

Run: `uv run python -c "from fastapi.templating import Jinja2Templates; t = Jinja2Templates(directory='templates'); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add templates/
git commit -m "feat: add HTML templates for editor and success pages"
```

---

## Task 7: CSS样式

**Files:**
- Create: `static/css/style.css`

- [ ] **Step 1: 创建 static/css/style.css**

```css
/* 基础样式 */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f5f5f5;
}

header {
    background: #2c3e50;
    color: white;
    padding: 1rem 2rem;
}

header h1 {
    font-size: 1.5rem;
    font-weight: 500;
}

main {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}

/* 表单样式 */
.form-section {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.form-section h2 {
    font-size: 1.1rem;
    color: #2c3e50;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #eee;
}

.form-row {
    margin-bottom: 1rem;
}

.form-row label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #555;
}

.form-row input[type="text"],
.form-row input[type="url"],
.form-row input[type="date"],
.form-row textarea,
.form-row select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    transition: border-color 0.2s;
}

.form-row input:focus,
.form-row textarea:focus,
.form-row select:focus {
    outline: none;
    border-color: #3498db;
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
}

@media (max-width: 768px) {
    .form-grid {
        grid-template-columns: 1fr;
    }
}

/* 编辑器样式 */
.editor-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    min-height: 400px;
}

.editor-pane,
.preview-pane {
    display: flex;
    flex-direction: column;
}

.editor-pane h3,
.preview-pane h3 {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 0.5rem;
}

.editor-pane .CodeMirror {
    flex: 1;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.preview-pane #preview {
    flex: 1;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1rem;
    overflow-y: auto;
    background: #fafafa;
}

/* 预览内容样式 */
#preview h1, #preview h2, #preview h3 {
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}

#preview h1 { font-size: 1.5rem; }
#preview h2 { font-size: 1.3rem; }
#preview h3 { font-size: 1.1rem; }

#preview p {
    margin-bottom: 1rem;
}

#preview code {
    background: #f0f0f0;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-family: monospace;
}

#preview pre {
    background: #f8f8f8;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
}

#preview pre code {
    background: none;
    padding: 0;
}

/* TOC样式 */
#toc-container {
    padding: 1rem;
    background: #fafafa;
    border-radius: 4px;
}

#toc-container .hint {
    color: #888;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.toc-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 0.5rem;
}

.toc-item input[type="checkbox"] {
    width: auto;
}

.toc-item input[type="text"] {
    flex: 1;
    padding: 0.4rem;
    border: 1px solid #ddd;
    border-radius: 3px;
}

.toc-item .toc-link {
    width: 150px;
    color: #666;
}

.toc-item button {
    padding: 0.3rem 0.6rem;
    background: #e74c3c;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
}

/* 按钮样式 */
.btn-primary {
    display: inline-block;
    padding: 0.75rem 2rem;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    text-decoration: none;
    transition: background 0.2s;
}

.btn-primary:hover {
    background: #2980b9;
}

.btn-primary:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
}

.btn-small {
    padding: 0.3rem 0.8rem;
    background: #ecf0f1;
    border: 1px solid #ddd;
    border-radius: 3px;
    cursor: pointer;
    font-size: 0.9rem;
}

.btn-small:hover {
    background: #ddd;
}

.form-actions {
    text-align: center;
    padding: 1rem;
}

#submit-status {
    margin-left: 1rem;
    color: #666;
}

/* 成功页面样式 */
.success-container {
    max-width: 600px;
    margin: 2rem auto;
    text-align: center;
    background: white;
    padding: 3rem;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.success-icon {
    width: 80px;
    height: 80px;
    line-height: 80px;
    font-size: 40px;
    background: #27ae60;
    color: white;
    border-radius: 50%;
    margin: 0 auto 1.5rem;
}

.success-container h2 {
    color: #27ae60;
    margin-bottom: 1.5rem;
}

.success-details {
    text-align: left;
    background: #f8f8f8;
    padding: 1.5rem;
    border-radius: 4px;
    margin-bottom: 1.5rem;
}

.success-details p {
    margin-bottom: 0.5rem;
    word-break: break-all;
}

.success-details a {
    color: #3498db;
}

.success-details .warning {
    color: #e67e22;
}

.success-actions {
    margin-top: 1.5rem;
}
```

- [ ] **Step 2: Commit**

```bash
git add static/css/style.css
git commit -m "feat: add CSS styles for blog publisher"
```

---

## Task 8: 前端JavaScript

**Files:**
- Create: `static/js/editor.js`

- [ ] **Step 1: 创建 static/js/editor.js**

```javascript
/**
 * 博客编辑器JavaScript
 */

// 全局变量
let editor = null;
let tocItems = [];

/**
 * 初始化CodeMirror编辑器
 */
function initEditor() {
    const textarea = document.getElementById('content');
    editor = CodeMirror.fromTextArea(textarea, {
        mode: 'markdown',
        lineNumbers: true,
        lineWrapping: true,
        theme: 'default',
    });
    
    // 监听内容变化，更新预览
    editor.on('change', function() {
        updatePreview();
    });
    
    // 初始预览
    updatePreview();
}

/**
 * 更新Markdown预览
 */
function updatePreview() {
    const content = editor.getValue();
    const preview = document.getElementById('preview');
    
    // 使用marked渲染Markdown
    preview.innerHTML = marked.parse(content);
    
    // 高亮代码块
    preview.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

/**
 * 从Markdown内容解析TOC
 */
function parseTocFromContent() {
    const content = editor.getValue();
    const lines = content.split('\n');
    const items = [];
    
    lines.forEach(line => {
        // 匹配二级标题 ## Title
        const match = line.match(/^##\s+(.+)$/);
        if (match) {
            const title = match[1].trim();
            const link = '#' + title
                .toLowerCase()
                .replace(/[^\w\s\-]/g, '')  // 去除特殊字符
                .replace(/\s+/g, '-')        // 空格转连字符
                .replace(/-+/g, '-')         // 多个连字符合并
                .replace(/^-|-$/g, '');      // 去除首尾连字符
            
            items.push({
                title: title,
                link: link,
                enabled: true
            });
        }
    });
    
    return items;
}

/**
 * 刷新TOC列表
 */
function refreshToc() {
    tocItems = parseTocFromContent();
    renderTocList();
}

/**
 * 渲染TOC列表到DOM
 */
function renderTocList() {
    const container = document.getElementById('toc-list');
    container.innerHTML = '';
    
    tocItems.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'toc-item';
        div.innerHTML = `
            <input type="checkbox" ${item.enabled ? 'checked' : ''} 
                   onchange="toggleTocItem(${index}, this.checked)">
            <input type="text" value="${escapeHtml(item.title)}" 
                   onchange="updateTocTitle(${index}, this.value)">
            <input type="text" class="toc-link" value="${escapeHtml(item.link)}" 
                   onchange="updateTocLink(${index}, this.value)">
            <button type="button" onclick="removeTocItem(${index})">删除</button>
        `;
        container.appendChild(div);
    });
    
    updateTocJson();
}

/**
 * 切换TOC项启用状态
 */
function toggleTocItem(index, enabled) {
    tocItems[index].enabled = enabled;
    updateTocJson();
}

/**
 * 更新TOC项标题
 */
function updateTocTitle(index, title) {
    tocItems[index].title = title;
    updateTocJson();
}

/**
 * 更新TOC项链接
 */
function updateTocLink(index, link) {
    tocItems[index].link = link;
    updateTocJson();
}

/**
 * 删除TOC项
 */
function removeTocItem(index) {
    tocItems.splice(index, 1);
    renderTocList();
}

/**
 * 添加新TOC项
 */
function addTocItem() {
    tocItems.push({
        title: '新目录项',
        link: '#new-section',
        enabled: true
    });
    renderTocList();
}

/**
 * 更新隐藏的TOC JSON字段
 */
function updateTocJson() {
    const enabledItems = tocItems
        .filter(item => item.enabled)
        .map(item => ({
            title: item.title,
            link: item.link
        }));
    
    document.getElementById('toc_json').value = JSON.stringify(enabledItems);
}

/**
 * HTML转义
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 处理新建目录选项
 */
function handleCategoryChange() {
    const select = document.getElementById('category_folder');
    const newInput = document.getElementById('new_category');
    
    if (select.value === '__new__') {
        newInput.style.display = 'block';
        newInput.required = true;
        newInput.focus();
    } else {
        newInput.style.display = 'none';
        newInput.required = false;
    }
}

/**
 * 处理表单提交
 */
async function handleSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = document.getElementById('submit-btn');
    const status = document.getElementById('submit-status');
    
    // 处理新建目录
    const categorySelect = document.getElementById('category_folder');
    const newCategory = document.getElementById('new_category');
    if (categorySelect.value === '__new__' && newCategory.value) {
        // 创建新的option并选中
        const option = document.createElement('option');
        option.value = newCategory.value;
        option.textContent = newCategory.value;
        categorySelect.insertBefore(option, categorySelect.lastElementChild);
        categorySelect.value = newCategory.value;
    }
    
    // 同步CodeMirror内容到textarea
    editor.save();
    
    // 禁用提交按钮
    submitBtn.disabled = true;
    status.textContent = '正在提交...';
    
    try {
        const formData = new FormData(form);
        
        const response = await fetch('/api/publish', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // 跳转到成功页面
            const params = new URLSearchParams({
                branch: data.branch,
                mr_url: data.mr_url || '',
                manual_mr_url: data.manual_mr_url || ''
            });
            window.location.href = '/success?' + params.toString();
        } else {
            throw new Error(data.detail || '提交失败');
        }
    } catch (error) {
        status.textContent = '错误: ' + error.message;
        submitBtn.disabled = false;
    }
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化编辑器
    initEditor();
    
    // 绑定TOC刷新按钮
    document.getElementById('refresh-toc').addEventListener('click', refreshToc);
    
    // 绑定添加TOC按钮
    document.getElementById('add-toc').addEventListener('click', addTocItem);
    
    // 绑定目录选择变化
    document.getElementById('category_folder').addEventListener('change', handleCategoryChange);
    
    // 绑定表单提交
    document.getElementById('blog-form').addEventListener('submit', handleSubmit);
    
    // 初始化TOC
    refreshToc();
});
```

- [ ] **Step 2: 测试前端功能**

Run: `uv run uvicorn main:app --reload`

手动测试：
1. 访问 http://localhost:8000
2. 验证CodeMirror编辑器加载
3. 输入Markdown内容，验证右侧预览更新
4. 添加 `## 标题`，点击"刷新"按钮，验证TOC自动生成
5. 编辑/删除/添加TOC项
6. 选择"新建目录"，输入新目录名

Expected: 所有功能正常工作

- [ ] **Step 3: Commit**

```bash
git add static/js/editor.js
git commit -m "feat: add frontend JavaScript for editor, preview, and TOC"
```

---

## Task 9: 集成测试

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: 创建集成测试文件**

```python
"""集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import date


@pytest.fixture
def app():
    """创建测试应用"""
    from main import app
    return app


@pytest.fixture
def mock_git_service():
    """Mock Git服务"""
    with patch('main.git_service') as mock:
        mock.publish_blog.return_value = "blog/test-post-20260415120000"
        yield mock


@pytest.fixture
def mock_gitlab_service():
    """Mock GitLab服务"""
    with patch('main.gitlab_service') as mock:
        mock.create_merge_request.return_value = "https://gitlab.example.com/group/project/-/merge_requests/1"
        mock.get_manual_mr_url.return_value = "https://gitlab.example.com/group/project/-/merge_requests/new"
        yield mock


@pytest.mark.asyncio
async def test_full_publish_flow(app, mock_git_service, mock_gitlab_service):
    """测试完整发布流程"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        form_data = {
            "page_h1_title": "Test Blog Post",
            "meta_title": "Test Blog | Site",
            "url_slug": "test-blog-post",
            "meta_description": "A test blog post description",
            "summary": "Test summary for the blog post",
            "image": "https://example.com/image.png",
            "post_date": "2026-04-15",
            "editor_name": "Test Editor",
            "content_type": "tutorial",
            "content_category": "tech",
            "tags": "python, testing, integration",
            "category_folder": "tutorials",
            "content": "# Hello World\n\nThis is test content.",
            "toc_json": '[{"title": "Hello World", "link": "#hello-world"}]',
        }
        
        response = await client.post("/api/publish", data=form_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["branch"] == "blog/test-post-20260415120000"
    assert data["mr_url"] == "https://gitlab.example.com/group/project/-/merge_requests/1"
    
    # 验证Git服务被正确调用
    mock_git_service.publish_blog.assert_called_once()
    call_kwargs = mock_git_service.publish_blog.call_args[1]
    assert call_kwargs["slug"] == "test-blog-post"
    assert call_kwargs["title"] == "Test Blog Post"
    assert "content/tutorials/test-blog-post/index.md" in call_kwargs["file_path"]


@pytest.mark.asyncio
async def test_publish_with_mr_failure(app, mock_git_service, mock_gitlab_service):
    """测试MR创建失败时返回手动链接"""
    from services.gitlab_service import GitLabServiceError
    
    mock_gitlab_service.create_merge_request.side_effect = GitLabServiceError("API Error")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        form_data = {
            "page_h1_title": "Test Blog Post",
            "meta_title": "Test Blog | Site",
            "url_slug": "test-blog-post",
            "meta_description": "Description",
            "summary": "Summary",
            "image": "https://example.com/image.png",
            "post_date": "2026-04-15",
            "editor_name": "Editor",
            "content_type": "tutorial",
            "content_category": "tech",
            "tags": "test",
            "category_folder": "tutorials",
            "content": "Content",
            "toc_json": "[]",
        }
        
        response = await client.post("/api/publish", data=form_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["mr_url"] is None
    assert data["manual_mr_url"] is not None


@pytest.mark.asyncio
async def test_publish_with_git_failure(app, mock_git_service, mock_gitlab_service):
    """测试Git操作失败时返回错误"""
    from services.git_service import GitServiceError
    
    mock_git_service.publish_blog.side_effect = GitServiceError("路径已存在")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        form_data = {
            "page_h1_title": "Test Blog Post",
            "meta_title": "Test Blog | Site",
            "url_slug": "existing-slug",
            "meta_description": "Description",
            "summary": "Summary",
            "image": "https://example.com/image.png",
            "post_date": "2026-04-15",
            "editor_name": "Editor",
            "content_type": "tutorial",
            "content_category": "tech",
            "tags": "test",
            "category_folder": "tutorials",
            "content": "Content",
            "toc_json": "[]",
        }
        
        response = await client.post("/api/publish", data=form_data)
    
    assert response.status_code == 500
    data = response.json()
    assert "路径已存在" in data["detail"]
```

- [ ] **Step 2: 运行所有测试**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for publish flow"
```

---

## Task 10: 最终验证与文档

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 README.md**

```markdown
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
```

- [ ] **Step 2: 运行完整测试套件**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: 启动应用进行手动验证**

Run: `uv run uvicorn main:app --reload`

手动测试清单：
1. [ ] 访问首页，表单正常显示
2. [ ] CodeMirror编辑器正常工作
3. [ ] Markdown实时预览正常
4. [ ] TOC自动解析正常
5. [ ] TOC手动编辑正常
6. [ ] 新建目录功能正常
7. [ ] 表单验证正常（必填字段）

- [ ] **Step 4: Final Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```

- [ ] **Step 5: 查看完整提交历史**

Run: `git log --oneline`

Expected commits:
```
docs: add README with setup and usage instructions
test: add integration tests for publish flow
feat: add frontend JavaScript for editor, preview, and TOC
feat: add CSS styles for blog publisher
feat: add HTML templates for editor and success pages
feat: add FastAPI main application with routes
feat: add GitLabService for MR creation
feat: add GitService for git operations
feat: add BlogPost and TocItem data models
chore: initialize project with dependencies and config
```

---

## 自审检查

- [x] **Spec覆盖**: 所有需求已在Task中实现
- [x] **无占位符**: 所有代码完整，无TBD/TODO
- [x] **类型一致**: 所有类型、方法名在各Task中保持一致
- [x] **完整路径**: 所有文件路径明确
- [x] **完整命令**: 所有命令包含预期输出
