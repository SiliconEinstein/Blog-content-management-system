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
