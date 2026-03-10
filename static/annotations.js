/**
 * CopyEZ 交互式划线笔记功能
 * 模拟微信读书和 Word 批注的体验
 */

(function() {
    'use strict';

    // 全局状态
    const state = {
        noteId: null,
        annotations: [],
        currentSelection: null,
        popupMenu: null,
        commentDialog: null
    };

    /**
     * 前端清洗函数：去除 HTML 中段落文本的行首空格
     * 使用 JavaScript 的正则表达式：text.replace(/^[ \t\u00A0\u3000]+/gm, '')
     * 确保渲染出的 <p> 标签内部第一字符就是正文
     * 
     * 注意：此函数会保留 HTML 结构（如高亮标记），只清洗文本节点的行首空格
     */
    function cleanParagraphText(htmlContent) {
        if (!htmlContent) return htmlContent;
        
        // 创建一个临时 DOM 容器来解析 HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;
        
        // 遍历所有段落元素，清洗其第一个文本节点的行首空格
        const paragraphs = tempDiv.querySelectorAll('p.paragraph');
        paragraphs.forEach(p => {
            // 使用 TreeWalker 遍历所有文本节点
            const walker = document.createTreeWalker(
                p,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            // 找到第一个非空文本节点
            let textNode = walker.nextNode();
            while (textNode) {
                const originalText = textNode.textContent;
                if (originalText.trim()) {
                    // 去除行首的所有空格、制表符、不间断空格、全角空格
                    // 使用全局多行模式，确保匹配每一行的开头
                    const cleanedText = originalText.replace(/^[ \t\u00A0\u3000]+/gm, '');
                    if (originalText !== cleanedText) {
                        textNode.textContent = cleanedText;
                    }
                    // 只处理第一个非空文本节点
                    break;
                }
                textNode = walker.nextNode();
            }
        });
        
        return tempDiv.innerHTML;
    }

    /**
     * 初始化功能
     */
    function init() {
        initAnnotations();
        
        // 监听内容重新加载事件，重新加载批注
        window.addEventListener('contentReloaded', function() {
            console.log('[annotations] 检测到内容重新加载，重新加载批注');
            // 清空当前批注状态
            state.annotations = [];
            // 重新加载批注
            setTimeout(() => {
                loadAnnotations();
            }, 200);
        });
    }
    
    /**
     * 初始化批注功能（实际初始化逻辑）
     */
    function initAnnotations() {
        // 获取笔记 ID
        const noteIdMatch = window.location.pathname.match(/\/note\/(\d+)/);
        if (!noteIdMatch) return;
        
        state.noteId = parseInt(noteIdMatch[1]);
        
        // 初始化全局选区快照
        window.lastSelection = null;
        
        // 创建浮窗菜单
        createPopupMenu();
        
        // 创建批注输入弹窗
        createCommentDialog();
        
        // 加载已有批注
        loadAnnotations();
        
        // 监听正文区域的鼠标抬起事件
        const docContent = document.querySelector('.doc-content');
        if (docContent) {
            docContent.addEventListener('mouseup', handleMouseUp);
            // 点击其他地方时隐藏浮窗
            document.addEventListener('click', handleDocumentClick);
        }
        
        // 监听选区变化事件，实时更新选区快照
        document.addEventListener('selectionchange', handleSelectionChange);
        
        // 初始化深度思考的块状化功能
        initGlobalThoughtBlocks();
        
        // 初始化大纲展开/收起功能
        initOutlineToggle();
    }

    /**
     * 创建浮窗菜单（修正图标逻辑）
     */
    function createPopupMenu() {
        const popup = document.createElement('div');
        popup.className = 'annotation-popup';
        popup.innerHTML = `
            <button class="popup-btn" data-action="bold" title="加粗">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
                    <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>
                </svg>
            </button>
            <button class="popup-btn" data-action="blue" title="标蓝">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <path d="M9 9h6v6H9z"></path>
                </svg>
            </button>
            <button class="popup-btn" data-action="red" title="标红">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <path d="M9 9h6v6H9z"></path>
                </svg>
            </button>
            <button class="popup-btn" data-action="comment" title="写批注">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            </button>
            <div class="popup-divider"></div>
            <button class="popup-btn" data-action="remove" title="取消标注">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
            <button class="popup-btn" data-action="copy" title="复制">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
            </button>
        `;
        
        document.body.appendChild(popup);
        state.popupMenu = popup;
        
        // 绑定按钮事件
        popup.addEventListener('click', handlePopupAction);
    }

    /**
     * 创建批注输入弹窗
     */
    function createCommentDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'comment-dialog';
        dialog.innerHTML = `
            <div class="comment-dialog-content">
                <div class="comment-dialog-header">
                    <span class="comment-dialog-title">添加批注</span>
                    <button class="comment-dialog-close" aria-label="关闭">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <textarea 
                    class="comment-dialog-textarea" 
                    placeholder="输入批注内容（支持多行）..."
                    rows="4"
                ></textarea>
                <div class="comment-dialog-actions">
                    <button class="comment-dialog-cancel">Cancel</button>
                    <button class="comment-dialog-submit">Save</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        state.commentDialog = dialog;
        
        // 绑定关闭事件
        const closeBtn = dialog.querySelector('.comment-dialog-close');
        const cancelBtn = dialog.querySelector('.comment-dialog-cancel');
        const submitBtn = dialog.querySelector('.comment-dialog-submit');
        
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            hideCommentDialog();
        });
        cancelBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            hideCommentDialog();
        });
        submitBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            handleCommentSubmit();
        });
        
        // 点击背景关闭
        dialog.addEventListener('click', function(e) {
            if (e.target === dialog) {
                hideCommentDialog();
            }
        });
        
        // 阻止对话框内容区域的点击事件冒泡
        const dialogContent = dialog.querySelector('.comment-dialog-content');
        if (dialogContent) {
            dialogContent.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
        
        // ESC 键关闭
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && dialog.style.display === 'flex') {
                hideCommentDialog();
            }
        });
    }

    /**
     * 检查选中区域是否已有标注
     */
    function checkExistingHighlight(range) {
        const commonAncestor = range.commonAncestorContainer;
        let node = commonAncestor.nodeType === Node.TEXT_NODE 
            ? commonAncestor.parentElement 
            : commonAncestor;
        
        // 向上查找包含选中区域的 span 标注
        while (node && node !== document.body) {
            if (node.classList && (
                node.classList.contains('hl-blue') || 
                node.classList.contains('hl-red') || 
                node.classList.contains('hl-bold')
            )) {
                // 检查选中区域是否完全在这个标注内
                const nodeRange = document.createRange();
                nodeRange.selectNodeContents(node);
                if (range.compareBoundaryPoints(Range.START_TO_START, nodeRange) >= 0 &&
                    range.compareBoundaryPoints(Range.END_TO_END, nodeRange) <= 0) {
                    return {
                        element: node,
                        type: node.classList.contains('hl-blue') ? 'blue' :
                              node.classList.contains('hl-red') ? 'red' : 'bold'
                    };
                }
            }
            node = node.parentElement;
        }
        return null;
    }

    /**
     * 处理选区变化事件（实时更新选区快照）
     */
    function handleSelectionChange() {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        // 检查选择是否在正文区域内
        const docContent = document.querySelector('.doc-content');
        if (!docContent || selection.rangeCount === 0) {
            return;
        }
        
        const anchorNode = selection.anchorNode;
        if (!anchorNode || !docContent.contains(anchorNode)) {
            return;
        }
        
        // 如果有选中文本，保存到全局快照
        if (selectedText && selectedText.length > 0) {
            try {
                const range = selection.getRangeAt(0);
                if (!range.collapsed) {
                    window.lastSelection = {
                        range: range.cloneRange(),
                        text: selectedText,
                        timestamp: Date.now()
                    };
                }
            } catch (err) {
                // 忽略错误，可能选择无效
            }
        }
    }

    /**
     * 处理鼠标抬起事件（增强版：支持点击已标注区域）
     */
    function handleMouseUp(e) {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        // Debug: 打印选区信息
        console.log('[handleMouseUp] 开始处理鼠标抬起事件');
        console.log('[handleMouseUp] selectedText:', selectedText);
        console.log('[handleMouseUp] selection.rangeCount:', selection.rangeCount);
        
        // 检查选择是否在正文区域内
        const docContent = document.querySelector('.doc-content');
        if (!docContent) {
            console.warn('[handleMouseUp] .doc-content 不存在');
            hidePopup();
            return;
        }
        
        // 验证选区是否有效
        if (selection.rangeCount === 0) {
            console.log('[handleMouseUp] 没有有效的选区');
            hidePopup();
            return;
        }
        
        const anchorNode = selection.anchorNode;
        if (!anchorNode) {
            console.warn('[handleMouseUp] anchorNode 为 null');
            hidePopup();
            return;
        }
        
        // 严格验证选区是否在正文区域内
        if (!docContent.contains(anchorNode)) {
            console.log('[handleMouseUp] 选区不在 .doc-content 内，anchorNode:', anchorNode);
            hidePopup();
            return;
        }
        
        // 获取 range 并验证
        let range;
        try {
            range = selection.getRangeAt(0);
            if (!range) {
                console.warn('[handleMouseUp] range 为 null');
                hidePopup();
                return;
            }
            
            // 验证 range.commonAncestorContainer 是否属于 .doc-content
            const commonAncestor = range.commonAncestorContainer;
            const ancestorElement = commonAncestor.nodeType === Node.TEXT_NODE 
                ? commonAncestor.parentElement 
                : commonAncestor;
            
            if (!ancestorElement || !docContent.contains(ancestorElement)) {
                console.warn('[handleMouseUp] range.commonAncestorContainer 不在 .doc-content 内');
                console.warn('[handleMouseUp] ancestorElement:', ancestorElement);
                hidePopup();
                return;
            }
            
            console.log('[handleMouseUp] range 验证通过，commonAncestor:', ancestorElement);
        } catch (err) {
            console.error('[handleMouseUp] 获取 range 失败:', err);
            hidePopup();
            return;
        }
        
        // 如果没有选中文本，检查是否点击了已标注区域
        if (!selectedText || selectedText.length === 0) {
            // 检查点击的元素是否是标注
            const clickedElement = e.target.closest('.hl-blue, .hl-red, .hl-bold');
            if (clickedElement) {
                // 选中该标注的文字，并显示工具栏
                try {
                    const range = document.createRange();
                    range.selectNodeContents(clickedElement);
                    selection.removeAllRanges();
                    selection.addRange(range);
                    
                    // 保存当前选择到 state 和全局快照
                    const selectedText = clickedElement.textContent.trim();
                    const selectionData = {
                        range: range.cloneRange(),
                        text: selectedText,
                        timestamp: Date.now(),
                        clickedElement: clickedElement // 保存点击的元素，用于后续操作
                    };
                    state.currentSelection = selectionData;
                    window.lastSelection = selectionData;
                    
                    // 显示浮窗
                    showPopup(e);
                } catch (err) {
                    console.error('[handleMouseUp] 选中标注文字失败:', err);
                    hidePopup();
                }
            } else {
                hidePopup();
            }
            return;
        }
        
        // 保存当前选择到 state 和全局快照
        try {
            const selectionData = {
                range: range.cloneRange(),
                text: selectedText,
                timestamp: Date.now()
            };
            state.currentSelection = selectionData;
            window.lastSelection = selectionData;
            
            console.log('[handleMouseUp] 选区已保存，text:', selectedText);
            console.log('[handleMouseUp] state.currentSelection:', state.currentSelection);
        } catch (err) {
            console.error('[handleMouseUp] 保存选区失败:', err);
            hidePopup();
            return;
        }
        
        // 显示浮窗
        showPopup(e);
    }

    /**
     * 显示浮窗菜单
     */
    function showPopup(e) {
        if (!state.popupMenu || !state.currentSelection) return;
        
        const popup = state.popupMenu;
        const range = state.currentSelection.range;
        const rect = range.getBoundingClientRect();
        
        // 计算浮窗位置（在选中文本上方）
        const popupTop = rect.top + window.scrollY - 45;
        const popupLeft = rect.left + window.scrollX + (rect.width / 2) - 100;
        
        popup.style.top = popupTop + 'px';
        popup.style.left = popupLeft + 'px';
        popup.style.display = 'flex';
        
        // 检查当前选中区域是否已有标注，如果有则高亮对应的按钮
        const existing = checkExistingHighlight(range);
        if (existing) {
            // 移除所有按钮的激活状态
            popup.querySelectorAll('.popup-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // 激活对应的按钮
            const actionBtn = popup.querySelector(`[data-action="${existing.type}"]`);
            if (actionBtn) {
                actionBtn.classList.add('active');
            }
            
            // 显示"取消"和"复制"按钮（如果之前隐藏了）
            const removeBtn = popup.querySelector('[data-action="remove"]');
            const copyBtn = popup.querySelector('[data-action="copy"]');
            const divider = popup.querySelector('.popup-divider');
            if (removeBtn) removeBtn.style.display = 'flex';
            if (copyBtn) copyBtn.style.display = 'flex';
            if (divider) divider.style.display = 'block';
        } else {
            // 如果没有标注，隐藏"取消"按钮，但保留"复制"按钮
            const removeBtn = popup.querySelector('[data-action="remove"]');
            const divider = popup.querySelector('.popup-divider');
            if (removeBtn) removeBtn.style.display = 'none';
            if (divider) divider.style.display = 'none';
            
            // 移除所有按钮的激活状态
            popup.querySelectorAll('.popup-btn').forEach(btn => {
                btn.classList.remove('active');
            });
        }
    }

    /**
     * 隐藏浮窗菜单
     */
    function hidePopup() {
        if (state.popupMenu) {
            state.popupMenu.style.display = 'none';
        }
        // 注意：不清除 state.currentSelection 和 window.lastSelection
        // 因为用户可能点击"写批注"按钮，需要保留选区数据
    }

    /**
     * 处理文档点击事件（点击其他地方时隐藏浮窗）
     */
    function handleDocumentClick(e) {
        // 如果点击的是 popup 菜单本身或其子元素，不隐藏
        if (state.popupMenu && state.popupMenu.contains(e.target)) {
            return;
        }
        
        // 如果点击的是批注输入弹窗，不隐藏浮窗
        if (state.commentDialog && state.commentDialog.contains(e.target)) {
            return;
        }
        
        // 如果点击的是正文区域，也不隐藏（允许在正文区域继续选择）
        const docContent = document.querySelector('.doc-content');
        if (docContent && docContent.contains(e.target)) {
            // 只有在点击正文区域且没有选中文本时才隐藏浮窗
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0 || selection.toString().trim().length === 0) {
                hidePopup();
            }
            return;
        }
        
        // 点击其他地方时隐藏浮窗
        hidePopup();
    }

    /**
     * 处理浮窗按钮点击
     */
    function handlePopupAction(e) {
        // 阻止事件冒泡，避免触发 handleDocumentClick
        e.stopPropagation();
        
        const btn = e.target.closest('.popup-btn');
        if (!btn) {
            console.log('[handlePopupAction] 点击的不是按钮');
            return;
        }
        
        const action = btn.getAttribute('data-action');
        console.log('[handlePopupAction] 按钮点击，action:', action);
        console.log('[handlePopupAction] state.currentSelection:', state.currentSelection);
        console.log('[handlePopupAction] window.lastSelection:', window.lastSelection);
        
        // 优先使用 state.currentSelection，如果为空则从全局快照恢复
        let selectionToUse = state.currentSelection;
        if (!selectionToUse && window.lastSelection) {
            try {
                selectionToUse = {
                    range: window.lastSelection.range.cloneRange(),
                    text: window.lastSelection.text,
                    timestamp: window.lastSelection.timestamp,
                    clickedElement: window.lastSelection.clickedElement || null // 恢复点击的元素
                };
                state.currentSelection = selectionToUse;
                console.log('[handlePopupAction] 从 window.lastSelection 恢复选区');
            } catch (err) {
                console.error('[handlePopupAction] 恢复选区失败:', err);
            }
        }
        
        if (!selectionToUse) {
            console.error('[handlePopupAction] 没有可用的选区数据');
            if (window.showToast) {
                window.showToast('请先选中要添加批注的文字', 'error');
            } else {
                alert('请先选中要添加批注的文字');
            }
            return;
        }
        
        // 验证选区是否仍然有效
        try {
            const docContent = document.querySelector('.doc-content');
            if (!docContent) {
                console.error('[handlePopupAction] .doc-content 不存在');
                return;
            }
            
            const range = selectionToUse.range;
            const commonAncestor = range.commonAncestorContainer;
            const ancestorElement = commonAncestor.nodeType === Node.TEXT_NODE 
                ? commonAncestor.parentElement 
                : commonAncestor;
            
            if (!ancestorElement || !docContent.contains(ancestorElement)) {
                console.error('[handlePopupAction] 选区已失效，不在 .doc-content 内');
                if (window.showToast) {
                    window.showToast('选区已失效，请重新选择文字', 'error');
                } else {
                    alert('选区已失效，请重新选择文字');
                }
                // 清除无效的选区
                state.currentSelection = null;
                window.lastSelection = null;
                return;
            }
        } catch (err) {
            console.error('[handlePopupAction] 验证选区失败:', err);
            if (window.showToast) {
                window.showToast('选区验证失败，请重新选择文字', 'error');
            } else {
                alert('选区验证失败，请重新选择文字');
            }
            return;
        }
        
        switch (action) {
            case 'bold':
                applyHighlight('bold');
                break;
            case 'blue':
                applyHighlight('blue');
                break;
            case 'red':
                applyHighlight('red');
                break;
            case 'comment':
                showCommentDialog();
                break;
            case 'remove':
                // 文本点击删除批注功能已禁用：仅清除选择，不再通过正文删除批注
                try {
                    window.getSelection().removeAllRanges();
                } catch (err) {
                    // 忽略错误
                }
                break;
            case 'copy':
                // 复制选中文字
                try {
                    const textToCopy = selectionToUse.text;
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(textToCopy).then(() => {
                            if (window.showToast) {
                                window.showToast('已复制到剪贴板', 'success');
                            }
                        }).catch(err => {
                            console.error('复制失败:', err);
                            // 降级方案：使用传统方法
                            fallbackCopyText(textToCopy);
                        });
                    } else {
                        // 降级方案：使用传统方法
                        fallbackCopyText(textToCopy);
                    }
                } catch (err) {
                    console.error('[handlePopupAction] 复制失败:', err);
                    if (window.showToast) {
                        window.showToast('复制失败，请重试', 'error');
                    }
                }
                // 清除选择
                try {
                    window.getSelection().removeAllRanges();
                } catch (err) {
                    // 忽略错误
                }
                break;
        }
        
        // 隐藏浮窗，但不清除选择（保留选区快照）
        hidePopup();
        
        // 对于非批注操作，清除视觉选择
        if (action !== 'comment') {
            try {
                window.getSelection().removeAllRanges();
            } catch (err) {
                // 忽略错误
            }
        }
    }

    /**
     * 剥离区域内的所有 span 标签（去重逻辑）
     * 返回处理后的文档片段
     */
    function unwrapSpansInRange(range) {
        // 先克隆范围，避免修改原始范围
        const clonedRange = range.cloneRange();
        
        // 获取范围内的所有 span 元素
        const tempContainer = document.createElement('div');
        tempContainer.appendChild(clonedRange.extractContents());
        
        // 查找所有需要剥离的 span
        const spansToUnwrap = tempContainer.querySelectorAll('span.hl-blue, span.hl-red, span.hl-bold');
        
        // 剥离所有 span，保留文本内容
        spansToUnwrap.forEach(span => {
            const parent = span.parentNode;
            while (span.firstChild) {
                parent.insertBefore(span.firstChild, span);
            }
            parent.removeChild(span);
        });
        
        // 返回处理后的内容
        return tempContainer;
    }

    /**
     * 移除高亮标记（开关功能）
     * 完全移除 span 标签，不留下任何空的 span 或嵌套结构
     */
    function removeHighlight(element) {
        if (!element) return;
        
        const annotationId = element.getAttribute('data-annotation-id');
        
        // 如果元素不是 span 或者没有标注类，直接返回
        if (element.tagName !== 'SPAN' || 
            (!element.classList.contains('hl-blue') && 
             !element.classList.contains('hl-red') && 
             !element.classList.contains('hl-bold'))) {
            return;
        }
        
        const parent = element.parentNode;
        if (!parent) return;
        
        // 创建一个文档片段来存储所有子节点
        const fragment = document.createDocumentFragment();
        
        // 将 span 内的所有子节点（包括文本节点和其他元素）移出
        // 使用 firstChild 而不是 firstElementChild，确保包括文本节点
        while (element.firstChild) {
            fragment.appendChild(element.firstChild);
        }
        
        // 将文档片段插入到父节点中，替换 span
        parent.insertBefore(fragment, element);
        
        // 移除空的 span 元素
        parent.removeChild(element);
        
        // 规范化 DOM：合并相邻的文本节点，移除空的文本节点
        parent.normalize();
        
        // 递归检查父节点：如果父节点也是空的标注 span，也一并移除
        // 这可以处理嵌套 span 的情况
        if (parent.tagName === 'SPAN' && 
            (parent.classList.contains('hl-blue') || 
             parent.classList.contains('hl-red') || 
             parent.classList.contains('hl-bold'))) {
            // 如果父节点也是标注 span，递归移除
            removeHighlight(parent);
            return;
        }
        
        // 从批注列表中移除
        if (annotationId) {
            state.annotations = state.annotations.filter(a => a.id !== annotationId);
            
            // 从右侧栏移除批注项
            const commentItem = document.querySelector(`.annotation-item[data-annotation-id="${annotationId}"]`);
            if (commentItem) {
                commentItem.remove();
            }
            
            // 保存更新后的批注列表
            saveAllAnnotations();
        }
    }

    /**
     * 应用高亮标记（纯色模式：只改变字体颜色，支持开关功能）
     */
    function applyHighlight(type) {
        if (!state.currentSelection) return null;
        
        const range = state.currentSelection.range;
        const selectedText = state.currentSelection.text;
        
        // 检查选择是否跨越多个节点
        if (range.collapsed) return null;
        
        try {
            // 检查选中区域是否已有相同类型的标注
            const existing = checkExistingHighlight(range);
            if (existing && existing.type === type) {
                // 如果已有相同类型标注，移除它（开关功能）
                removeHighlight(existing.element);
                return null;
            }
            
            // 先剥离区域内已有的 span 标签（去重逻辑）
            const processedContainer = unwrapSpansInRange(range.cloneRange());
            
            // 创建新的 span 元素
            const span = document.createElement('span');
            
            if (type === 'bold') {
                span.className = 'hl-bold';
                span.style.fontWeight = 'bold';
                span.style.color = '#111827';
            } else if (type === 'blue') {
                span.className = 'hl-blue';
                span.style.color = '#2563eb';
            } else if (type === 'red') {
                span.className = 'hl-red';
                span.style.color = '#dc2626';
            }
            
            // 添加唯一 ID 用于关联批注
            const annotationId = 'ann_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            span.setAttribute('data-annotation-id', annotationId);
            
            // 将处理后的内容移动到 span 中
            while (processedContainer.firstChild) {
                span.appendChild(processedContainer.firstChild);
            }
            
            // 删除原内容并插入新的 span
            range.deleteContents();
            range.insertNode(span);
            
            // 保存批注信息
            saveAnnotation({
                id: annotationId,
                type: type,
                text: selectedText,
                comment: '',
                position: getElementPosition(span)
            });
            
            // 返回创建的 annotationId
            return annotationId;
            
        } catch (err) {
            console.error('应用高亮失败:', err);
            return null;
        }
    }

    /**
     * 显示批注输入弹窗
     */
    function showCommentDialog() {
        console.log('[showCommentDialog] 开始显示批注输入弹窗');
        
        if (!state.commentDialog) {
            console.error('[showCommentDialog] 批注对话框不存在');
            return;
        }
        
        // 优先使用 state.currentSelection，如果为空则从全局快照恢复
        let selectionToUse = state.currentSelection;
        console.log('[showCommentDialog] state.currentSelection:', state.currentSelection);
        console.log('[showCommentDialog] window.lastSelection:', window.lastSelection);
        
        if (!selectionToUse && window.lastSelection) {
            // 从快照恢复选区
            try {
                const selection = window.getSelection();
                selection.removeAllRanges();
                const clonedRange = window.lastSelection.range.cloneRange();
                selection.addRange(clonedRange);
                
                // 更新 state.currentSelection
                selectionToUse = {
                    range: clonedRange,
                    text: window.lastSelection.text,
                    timestamp: window.lastSelection.timestamp
                };
                state.currentSelection = selectionToUse;
                console.log('[showCommentDialog] 从 window.lastSelection 恢复选区');
                
                // 确保选区在视口中可见（滚动到选区位置）
                try {
                    const rect = clonedRange.getBoundingClientRect();
                    if (rect.top < 0 || rect.bottom > window.innerHeight) {
                        clonedRange.getBoundingClientRect(); // 触发重新计算
                        clonedRange.startContainer.parentElement?.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'center' 
                        });
                    }
                } catch (err) {
                    console.warn('[showCommentDialog] 滚动到选区失败:', err);
                }
            } catch (err) {
                console.error('[showCommentDialog] 恢复选区失败:', err);
                // 如果恢复失败，直接使用快照数据（不恢复视觉选择）
                try {
                    selectionToUse = {
                        range: window.lastSelection.range.cloneRange(),
                        text: window.lastSelection.text,
                        timestamp: window.lastSelection.timestamp
                    };
                    state.currentSelection = selectionToUse;
                } catch (cloneErr) {
                    console.error('[showCommentDialog] 克隆选区失败:', cloneErr);
                }
            }
        }
        
        if (!selectionToUse) {
            console.error('[showCommentDialog] 没有可用的选区数据');
            if (window.showToast) {
                window.showToast('请先选中要添加批注的文字', 'error');
            } else {
                alert('请先选中要添加批注的文字');
            }
            return;
        }
        
        // 验证选区是否仍然有效
        try {
            const docContent = document.querySelector('.doc-content');
            if (!docContent) {
                console.error('[showCommentDialog] .doc-content 不存在');
                if (window.showToast) {
                    window.showToast('无法找到正文区域', 'error');
                }
                return;
            }
            
            const range = selectionToUse.range;
            const commonAncestor = range.commonAncestorContainer;
            const ancestorElement = commonAncestor.nodeType === Node.TEXT_NODE 
                ? commonAncestor.parentElement 
                : commonAncestor;
            
            if (!ancestorElement || !docContent.contains(ancestorElement)) {
                console.error('[showCommentDialog] 选区已失效，不在 .doc-content 内');
                console.error('[showCommentDialog] ancestorElement:', ancestorElement);
                if (window.showToast) {
                    window.showToast('选区已失效，请重新选择文字', 'error');
                } else {
                    alert('选区已失效，请重新选择文字');
                }
                // 清除无效的选区
                state.currentSelection = null;
                window.lastSelection = null;
                return;
            }
            
            console.log('[showCommentDialog] 选区验证通过');
        } catch (err) {
            console.error('[showCommentDialog] 验证选区失败:', err);
            if (window.showToast) {
                window.showToast('选区验证失败，请重新选择文字', 'error');
            } else {
                alert('选区验证失败，请重新选择文字');
            }
            return;
        }
        
        const dialog = state.commentDialog;
        const textarea = dialog.querySelector('.comment-dialog-textarea');
        
        // 弹窗使用居中布局，不需要手动设置位置
        dialog.style.display = 'flex';
        
        // 清空并聚焦输入框
        textarea.value = '';
        // 延迟聚焦，确保选区保持可见
        setTimeout(() => {
            textarea.focus();
            // 再次尝试保持选区可见（某些浏览器在聚焦输入框时会清除选择）
            if (window.lastSelection && state.currentSelection) {
                try {
                    const selection = window.getSelection();
                    if (selection.rangeCount === 0) {
                        selection.addRange(state.currentSelection.range.cloneRange());
                    }
                } catch (err) {
                    // 忽略错误，快照数据已保存
                }
            }
        }, 100);
    }

    /**
     * 隐藏批注输入弹窗
     */
    function hideCommentDialog() {
        if (state.commentDialog) {
            state.commentDialog.style.display = 'none';
        }
    }

    /**
     * 处理批注提交（使用选区快照，不依赖 getSelection）
     */
    function handleCommentSubmit() {
        console.log('[handleCommentSubmit] 开始处理批注提交');
        
        if (!state.commentDialog) {
            console.error('[handleCommentSubmit] 批注对话框不存在');
            return;
        }
        
        // 优先使用 state.currentSelection，如果为空则从全局快照恢复
        let selectionToUse = state.currentSelection;
        if (!selectionToUse && window.lastSelection) {
            try {
                selectionToUse = {
                    range: window.lastSelection.range.cloneRange(),
                    text: window.lastSelection.text,
                    timestamp: window.lastSelection.timestamp
                };
                state.currentSelection = selectionToUse;
                console.log('[handleCommentSubmit] 从 window.lastSelection 恢复选区');
            } catch (err) {
                console.error('[handleCommentSubmit] 恢复选区失败:', err);
            }
        }
        
        if (!selectionToUse) {
            console.error('[handleCommentSubmit] 当前选择为空，无法添加批注');
            if (window.showToast) {
                window.showToast('请先选中要添加批注的文字', 'error');
            } else {
                alert('请先选中要添加批注的文字');
            }
            return;
        }
        
        // 验证选区是否仍然有效
        try {
            const docContent = document.querySelector('.doc-content');
            if (!docContent) {
                console.error('[handleCommentSubmit] .doc-content 不存在');
                if (window.showToast) {
                    window.showToast('无法找到正文区域', 'error');
                }
                return;
            }
            
            const range = selectionToUse.range;
            const commonAncestor = range.commonAncestorContainer;
            const ancestorElement = commonAncestor.nodeType === Node.TEXT_NODE 
                ? commonAncestor.parentElement 
                : commonAncestor;
            
            if (!ancestorElement || !docContent.contains(ancestorElement)) {
                console.error('[handleCommentSubmit] 选区已失效，不在 .doc-content 内');
                if (window.showToast) {
                    window.showToast('选区已失效，请重新选择文字', 'error');
                } else {
                    alert('选区已失效，请重新选择文字');
                }
                // 清除无效的选区
                state.currentSelection = null;
                window.lastSelection = null;
                return;
            }
            
            console.log('[handleCommentSubmit] 选区验证通过');
        } catch (err) {
            console.error('[handleCommentSubmit] 验证选区失败:', err);
            if (window.showToast) {
                window.showToast('选区验证失败，请重新选择文字', 'error');
            } else {
                alert('选区验证失败，请重新选择文字');
            }
            return;
        }
        
        const textarea = state.commentDialog.querySelector('.comment-dialog-textarea');
        const comment = textarea.value.trim();
        const selectedText = selectionToUse.text;
        
        console.log('[handleCommentSubmit] 准备提交批注，comment 长度:', comment.length, 'comment 内容:', comment?.substring(0, 50));
        
        // 保存当前选择信息（深拷贝），因为 applyHighlight 可能会影响 DOM
        const savedSelection = {
            range: selectionToUse.range.cloneRange(),
            text: selectedText
        };
        
        // 临时更新 state.currentSelection，供 applyHighlight 使用
        state.currentSelection = savedSelection;
        
        // 先应用蓝色高亮，获取创建的 annotationId
        const annotationId = applyHighlight('blue');
        
        if (!annotationId) {
            console.error('[handleCommentSubmit] 创建高亮失败，未返回 annotationId');
            if (window.showToast) {
                window.showToast('创建批注失败，请重试', 'error');
            } else {
                alert('创建批注失败，请重试');
            }
            hideCommentDialog();
            return;
        }
        
        console.log('[handleCommentSubmit] 创建的高亮 annotationId:', annotationId);
        
        // 等待 DOM 更新后添加批注
        setTimeout(() => {
            // 验证 span 是否存在
            const span = document.querySelector(`.doc-content span[data-annotation-id="${annotationId}"]`);
            
            if (span) {
                console.log('[handleCommentSubmit] 找到新创建的标注元素，ID:', annotationId);
                console.log('[handleCommentSubmit] 准备更新批注，comment:', comment?.substring(0, 50));
                
                // 更新批注信息
                updateAnnotationComment(annotationId, comment);
                
                // 立即刷新批注列表（saveAnnotation 是同步更新 state.annotations 的）
                // 但为了确保 DOM 更新完成，稍微延迟一下
                setTimeout(() => {
                    console.log('[handleCommentSubmit] 刷新批注列表，当前批注数量:', state.annotations.length);
                    console.log('[handleCommentSubmit] 所有批注:', state.annotations.map(a => ({ id: a.id, text: a.text?.substring(0, 20), hasComment: !!a.comment })));
                    const commentsWithText = state.annotations.filter(ann => ann.comment && ann.comment.trim());
                    console.log('[handleCommentSubmit] 有批注内容的批注数量:', commentsWithText.length);
                    console.log('[handleCommentSubmit] 有批注内容的批注:', commentsWithText.map(a => ({ id: a.id, text: a.text?.substring(0, 20), comment: a.comment?.substring(0, 20) })));
                    restoreComments();
                }, 100);
            } else {
                console.error('[handleCommentSubmit] 未找到新创建的标注元素，annotationId:', annotationId);
                console.error('[handleCommentSubmit] 当前所有 span:', Array.from(document.querySelectorAll('.doc-content span[data-annotation-id]')).map(s => s.getAttribute('data-annotation-id')));
                if (window.showToast) {
                    window.showToast('创建批注失败，请重试', 'error');
                } else {
                    alert('创建批注失败，请重试');
                }
            }
            
            // 关闭弹窗并清除选择
            hideCommentDialog();
            
            // 清除视觉选择
            try {
                const selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    selection.removeAllRanges();
                }
            } catch (err) {
                console.warn('[handleCommentSubmit] 清除视觉选择失败:', err);
            }
            
            // 清除选区快照（允许用户继续添加新的批注）
            state.currentSelection = null;
            window.lastSelection = null;
            console.log('[handleCommentSubmit] 批注提交完成，选区已清除，可以继续添加新批注');
        }, 100);
    }

    /**
     * 获取元素位置信息（用于定位批注）
     */
    function getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        const docContent = document.querySelector('.doc-content');
        const contentRect = docContent.getBoundingClientRect();
        
        return {
            top: rect.top - contentRect.top + window.scrollY,
            left: rect.left - contentRect.left + window.scrollX
        };
    }

    /**
     * 保存批注到后端（防抖处理，避免频繁请求）
     */
    let saveAnnotationTimeout = null;
    
    function saveAnnotation(annotation) {
        console.log('[saveAnnotation] 保存批注:', annotation.id, annotation.text?.substring(0, 20) + '...');
        
        // 检查是否已存在相同 ID 的批注
        const index = state.annotations.findIndex(a => a.id === annotation.id);
        if (index >= 0) {
            console.log('[saveAnnotation] 更新已存在的批注，索引:', index);
            state.annotations[index] = annotation;
        } else {
            console.log('[saveAnnotation] 添加新批注，当前总数:', state.annotations.length);
            state.annotations.push(annotation);
            console.log('[saveAnnotation] 添加后总数:', state.annotations.length);
        }
        
        // 不再保存整个文档的 HTML，只保存批注数据本身
        // 这样可以避免正文内容被锁定，确保正文和批注使用统一的数据源
        
        // 防抖：延迟保存，避免频繁请求
        clearTimeout(saveAnnotationTimeout);
        saveAnnotationTimeout = setTimeout(() => {
            console.log('[saveAnnotation] 防抖保存，当前批注总数:', state.annotations.length);
            saveAllAnnotations();
        }, 300);
    }
    
    /**
     * 保存所有批注到后端
     * 不再保存整个 HTML 内容，只保存批注数据本身
     */
    function saveAllAnnotations() {
        console.log('[saveAllAnnotations] 开始保存所有批注，总数:', state.annotations.length);
        console.log('[saveAllAnnotations] 批注详情:', state.annotations.map(a => ({ 
            id: a.id, 
            text: a.text?.substring(0, 20), 
            hasComment: !!(a.comment && a.comment.trim())
        })));
        
        // 清理批注数据：移除 htmlContent 字段（不再需要）
        const cleanedAnnotations = state.annotations.map(ann => {
            const { htmlContent, ...rest } = ann;
            return rest;
        });
        
        // 异步保存到后端，返回 Promise
        console.log('[saveAllAnnotations] 发送到后端，批注数量:', cleanedAnnotations.length);
        return fetch(`/api/note/${state.noteId}/annotations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                annotations: cleanedAnnotations
            })
        })
        .then(res => {
            if (!res.ok) {
                throw new Error('保存失败');
            }
            return res.json();
        })
        .then(data => {
            console.log('[saveAllAnnotations] 保存成功');
            return data;
        })
        .catch(err => {
            console.error('保存批注失败:', err);
            throw err;
        });
    }

    /**
     * 更新批注的评论内容
     */
    function updateAnnotationComment(annotationId, comment) {
        console.log('[updateAnnotationComment] 开始更新批注，ID:', annotationId);
        console.log('[updateAnnotationComment] comment 参数类型:', typeof comment, '长度:', comment?.length, '内容:', comment?.substring(0, 50));
        console.log('[updateAnnotationComment] 当前 state.annotations 数量:', state.annotations.length);
        
        const annotation = state.annotations.find(a => a.id === annotationId);
        if (annotation) {
            console.log('[updateAnnotationComment] 找到批注，更新前:', { 
                id: annotation.id, 
                text: annotation.text?.substring(0, 30), 
                hasComment: !!annotation.comment,
                commentLength: annotation.comment?.length || 0
            });
            
            // 确保 comment 是字符串
            const commentToSave = typeof comment === 'string' ? comment : String(comment || '');
            annotation.comment = commentToSave;
            
            console.log('[updateAnnotationComment] 更新后:', { 
                id: annotation.id, 
                text: annotation.text?.substring(0, 30), 
                comment: annotation.comment?.substring(0, 50),
                commentLength: annotation.comment?.length || 0
            });
            
            console.log('[updateAnnotationComment] 当前 state.annotations 详情:', state.annotations.map(a => ({ 
                id: a.id, 
                text: a.text?.substring(0, 20), 
                hasComment: !!(a.comment && a.comment.trim()),
                commentLength: a.comment?.length || 0
            })));
            
            saveAnnotation(annotation);
            console.log('[updateAnnotationComment] 保存后 state.annotations 数量:', state.annotations.length);
        } else {
            console.error('[updateAnnotationComment] 未找到批注:', annotationId);
            console.error('[updateAnnotationComment] 当前批注列表:', state.annotations.map(a => ({ id: a.id, text: a.text?.substring(0, 20) })));
        }
    }

    /**
     * 根据批注文本重新应用高亮标记
     * 不再恢复整个 HTML，而是基于当前页面内容重新应用标记
     */
    function reapplyHighlights() {
        if (!state.annotations || state.annotations.length === 0) {
            return;
        }
        
        const docContent = document.querySelector('.doc-content');
        if (!docContent) {
            console.warn('[reapplyHighlights] .doc-content 不存在');
            return;
        }
        
        console.log('[reapplyHighlights] 开始重新应用高亮标记，批注数量:', state.annotations.length);
        
        // 转义正则表达式特殊字符
        function escapeRegex(str) {
            return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }
        
        // 查找文本在 DOM 中的位置（简化版本：使用更可靠的文本匹配）
        function findTextInDOM(element, searchText) {
            const normalizedSearchText = searchText.trim().replace(/\s+/g, ' ');
            const fullText = element.textContent || '';
            const normalizedFullText = fullText.replace(/\s+/g, ' ');
            
            // 如果文本不存在，返回 null
            if (!normalizedFullText.includes(normalizedSearchText)) {
                return null;
            }
            
            // 使用 Range API 查找文本（如果浏览器支持）
            // 否则使用 TreeWalker 手动查找
            try {
                // 尝试使用 Range.findText（非标准，但某些浏览器支持）
                const range = document.createRange();
                range.selectNodeContents(element);
                
                // 使用更简单的方法：遍历所有文本节点，累积文本，找到匹配位置
                const walker = document.createTreeWalker(
                    element,
                    NodeFilter.SHOW_TEXT,
                    null
                );
                
                let textNodes = [];
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.trim()) {
                        textNodes.push(node);
                    }
                }
                
                // 累积文本并查找匹配位置
                let accumulatedNormalized = '';
                let startNode = null;
                let startOffset = 0;
                let endNode = null;
                let endOffset = 0;
                
                for (let i = 0; i < textNodes.length; i++) {
                    const textNode = textNodes[i];
                    const nodeText = textNode.textContent;
                    const normalizedNodeText = nodeText.replace(/\s+/g, ' ');
                    
                    const beforeAccumulated = accumulatedNormalized;
                    accumulatedNormalized += normalizedNodeText;
                    
                    // 检查是否包含目标文本
                    const matchIndex = accumulatedNormalized.indexOf(normalizedSearchText);
                    if (matchIndex !== -1) {
                        // 找到匹配，计算在原始文本中的位置
                        // 计算匹配开始位置在哪个节点
                        let pos = 0;
                        for (let j = 0; j <= i; j++) {
                            const currentText = textNodes[j].textContent;
                            const normalizedCurrentText = currentText.replace(/\s+/g, ' ');
                            const normalizedBefore = pos === 0 ? '' : accumulatedNormalized.substring(0, pos).replace(/\s+/g, ' ');
                            const normalizedAfter = normalizedBefore + normalizedCurrentText;
                            
                            if (matchIndex < normalizedAfter.length) {
                                // 匹配开始在这个节点内
                                const offsetInNormalized = matchIndex - normalizedBefore.length;
                                // 将规范化偏移量转换为原始偏移量（简化：假设空格数量相同）
                                startNode = textNodes[j];
                                startOffset = Math.min(offsetInNormalized, currentText.length);
                                break;
                            }
                            pos += normalizedCurrentText.length;
                        }
                        
                        // 计算匹配结束位置
                        const endMatchIndex = matchIndex + normalizedSearchText.length;
                        pos = 0;
                        for (let j = 0; j <= i; j++) {
                            const currentText = textNodes[j].textContent;
                            const normalizedCurrentText = currentText.replace(/\s+/g, ' ');
                            const normalizedBefore = pos === 0 ? '' : accumulatedNormalized.substring(0, pos).replace(/\s+/g, ' ');
                            const normalizedAfter = normalizedBefore + normalizedCurrentText;
                            
                            if (endMatchIndex <= normalizedAfter.length) {
                                const offsetInNormalized = endMatchIndex - normalizedBefore.length;
                                endNode = textNodes[j];
                                endOffset = Math.min(offsetInNormalized, currentText.length);
                                break;
                            }
                            pos += normalizedCurrentText.length;
                        }
                        
                        if (startNode && endNode) {
                            return { startNode, startOffset, endNode, endOffset };
                        }
                        break;
                    }
                }
            } catch (err) {
                console.error('[findTextInDOM] 查找文本失败:', err);
            }
            
            return null;
        }
        
        // 为每个批注重新应用高亮
        state.annotations.forEach(annotation => {
            if (!annotation.text || !annotation.text.trim() || !annotation.type) {
                return; // 跳过无效批注
            }
            
            // 检查是否已经存在该批注的高亮标记
            const existingSpan = docContent.querySelector(`span[data-annotation-id="${annotation.id}"]`);
            if (existingSpan) {
                console.log(`[reapplyHighlights] 批注 ${annotation.id} 已存在，跳过`);
                return; // 已经存在，跳过
            }
            
            // 查找文本位置
            const textPosition = findTextInDOM(docContent, annotation.text);
            if (!textPosition) {
                console.warn(`[reapplyHighlights] 批注 ${annotation.id} 的文本未找到:`, annotation.text.substring(0, 30));
                return; // 文本不存在，跳过
            }
            
            try {
                // 创建 Range
                const range = document.createRange();
                range.setStart(textPosition.startNode, textPosition.startOffset);
                range.setEnd(textPosition.endNode, textPosition.endOffset);
                
                // 检查是否已有相同类型的标注
                const existing = checkExistingHighlight(range);
                if (existing && existing.type === annotation.type) {
                    // 如果已有相同类型标注，跳过
                    return;
                }
                
                // 创建高亮 span
                const span = document.createElement('span');
                span.setAttribute('data-annotation-id', annotation.id);
                
                if (annotation.type === 'bold') {
                    span.className = 'hl-bold';
                    span.style.fontWeight = 'bold';
                    span.style.color = '#111827';
                } else if (annotation.type === 'blue') {
                    span.className = 'hl-blue';
                    span.style.color = '#2563eb';
                } else if (annotation.type === 'red') {
                    span.className = 'hl-red';
                    span.style.color = '#dc2626';
                }
                
                // 提取内容并包裹
                const contents = range.extractContents();
                span.appendChild(contents);
                range.insertNode(span);
                
                console.log(`[reapplyHighlights] 成功重新应用批注 ${annotation.id}`);
            } catch (err) {
                console.error(`[reapplyHighlights] 重新应用批注 ${annotation.id} 失败:`, err);
            }
        });
        
        console.log('[reapplyHighlights] 重新应用高亮标记完成');
    }

    /**
     * 加载已有批注
     */
    function loadAnnotations() {
        fetch(`/api/note/${state.noteId}/annotations`)
            .then(res => res.json())
            .then(data => {
                state.annotations = data.annotations || [];
                
                console.log('[loadAnnotations] 加载批注完成，数量:', state.annotations.length);
                
                // 不再恢复整个 HTML，而是重新应用高亮标记
                // 这样可以确保正文内容始终是最新的，不会被旧的 HTML 覆盖
                if (state.annotations.length > 0) {
                    // 延迟执行，确保页面内容已完全加载
                    setTimeout(() => {
                        reapplyHighlights();
                            // 触发自定义事件，通知大纲需要重新生成
                            window.dispatchEvent(new CustomEvent('annotationsLoaded'));
                    }, 100);
                }
                
                // 恢复右侧批注列表
                restoreComments();
            })
            .catch(err => {
                console.error('加载批注失败:', err);
            });
    }


    /**
     * 恢复右侧批注列表
     */
    function restoreComments() {
        console.log('[restoreComments] 开始恢复批注列表');
        console.log('[restoreComments] state.annotations 总数:', state.annotations.length);
        console.log('[restoreComments] state.annotations 详情:', state.annotations.map(a => ({ 
            id: a.id, 
            text: a.text?.substring(0, 30), 
            comment: a.comment?.substring(0, 30),
            hasComment: !!(a.comment && a.comment.trim())
        })));
        
        const commentsContainer = document.getElementById('annotations-list');
        const emptyTip = document.getElementById('annotations-empty');
        if (!commentsContainer) {
            console.error('[restoreComments] 批注容器不存在');
            return;
        }
        
        // 清空容器
        commentsContainer.innerHTML = '';
        console.log('[restoreComments] 已清空批注容器');
        
        // 过滤出有批注内容的批注
        const commentsWithText = state.annotations.filter(ann => ann.comment && ann.comment.trim());
        console.log('[restoreComments] 有批注内容的批注数量:', commentsWithText.length);
        console.log('[restoreComments] 有批注内容的批注详情:', commentsWithText.map(a => ({ 
            id: a.id, 
            text: a.text?.substring(0, 30), 
            comment: a.comment?.substring(0, 30)
        })));
        
        if (commentsWithText.length === 0) {
            if (emptyTip) emptyTip.style.display = 'block';
            console.log('[restoreComments] 没有批注，显示空提示');
        } else {
            if (emptyTip) emptyTip.style.display = 'none';
            // 按时间顺序排序（后添加的在前）
            const sortedComments = commentsWithText.slice().reverse();
            console.log('[restoreComments] 开始添加批注，共', sortedComments.length, '个');
            sortedComments.forEach((ann, index) => {
                console.log(`[restoreComments] 添加批注 ${index + 1}/${sortedComments.length}:`, {
                    id: ann.id,
                    text: ann.text?.substring(0, 30) + '...',
                    comment: ann.comment?.substring(0, 30) + '...'
                });
                addCommentToSidebar(ann.id, ann.text, ann.comment);
            });
            console.log('[restoreComments] 批注列表恢复完成，容器中元素数量:', commentsContainer.children.length);
        }
    }

    /**
     * 在右侧批注区添加批注项
     */
    function addCommentToSidebar(annotationId, text, comment) {
        console.log('[addCommentToSidebar] 开始添加批注到侧边栏，ID:', annotationId, 'text:', text?.substring(0, 20), 'comment:', comment?.substring(0, 20));
        const commentsContainer = document.getElementById('annotations-list');
        const emptyTip = document.getElementById('annotations-empty');
        if (!commentsContainer) {
            console.error('[addCommentToSidebar] 批注容器不存在');
            return;
        }
        
        // 隐藏空提示
        if (emptyTip) emptyTip.style.display = 'none';
        
        // 检查是否已存在
        const existing = commentsContainer.querySelector(`[data-annotation-id="${annotationId}"]`);
        if (existing) {
            console.log('[addCommentToSidebar] 发现已存在的批注，移除旧项');
            existing.remove();
        }
        
        const commentItem = document.createElement('div');
        commentItem.className = 'annotation-item';
        commentItem.setAttribute('data-annotation-id', annotationId);
        
        // 转义 HTML，保留换行
        const escapedComment = escapeHtml(comment).replace(/\n/g, '<br>');
        const escapedText = escapeHtml(text);
        
        commentItem.innerHTML = `
            <div class="annotation-quote">${escapedText}</div>
            <div class="annotation-comment">${escapedComment}</div>
            <div class="annotation-actions">
                <button class="annotation-edit-btn" data-annotation-id="${annotationId}" title="Edit">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 20h9"></path>
                        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                    </svg>
                    Edit
                </button>
                <button class="annotation-delete" aria-label="Delete annotation">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="m19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        <line x1="10" y1="11" x2="10" y2="17"></line>
                        <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                </button>
            </div>
        `;
        
        // 绑定点击事件：点击批注卡片时，左侧原文闪烁
        commentItem.addEventListener('click', function(e) {
            // 如果点击的是操作按钮，不触发闪烁
            if (e.target.closest('.annotation-actions')) return;
            
            const span = document.querySelector(`span[data-annotation-id="${annotationId}"]`);
            if (span) {
                // 添加闪烁动画类
                span.classList.add('annotation-pulse');
                
                // 滚动到对应位置
                span.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // 移除动画类
                setTimeout(() => {
                    span.classList.remove('annotation-pulse');
                }, 2000);
            }
        });
        
        // 绑定修改事件
        const editBtn = commentItem.querySelector('.annotation-edit-btn');
        editBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const annotation = state.annotations.find(a => a.id === annotationId);
            if (annotation) {
                enterAnnotationEditMode(commentItem, annotation);
            }
        });
        
        // 绑定删除事件
        const deleteBtn = commentItem.querySelector('.annotation-delete');
        deleteBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            deleteAnnotation(annotationId);
        });
        
        commentsContainer.appendChild(commentItem);
        console.log('[addCommentToSidebar] 批注已添加到侧边栏，当前容器中元素数量:', commentsContainer.children.length);
    }

    /**
     * 删除批注（使用统一的保存函数）
     */
    async function deleteAnnotation(annotationId) {
        const confirmed = await showConfirmDialog(
            'Are you sure you want to delete this annotation?',
            'Delete Annotation',
            {
                confirmText: 'OK',
                cancelText: 'Cancel'
            }
        );
        
        if (!confirmed) return;
        
        // 从数组中移除
        state.annotations = state.annotations.filter(a => a.id !== annotationId);
        
        // 从页面中移除高亮标记
        const span = document.querySelector(`span[data-annotation-id="${annotationId}"]`);
        if (span) {
            const parent = span.parentNode;
            const textNode = document.createTextNode(span.textContent);
            parent.replaceChild(textNode, span);
            parent.normalize();
        }
        
        // 从右侧栏移除
        const commentItem = document.querySelector(`.annotation-item[data-annotation-id="${annotationId}"]`);
        if (commentItem) {
            commentItem.remove();
        }
        
        // 检查是否还有批注，如果没有则显示空提示
        const commentsContainer = document.getElementById('annotations-list');
        const emptyTip = document.getElementById('annotations-empty');
        if (commentsContainer && commentsContainer.children.length === 0 && emptyTip) {
            emptyTip.style.display = 'block';
        }
        
        // 使用统一的保存函数
        saveAllAnnotations();
    }

    /**
     * HTML 转义
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 进入批注编辑模式：将批注内容切换为 textarea 编辑模式
     */
    function enterAnnotationEditMode(commentItem, annotation) {
        const commentDiv = commentItem.querySelector('.annotation-comment');
        if (!commentDiv) return;
        
        // 保存原始内容
        const originalComment = annotation.comment || '';
        
        // 创建 textarea
        const textarea = document.createElement('textarea');
        textarea.className = 'annotation-edit-textarea';
        textarea.value = originalComment;
        textarea.rows = Math.max(3, Math.ceil(originalComment.split('\n').length));
        
        // 创建编辑模式的操作按钮容器
        const editActions = document.createElement('div');
        editActions.className = 'annotation-edit-actions';
        editActions.innerHTML = `
            <button class="annotation-save-btn" data-annotation-id="${annotation.id}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Save
            </button>
            <button class="annotation-cancel-btn" data-annotation-id="${annotation.id}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Cancel
            </button>
        `;
        
        // 隐藏原有的内容和操作栏
        const actionsDiv = commentItem.querySelector('.annotation-actions');
        if (actionsDiv) {
            actionsDiv.style.display = 'none';
        }
        
        // 替换内容为 textarea
        commentDiv.style.display = 'none';
        commentItem.insertBefore(textarea, commentDiv);
        commentItem.appendChild(editActions);
        
        // 聚焦 textarea
        setTimeout(() => {
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }, 10);
        
        // 绑定保存事件
        const saveBtn = editActions.querySelector('.annotation-save-btn');
        saveBtn.addEventListener('click', function() {
            saveAnnotationComment(commentItem, annotation.id, textarea.value);
        });
        
        // 绑定取消事件
        const cancelBtn = editActions.querySelector('.annotation-cancel-btn');
        cancelBtn.addEventListener('click', function() {
            cancelAnnotationEdit(commentItem, originalComment, annotation);
        });
        
        // 支持 ESC 键取消
        const handleEsc = function(e) {
            if (e.key === 'Escape') {
                cancelAnnotationEdit(commentItem, originalComment, annotation);
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }
    
    /**
     * 保存批注修改
     */
    function saveAnnotationComment(commentItem, annotationId, newComment) {
        if (!newComment.trim()) {
            if (window.showToast) {
                window.showToast('批注内容不能为空', 'error');
            } else {
                alert('批注内容不能为空');
            }
            return;
        }
        
        // 更新批注内容
        const annotation = state.annotations.find(a => a.id === annotationId);
        if (!annotation) {
            if (window.showToast) {
                window.showToast('批注不存在', 'error');
            }
            return;
        }
        
        annotation.comment = newComment.trim();
        
        // 保存到后端
        saveAllAnnotations()
            .then(() => {
                // 更新成功，刷新整个批注列表（确保所有批注都显示）
                restoreComments();
                
                if (window.showToast) {
                    window.showToast('批注已更新', 'success');
                }
            })
            .catch(err => {
                console.error('保存批注失败:', err);
                if (window.showToast) {
                    window.showToast('保存失败，请重试', 'error');
                } else {
                    alert('保存失败，请重试');
                }
            });
    }
    
    /**
     * 取消批注编辑模式：恢复原始显示
     */
    function cancelAnnotationEdit(commentItem, originalComment, annotation) {
        const textarea = commentItem.querySelector('.annotation-edit-textarea');
        const editActions = commentItem.querySelector('.annotation-edit-actions');
        const commentDiv = commentItem.querySelector('.annotation-comment');
        const actionsDiv = commentItem.querySelector('.annotation-actions');
        
        // 移除编辑元素
        if (textarea) textarea.remove();
        if (editActions) editActions.remove();
        
        // 恢复显示
        if (commentDiv) commentDiv.style.display = '';
        if (actionsDiv) actionsDiv.style.display = '';
    }

    /**
     * 降级复制方案（兼容旧浏览器）
     */
    function fallbackCopyText(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                if (window.showToast) {
                    window.showToast('已复制到剪贴板', 'success');
                }
            } else {
                throw new Error('复制命令失败');
            }
        } catch (err) {
            console.error('降级复制方案失败:', err);
            if (window.showToast) {
                window.showToast('复制失败，请手动复制', 'error');
            }
        } finally {
            document.body.removeChild(textArea);
        }
    }

    /**
     * 初始化深度思考的块状化功能
     */
    function initGlobalThoughtBlocks() {
        const textarea = document.getElementById('global-thought-input');
        const submitBtn = document.getElementById('thought-submit-btn');
        const thoughtsList = document.getElementById('thoughts-list');
        
        if (!textarea || !submitBtn || !thoughtsList) return;
        
        // 提交按钮点击事件
        submitBtn.addEventListener('click', function() {
            const content = textarea.value.trim();
            if (!content) return;
            
            // 创建新的笔记块
            const thoughtData = {
                content: content,
                created_at: new Date().toISOString()
            };
            
            // 保存到后端
            fetch(`/api/note/${state.noteId}/global-thought`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(thoughtData)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // 添加到列表
                    addThoughtBlock(data.thought);
                    // 清空输入框
                    textarea.value = '';
                }
            })
            .catch(err => {
                console.error('保存深度思考失败:', err);
            });
        });
        
        // Enter + Ctrl 提交
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                submitBtn.click();
            }
        });
        
        // 加载已有笔记块
        loadThoughtBlocks();
    }
    
    /**
     * 加载所有笔记块
     */
    function loadThoughtBlocks() {
        fetch(`/api/note/${state.noteId}/global-thought`)
            .then(res => res.json())
            .then(data => {
                const thoughtsList = document.getElementById('thoughts-list');
                if (!thoughtsList) return;
                
                thoughtsList.innerHTML = '';
                
                if (data.thoughts && data.thoughts.length > 0) {
                    // 按创建时间倒序排列
                    const sortedThoughts = data.thoughts.sort((a, b) => 
                        new Date(b.created_at) - new Date(a.created_at)
                    );
                    
                    sortedThoughts.forEach(thought => {
                        addThoughtBlock(thought, false);
                    });
                }
            })
            .catch(err => {
                console.error('加载深度思考失败:', err);
            });
    }
    
    /**
     * 添加笔记块到列表
     */
    function addThoughtBlock(thought, prepend = true) {
        const thoughtsList = document.getElementById('thoughts-list');
        if (!thoughtsList) return;
        
        const block = document.createElement('div');
        block.className = 'thought-block';
        block.setAttribute('data-thought-id', thought.id);
        
        const createdDate = new Date(thought.created_at);
        const dateStr = createdDate.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // 将内容中的换行符转换为HTML实体，确保white-space: pre-wrap能够正确显示
        const contentHtml = escapeHtml(thought.content || '');
        
        block.innerHTML = `
            <div class="thought-block-content">${contentHtml}</div>
            <div class="thought-block-footer">
                <span>${dateStr}</span>
                <div class="thought-block-actions">
                    <button class="thought-block-btn thought-edit-btn" data-thought-id="${thought.id}" title="Edit">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 20h9"></path>
                            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                        </svg>
                        Edit
                    </button>
                    <button class="thought-block-btn thought-delete-btn" data-thought-id="${thought.id}" title="Delete">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="m19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Delete
                    </button>
                </div>
            </div>
        `;
        
        // 绑定删除事件
        const deleteBtn = block.querySelector('.thought-delete-btn');
        deleteBtn.addEventListener('click', async function() {
            const confirmed = await showConfirmDialog(
                'Are you sure you want to delete this note?',
                'Delete Note',
                {
                    confirmText: 'OK',
                    cancelText: 'Cancel'
                }
            );
            
            if (confirmed) {
                deleteThoughtBlock(thought.id);
            }
        });
        
        // 绑定编辑事件
        const editBtn = block.querySelector('.thought-edit-btn');
        editBtn.addEventListener('click', function() {
            enterEditMode(block, thought);
        });
        
        if (prepend) {
            thoughtsList.insertBefore(block, thoughtsList.firstChild);
        } else {
            thoughtsList.appendChild(block);
        }
    }
    
    /**
     * 删除笔记块
     */
    function deleteThoughtBlock(thoughtId) {
        fetch(`/api/note/${state.noteId}/global-thought`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: thoughtId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const block = document.querySelector(`.thought-block[data-thought-id="${thoughtId}"]`);
                if (block) {
                    block.remove();
                }
                if (window.showToast) {
                    window.showToast('笔记已删除', 'success');
                }
            }
        })
        .catch(err => {
            console.error('删除笔记块失败:', err);
            if (window.showToast) {
                window.showToast('删除失败，请重试', 'error');
            }
        });
    }
    
    /**
     * 进入编辑模式：将笔记块切换为 textarea 编辑模式
     */
    function enterEditMode(block, thought) {
        const contentDiv = block.querySelector('.thought-block-content');
        if (!contentDiv) return;
        
        // 保存原始内容
        const originalContent = thought.content;
        
        // 创建 textarea
        const textarea = document.createElement('textarea');
        textarea.className = 'thought-block-edit-textarea';
        textarea.value = originalContent;
        textarea.rows = Math.max(3, Math.ceil(originalContent.split('\n').length));
        
        // 创建编辑模式的操作按钮容器
        const editActions = document.createElement('div');
        editActions.className = 'thought-block-edit-actions';
        editActions.innerHTML = `
            <button class="thought-block-save-btn" data-thought-id="${thought.id}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Save
            </button>
            <button class="thought-block-cancel-btn" data-thought-id="${thought.id}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Cancel
            </button>
        `;
        
        // 隐藏原有的内容和操作栏
        const footer = block.querySelector('.thought-block-footer');
        if (footer) {
            footer.style.display = 'none';
        }
        
        // 替换内容为 textarea
        contentDiv.style.display = 'none';
        block.insertBefore(textarea, contentDiv);
        block.appendChild(editActions);
        
        // 聚焦 textarea
        setTimeout(() => {
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }, 10);
        
        // 绑定保存事件
        const saveBtn = editActions.querySelector('.thought-block-save-btn');
        saveBtn.addEventListener('click', function() {
            saveThoughtBlock(block, thought.id, textarea.value);
        });
        
        // 绑定取消事件
        const cancelBtn = editActions.querySelector('.thought-block-cancel-btn');
        cancelBtn.addEventListener('click', function() {
            cancelEditMode(block, originalContent, thought);
        });
        
        // 支持 ESC 键取消
        const handleEsc = function(e) {
            if (e.key === 'Escape') {
                cancelEditMode(block, originalContent, thought);
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }
    
    /**
     * 保存笔记块修改
     */
    function saveThoughtBlock(block, thoughtId, newContent) {
        if (!newContent.trim()) {
            if (window.showToast) {
                window.showToast('笔记内容不能为空', 'error');
            } else {
                alert('笔记内容不能为空');
            }
            return;
        }
        
        // 先移除编辑模式的元素（textarea和editActions），避免在保存过程中显示混乱
        const textarea = block.querySelector('.thought-block-edit-textarea');
        const editActions = block.querySelector('.thought-block-edit-actions');
        if (textarea) textarea.style.display = 'none';
        if (editActions) editActions.style.display = 'none';
        
        // 发送更新请求
        fetch(`/api/note/${state.noteId}/global-thought`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: thoughtId,
                content: newContent.trim()
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success && data.thought) {
                // 更新成功，重新渲染笔记块
                const thoughtsList = document.getElementById('thoughts-list');
                if (thoughtsList && block.parentNode === thoughtsList) {
                    const index = Array.from(thoughtsList.children).indexOf(block);
                    // 完全移除旧的block（包括所有编辑元素）
                    block.remove();
                    // 创建新的block并插入到相同位置
                    addThoughtBlock(data.thought, false);
                    const newBlock = thoughtsList.querySelector(`[data-thought-id="${thoughtId}"]`);
                    if (newBlock && index < thoughtsList.children.length) {
                        thoughtsList.insertBefore(newBlock, thoughtsList.children[index]);
                    } else if (newBlock && index >= thoughtsList.children.length) {
                        // 如果索引超出范围，追加到末尾
                        thoughtsList.appendChild(newBlock);
                    }
                } else {
                    // 如果不在列表中，直接更新
                    block.remove();
                    addThoughtBlock(data.thought, false);
                }
                
                if (window.showToast) {
                    window.showToast('笔记已更新', 'success');
                }
            } else {
                throw new Error('更新失败');
            }
        })
        .catch(err => {
            console.error('保存笔记块失败:', err);
            // 保存失败时，恢复编辑模式
            if (textarea) textarea.style.display = '';
            if (editActions) editActions.style.display = '';
            if (window.showToast) {
                window.showToast('保存失败，请重试', 'error');
            } else {
                alert('保存失败，请重试');
            }
        });
    }
    
    /**
     * 取消编辑模式：恢复原始显示
     */
    function cancelEditMode(block, originalContent, thought) {
        const textarea = block.querySelector('.thought-block-edit-textarea');
        const editActions = block.querySelector('.thought-block-edit-actions');
        const contentDiv = block.querySelector('.thought-block-content');
        const footer = block.querySelector('.thought-block-footer');
        
        // 移除编辑元素
        if (textarea) textarea.remove();
        if (editActions) editActions.remove();
        
        // 恢复显示
        if (contentDiv) contentDiv.style.display = '';
        if (footer) footer.style.display = '';
    }

    /**
     * 初始化大纲展开/收起功能
     */
    function initOutlineToggle() {
        const toggleButtons = document.querySelectorAll('.sidebar-section .sidebar-toggle');
        if (!toggleButtons || toggleButtons.length === 0) return;
        
        toggleButtons.forEach(function(toggleBtn) {
            // 检查是否已经添加过事件监听器（通过检查 data-initialized 属性）
            if (toggleBtn.dataset.initialized === 'true') return;
            
            toggleBtn.addEventListener('click', function(e) {
                e.stopPropagation(); // 防止事件冒泡
                const section = toggleBtn.closest('.sidebar-section');
                if (section) {
                    section.classList.toggle('collapsed');
                }
            });
            
            // 标记为已初始化
            toggleBtn.dataset.initialized = 'true';
        });
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
