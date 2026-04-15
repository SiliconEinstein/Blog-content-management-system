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
        known_hosts_path: str | None = None,
    ):
        self.repo_url = repo_url
        self.local_path = Path(local_path)
        self.ssh_key_path = ssh_key_path
        self.target_branch = target_branch
        self._repo: Repo | None = None

        # 构建SSH命令，使用指定的known_hosts文件进行主机密钥验证
        if known_hosts_path:
            self._git_ssh_cmd = (
                f'ssh -i {ssh_key_path} '
                f'-o UserKnownHostsFile={known_hosts_path} '
                f'-o StrictHostKeyChecking=yes'
            )
        else:
            # 回退：使用系统默认的known_hosts
            self._git_ssh_cmd = f'ssh -i {ssh_key_path}'

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
        git_dir = self.local_path / ".git"
        if not git_dir.exists():
            if self.local_path.exists():
                # 目录存在但不是 git 仓库，拒绝操作而非删除
                raise GitServiceError(
                    f"目录 {self.local_path} 已存在但不是 Git 仓库，"
                    "请手动检查或删除后重试"
                )
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
