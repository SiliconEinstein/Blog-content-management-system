"""测试数据模型"""
import pytest
from datetime import date


def test_toc_item_creation():
    """测试TOC项创建"""
    from models.blog import TocItem

    item = TocItem(title="Test Title", link="#test-title")
    assert item.title == "Test Title"
    assert item.link == "#test-title"


def test_blog_post_creation():
    """测试博客文章创建"""
    from models.blog import BlogPost, TocItem

    post = BlogPost(
        page_h1_title="Test Blog",
        meta_title="Test Blog | Site",
        url_slug="test-blog",
        meta_description="A test blog post",
        summary="Test summary",
        image="https://example.com/image.png",
        date=date(2026, 4, 15),
        editor_name="Test Editor",
        content_type="tutorial",
        content_category="tech",
        tags=["python", "test"],
        custom_toc=[TocItem(title="Section 1", link="#section-1")],
        category_folder="tutorials",
        content="# Hello\n\nThis is content.",
    )
    assert post.url_slug == "test-blog"
    assert len(post.tags) == 2


def test_blog_post_to_markdown():
    """测试生成Markdown文件内容"""
    from models.blog import BlogPost, TocItem

    post = BlogPost(
        page_h1_title="Test Blog",
        meta_title="Test Blog | Site",
        url_slug="test-blog",
        meta_description="A test blog post",
        summary="Test summary",
        image="https://example.com/image.png",
        date=date(2026, 4, 15),
        editor_name="Test Editor",
        content_type="tutorial",
        content_category="tech",
        tags=["python", "test"],
        custom_toc=[TocItem(title="Section 1", link="#section-1")],
        category_folder="tutorials",
        content="# Hello\n\nThis is content.",
    )

    markdown = post.to_markdown()

    assert "---" in markdown
    assert 'page_h1_title: "Test Blog"' in markdown
    assert 'url_slug: "test-blog"' in markdown
    assert "# Hello" in markdown
    assert "This is content." in markdown


def test_blog_post_file_path():
    """测试生成文件路径"""
    from models.blog import BlogPost, TocItem

    post = BlogPost(
        page_h1_title="Test Blog",
        meta_title="Test Blog | Site",
        url_slug="test-blog",
        meta_description="A test blog post",
        summary="Test summary",
        image="https://example.com/image.png",
        date=date(2026, 4, 15),
        editor_name="Test Editor",
        content_type="tutorial",
        content_category="tech",
        tags=["python"],
        custom_toc=[],
        category_folder="tutorials",
        content="Content",
    )

    path = post.get_file_path()
    assert path == "content/tutorials/test-blog/index.md"
