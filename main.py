"""博客发布系统主应用"""
from datetime import date
from functools import lru_cache
from typing import Annotated
import json

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator

from config import Settings, get_settings
from models import BlogPost, TocItem
from services import GitService, GitServiceError, GitLabService, GitLabServiceError

app = FastAPI(title="博客发布系统")

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class PublishRequest(BaseModel):
    """发布博客请求模型"""

    model_config = ConfigDict(str_strip_whitespace=True)

    page_h1_title: str = Field(min_length=1, max_length=200)
    meta_title: str = Field(min_length=1, max_length=200)
    url_slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    meta_description: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=1, max_length=500)
    image: HttpUrl
    post_date: date
    editor_name: str = Field(min_length=1, max_length=100)
    content_type: str = Field(min_length=1, max_length=50)
    content_category: str = Field(min_length=1, max_length=50)
    tags: list[str]
    category_folder: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    custom_toc: list[TocItem]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        cleaned_tags = [tag.strip() for tag in value if tag.strip()]
        if not cleaned_tags:
            raise ValueError("至少需要一个标签")
        return cleaned_tags

    @field_validator("category_folder")
    @classmethod
    def validate_category_folder(cls, value: str) -> str:
        if "/" in value or ".." in value:
            raise ValueError("分类目录不合法")
        return value


def parse_toc_items(toc_json: str) -> list[TocItem]:
    """解析目录 JSON"""
    if not toc_json:
        return []

    try:
        toc_data = json.loads(toc_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"TOC JSON 格式错误: {exc}") from exc

    if not isinstance(toc_data, list):
        raise HTTPException(status_code=400, detail="TOC 必须是数组")

    try:
        return [TocItem(**item) for item in toc_data]
    except (TypeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=f"TOC 数据验证失败: {exc}") from exc


@lru_cache
def get_git_service() -> GitService:
    """获取 Git 服务单例"""
    settings = get_settings()
    return GitService(
        repo_url=settings.repo_url,
        local_path=settings.repo_local_path,
        username=settings.git_username,
        token=settings.git_token,
        target_branch=settings.target_branch,
    )


@lru_cache
def get_gitlab_service() -> GitLabService:
    """获取 GitLab 服务单例"""
    settings = get_settings()
    return GitLabService(
        url=settings.gitlab_url,
        token=settings.gitlab_token,
        project_id=settings.gitlab_project_id,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, settings: Settings = Depends(get_settings)):
    """编辑器页面"""
    return templates.TemplateResponse(
        request,
        "editor.html",
        {
            "categories": settings.category_folders,
            "today": date.today().isoformat(),
        },
    )


@app.get("/api/categories")
async def get_categories(settings: Settings = Depends(get_settings)):
    """获取类别列表"""
    return {"categories": settings.category_folders}


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
    settings: Settings = Depends(get_settings),
    git_service: GitService = Depends(get_git_service),
    gitlab_service: GitLabService = Depends(get_gitlab_service),
):
    """发布博客"""
    custom_toc = parse_toc_items(toc_json)

    try:
        publish_request = PublishRequest(
            page_h1_title=page_h1_title,
            meta_title=meta_title,
            url_slug=url_slug,
            meta_description=meta_description,
            summary=summary,
            image=image,
            post_date=post_date,
            editor_name=editor_name,
            content_type=content_type,
            content_category=content_category,
            tags=tags.split(","),
            category_folder=category_folder,
            content=content,
            custom_toc=custom_toc,
        )
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=f"数据验证失败: {e}")

    if publish_request.category_folder not in settings.category_folders:
        raise HTTPException(status_code=400, detail="分类目录不存在")

    post = BlogPost(
        page_h1_title=publish_request.page_h1_title,
        meta_title=publish_request.meta_title,
        url_slug=publish_request.url_slug,
        meta_description=publish_request.meta_description,
        summary=publish_request.summary,
        image=str(publish_request.image),
        date=publish_request.post_date,
        editor_name=publish_request.editor_name,
        content_type=publish_request.content_type,
        content_category=publish_request.content_category,
        tags=publish_request.tags,
        custom_toc=publish_request.custom_toc,
        category_folder=publish_request.category_folder,
        content=publish_request.content,
    )

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
    manual_mr_url = gitlab_service.get_manual_mr_url(branch_name, settings.target_branch)

    try:
        mr_url = gitlab_service.create_merge_request(
            source_branch=branch_name,
            target_branch=settings.target_branch,
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
        request,
        "success.html",
        {
            "branch": branch,
            "mr_url": mr_url,
            "manual_mr_url": manual_mr_url,
        },
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
