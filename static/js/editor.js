/**
 * 博客编辑器JavaScript
 */

// 全局变量
let editor = null;
let tocItems = [];

/**
 * 初始化CodeMirror编辑器
 */
function initEditor() {
    const textarea = document.getElementById('content');
    editor = CodeMirror.fromTextArea(textarea, {
        mode: 'markdown',
        lineNumbers: true,
        lineWrapping: true,
        theme: 'default',
    });

    // 监听内容变化，更新预览
    editor.on('change', function() {
        updatePreview();
    });

    // 初始预览
    updatePreview();
}

/**
 * 更新Markdown预览
 */
function updatePreview() {
    const content = editor.getValue();
    const preview = document.getElementById('preview');

    // 使用marked渲染Markdown
    preview.innerHTML = marked.parse(content);

    // 高亮代码块
    preview.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

/**
 * 从Markdown内容解析TOC
 */
function parseTocFromContent() {
    const content = editor.getValue();
    const lines = content.split('\n');
    const items = [];

    lines.forEach(line => {
        // 匹配二级标题 ## Title
        const match = line.match(/^##\s+(.+)$/);
        if (match) {
            const title = match[1].trim();
            const link = '#' + title
                .toLowerCase()
                .replace(/[^\w\s\-]/g, '')  // 去除特殊字符
                .replace(/\s+/g, '-')        // 空格转连字符
                .replace(/-+/g, '-')         // 多个连字符合并
                .replace(/^-|-$/g, '');      // 去除首尾连字符

            items.push({
                title: title,
                link: link,
                enabled: true
            });
        }
    });

    return items;
}

/**
 * 刷新TOC列表
 */
function refreshToc() {
    tocItems = parseTocFromContent();
    renderTocList();
}

/**
 * 渲染TOC列表到DOM
 */
function renderTocList() {
    const container = document.getElementById('toc-list');
    container.innerHTML = '';

    tocItems.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'toc-item';
        div.innerHTML = `
            <input type="checkbox" ${item.enabled ? 'checked' : ''}
                   onchange="toggleTocItem(${index}, this.checked)">
            <input type="text" value="${escapeHtml(item.title)}"
                   onchange="updateTocTitle(${index}, this.value)">
            <input type="text" class="toc-link" value="${escapeHtml(item.link)}"
                   onchange="updateTocLink(${index}, this.value)">
            <button type="button" onclick="removeTocItem(${index})">删除</button>
        `;
        container.appendChild(div);
    });

    updateTocJson();
}

/**
 * 切换TOC项启用状态
 */
function toggleTocItem(index, enabled) {
    tocItems[index].enabled = enabled;
    updateTocJson();
}

/**
 * 更新TOC项标题
 */
function updateTocTitle(index, title) {
    tocItems[index].title = title;
    updateTocJson();
}

/**
 * 更新TOC项链接
 */
function updateTocLink(index, link) {
    tocItems[index].link = link;
    updateTocJson();
}

/**
 * 删除TOC项
 */
function removeTocItem(index) {
    tocItems.splice(index, 1);
    renderTocList();
}

/**
 * 添加新TOC项
 */
function addTocItem() {
    tocItems.push({
        title: '新目录项',
        link: '#new-section',
        enabled: true
    });
    renderTocList();
}

/**
 * 更新隐藏的TOC JSON字段
 */
function updateTocJson() {
    const enabledItems = tocItems
        .filter(item => item.enabled)
        .map(item => ({
            title: item.title,
            link: item.link
        }));

    document.getElementById('toc_json').value = JSON.stringify(enabledItems);
}

/**
 * HTML转义
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 处理新建目录选项
 */
function handleCategoryChange() {
    const select = document.getElementById('category_folder');
    const newInput = document.getElementById('new_category');

    if (select.value === '__new__') {
        newInput.style.display = 'block';
        newInput.required = true;
        newInput.focus();
    } else {
        newInput.style.display = 'none';
        newInput.required = false;
    }
}

/**
 * 处理表单提交
 */
async function handleSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = document.getElementById('submit-btn');
    const status = document.getElementById('submit-status');

    // 处理新建目录
    const categorySelect = document.getElementById('category_folder');
    const newCategory = document.getElementById('new_category');
    if (categorySelect.value === '__new__' && newCategory.value) {
        // 创建新的option并选中
        const option = document.createElement('option');
        option.value = newCategory.value;
        option.textContent = newCategory.value;
        categorySelect.insertBefore(option, categorySelect.lastElementChild);
        categorySelect.value = newCategory.value;
    }

    // 同步CodeMirror内容到textarea
    editor.save();

    // 禁用提交按钮
    submitBtn.disabled = true;
    status.textContent = '正在提交...';

    try {
        const formData = new FormData(form);

        const response = await fetch('/api/publish', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // 跳转到成功页面
            const params = new URLSearchParams({
                branch: data.branch,
                mr_url: data.mr_url || '',
                manual_mr_url: data.manual_mr_url || ''
            });
            window.location.href = '/success?' + params.toString();
        } else {
            throw new Error(data.detail || '提交失败');
        }
    } catch (error) {
        status.textContent = '错误: ' + error.message;
        submitBtn.disabled = false;
    }
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化编辑器
    initEditor();

    // 绑定TOC刷新按钮
    document.getElementById('refresh-toc').addEventListener('click', refreshToc);

    // 绑定添加TOC按钮
    document.getElementById('add-toc').addEventListener('click', addTocItem);

    // 绑定目录选择变化
    document.getElementById('category_folder').addEventListener('change', handleCategoryChange);

    // 绑定表单提交
    document.getElementById('blog-form').addEventListener('submit', handleSubmit);

    // 初始化TOC
    refreshToc();
});
