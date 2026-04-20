"""应用配置 - 从环境变量读取"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # GitLab配置
    gitlab_url: str = "https://gitlab.example.invalid/"
    gitlab_project_id: str = "group/project"
    gitlab_token: str = ""

    # Git配置
    repo_url: str = "https://gitlab.example.invalid/group/project.git"
    repo_local_path: str = "/tmp/blog-repo"
    git_username: str = "oauth2"
    git_token: str = ""
    git_commit_name: str = "Blog Publisher"
    git_commit_email: str = "blog-publisher@example.com"
    target_branch: str = "test"

    # 应用配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 预定义的博客类别目录
    category_folders: list[str] = [
        "30-day-sprint",
        "dev-diaries",
        "industry-insights",
        "product-updates",
        "research-notes",
        "tutorials",
    ]


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
