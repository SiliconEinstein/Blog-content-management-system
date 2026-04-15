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
