"""博客数据模型"""
from datetime import date
from pydantic import BaseModel
import yaml


class _QuotedStr(str):
    """用于强制YAML输出双引号的字符串包装"""
    pass


class _FlowList(list):
    """用于强制YAML输出行内数组格式 ["a", "b"]"""
    pass


def _quoted_str_representer(dumper: yaml.Dumper, data: _QuotedStr) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style='"')


def _flow_list_representer(dumper: yaml.Dumper, data: _FlowList) -> yaml.SequenceNode:
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


yaml.add_representer(_QuotedStr, _quoted_str_representer)
yaml.add_representer(_FlowList, _flow_list_representer)


def _quote_strings(obj: object) -> object:
    """递归地将字典/列表中的字符串包装为 _QuotedStr"""
    if isinstance(obj, str):
        return _QuotedStr(obj)
    elif isinstance(obj, dict):
        return {k: _quote_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_quote_strings(item) for item in obj]
    return obj


class TocItem(BaseModel):
    """目录项"""
    title: str
    link: str


class BlogPost(BaseModel):
    """博客文章"""
    # 基础信息
    page_h1_title: str
    meta_title: str
    url_slug: str
    meta_description: str
    summary: str

    # 媒体
    image: str

    # 元数据
    date: date
    editor_name: str
    content_type: str
    content_category: str
    tags: list[str]

    # 目录
    custom_toc: list[TocItem]

    # 内容
    category_folder: str
    content: str

    def get_file_path(self) -> str:
        """获取博客文件存放路径"""
        return f"content/{self.category_folder}/{self.url_slug}/index.md"

    def to_markdown(self) -> str:
        """生成完整的Markdown文件内容（包含frontmatter）"""
        frontmatter = {
            "page_h1_title": self.page_h1_title,
            "meta_title": self.meta_title,
            "url_slug": self.url_slug,
            "meta_description": self.meta_description,
            "summary": self.summary,
            "image": self.image,
            "date": self.date.isoformat(),
            "editor_name": self.editor_name,
            "content_type": self.content_type,
            "content_category": self.content_category,
            "tags": _FlowList([_QuotedStr(tag) for tag in self.tags]),
            "custom_toc": [item.model_dump() for item in self.custom_toc],
        }

        # 对除了 tags 之外的字符串字段应用引号
        quoted_frontmatter = {}
        for k, v in frontmatter.items():
            if k == "tags":
                quoted_frontmatter[k] = v  # 已处理
            else:
                quoted_frontmatter[k] = _quote_strings(v)

        yaml_str = yaml.dump(
            quoted_frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        return f"---\n{yaml_str}---\n\n{self.content}"
