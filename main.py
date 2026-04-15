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
        request,
        "editor.html",
        {
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
    uvicorn.run(app, host=config.HOST, port=config.PORT)
