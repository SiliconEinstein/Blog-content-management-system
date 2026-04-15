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
