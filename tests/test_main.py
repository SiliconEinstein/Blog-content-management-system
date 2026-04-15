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
