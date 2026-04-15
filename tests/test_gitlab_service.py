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
