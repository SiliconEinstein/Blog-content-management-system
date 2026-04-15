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
