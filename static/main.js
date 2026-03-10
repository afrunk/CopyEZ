/**
 * main.js - 目录树生成和交互逻辑
 * 功能：
 * 1. 自动提取文档标题生成目录树
 * 2. 实现目录点击平滑跳转（使用 scrollIntoView）
 * 3. 实现滚动时目录激活态高亮
 */

(function() {
  'use strict';
  
  let headingLinkMap = new Map();
  let observer = null;
  let activeLink = null;
  
  /**
   * 生成大纲导航
   */
  function generateOutline() {
    const docContent = document.querySelector('.doc-content');
    const outlineNav = document.getElementById('outline-nav');
    
    if (!docContent || !outlineNav) return;
    
    // 检查是否已经有后端生成的 TOC（通过检查 .toc 类或直接检查内容）
    const sidebarContent = outlineNav.closest('.sidebar-content');
    if (sidebarContent && sidebarContent.querySelector('.toc')) {
      // 如果已经有后端生成的 TOC，不执行 JavaScript 生成逻辑
      return;
    }
    
    // 清空现有大纲（仅在 JavaScript 生成模式下）
    outlineNav.innerHTML = '';
    headingLinkMap.clear();
    
    // 如果已有观察器，先断开
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    
    // 查找所有标题：优先查找有 heading class 的，然后查找所有 h1, h2, h3
    // 使用更宽松的选择器，确保能找到所有标题
    let headings = docContent.querySelectorAll('h1.heading, h2.heading, h3.heading, h1, h2, h3');
    
    // 过滤掉总标题（第一个 h1，通常是文档标题）
    // 如果第一个 h1 是 .doc-title 的子元素或者是文档的第一个 h1，则跳过
    const filteredHeadings = Array.from(headings).filter((heading, index) => {
      // 跳过文档标题（通常是第一个 h1 且没有 heading class）
      if (index === 0 && heading.tagName === 'H1' && !heading.classList.contains('heading')) {
        // 检查是否是文档标题（通常在 .doc-title 中）
        const docTitle = document.querySelector('.doc-title');
        if (docTitle && (docTitle === heading || docTitle.contains(heading))) {
          return false;
        }
      }
      return true;
    });
    
    if (filteredHeadings.length === 0) {
      outlineNav.innerHTML = '<p class="sidebar-tip">暂无标题</p>';
      return;
    }
    
    headings = filteredHeadings;
    
    const outlineList = document.createElement('ul');
    outlineList.className = 'outline-list';
    
    headings.forEach((heading, index) => {
      // 直接从标签名获取级别（h1 => 1, h2 => 2, h3 => 3）
      const tagName = heading.tagName.toLowerCase();
      const level = tagName === 'h1' ? 1 : tagName === 'h2' ? 2 : 3;
      
      // 获取标题的 ID（后端已生成：section-1, section-2, ...）
      // 确保 ID 存在，如果后端没有生成则使用索引作为后备
      const headingId = heading.id || `section-${index + 1}`;
      if (!heading.id) {
        heading.id = headingId;
      }
      
      const listItem = document.createElement('li');
      listItem.className = 'outline-item outline-level-' + level;
      
      const link = document.createElement('a');
      link.href = '#' + headingId;
      link.textContent = heading.textContent.trim();
      link.className = 'outline-link';
      link.setAttribute('data-target', headingId);
      
      listItem.appendChild(link);
      outlineList.appendChild(listItem);
      
      // 建立标题和链接的映射关系
      headingLinkMap.set(headingId, link);
    });
    
    outlineNav.appendChild(outlineList);
    
    // 使用事件委托监听大纲区域的所有点击事件
    outlineNav.addEventListener('click', function(e) {
      const link = e.target.closest('.outline-link');
      if (!link) return;
      
      e.preventDefault();
      const targetId = link.getAttribute('data-target') || link.getAttribute('href')?.substring(1);
      if (!targetId) return;
      
      // 支持 #section-1 格式和直接 ID 查找
      const targetHeading = document.querySelector('#' + targetId) || document.getElementById(targetId);
      if (targetHeading) {
        // 使用 scrollIntoView，CSS scroll-margin-top 会自动处理偏移量
        targetHeading.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
    
    // 使用 IntersectionObserver 实现激活态高亮
    const NAVBAR_OFFSET = 70; // 导航栏高度偏移量
    const observerOptions = {
      root: null, // 使用视口作为根
      rootMargin: `-${NAVBAR_OFFSET}px 0px -80% 0px`, // 顶部偏移 70px（导航栏高度），底部偏移 80%
      threshold: [0, 0.1, 0.5, 1] // 多个阈值，确保准确捕获
    };
    
    observer = new IntersectionObserver(function(entries) {
      // 找到所有正在视口中的标题，并计算它们距离视口顶部的距离
      const visibleHeadings = entries
        .filter(entry => entry.isIntersecting)
        .map(entry => {
          const rect = entry.target.getBoundingClientRect();
          return {
            id: entry.target.id,
            top: rect.top, // 距离视口顶部的距离
            intersectionRatio: entry.intersectionRatio
          };
        })
        .sort((a, b) => {
          // 优先选择 intersectionRatio 更大的（更接近视口顶部）
          if (Math.abs(a.top - NAVBAR_OFFSET) < Math.abs(b.top - NAVBAR_OFFSET)) {
            return -1;
          }
          if (Math.abs(a.top - NAVBAR_OFFSET) > Math.abs(b.top - NAVBAR_OFFSET)) {
            return 1;
          }
          // 如果距离相同，选择 intersectionRatio 更大的
          return b.intersectionRatio - a.intersectionRatio;
        });
      
      // 移除所有激活态
      headingLinkMap.forEach(link => {
        link.classList.remove('active');
      });
      
      // 激活最接近视口顶部（考虑偏移量）的标题对应的链接
      if (visibleHeadings.length > 0) {
        const targetId = visibleHeadings[0].id;
        const linkToActivate = headingLinkMap.get(targetId);
        if (linkToActivate) {
          // 检查激活项是否改变
          const isNewActive = activeLink !== linkToActivate;
          
          linkToActivate.classList.add('active');
          activeLink = linkToActivate;
          
          // 仅在激活项改变时，自动滚动大纲使激活项可见
          if (isNewActive) {
            // 使用 requestAnimationFrame 确保 DOM 更新完成后再滚动
            requestAnimationFrame(() => {
              linkToActivate.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'nearest'
              });
            });
          }
        }
      }
    }, observerOptions);
    
    // 观察所有标题
    headings.forEach(heading => {
      observer.observe(heading);
    });
  }
  
  /**
   * 初始化后端生成的 TOC（.toc）的交互功能
   */
  function initBackendTOC() {
    const tocContainer = document.querySelector('.toc');
    if (!tocContainer) return;
    
    const docContent = document.querySelector('.doc-content');
    if (!docContent) return;
    
    // 清空之前的映射（如果有）
    headingLinkMap.clear();
    
    // 如果已有观察器，先断开
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    
    // 获取所有 TOC 链接
    const tocLinks = tocContainer.querySelectorAll('a[href^="#"]');
    
    // 建立标题和链接的映射关系
    tocLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (!href || !href.startsWith('#')) return;
      
      const targetId = href.substring(1); // 去掉 # 号
      const targetHeading = document.getElementById(targetId);
      
      if (targetHeading) {
        headingLinkMap.set(targetId, link);
      }
    });
    
    // 如果没有任何映射，退出
    if (headingLinkMap.size === 0) return;
    
    // 为 TOC 链接添加点击事件处理（使用事件委托）
    tocContainer.addEventListener('click', function(e) {
      const link = e.target.closest('a[href^="#"]');
      if (!link) return;
      
      e.preventDefault();
      const href = link.getAttribute('href');
      if (!href || !href.startsWith('#')) return;
      
      const targetId = href.substring(1);
      const targetHeading = document.getElementById(targetId);
      
      if (targetHeading) {
        // 使用 scrollIntoView，CSS scroll-margin-top 会自动处理偏移量
        targetHeading.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
    
    // 使用 IntersectionObserver 实现激活态高亮
    const NAVBAR_OFFSET = 70;
    const observerOptions = {
      root: null,
      rootMargin: `-${NAVBAR_OFFSET}px 0px -80% 0px`,
      threshold: [0, 0.1, 0.5, 1]
    };
    
    // 获取所有需要观察的标题
    const headingsToObserve = Array.from(headingLinkMap.keys())
      .map(id => document.getElementById(id))
      .filter(h => h !== null);
    
    observer = new IntersectionObserver(function(entries) {
      const visibleHeadings = entries
        .filter(entry => entry.isIntersecting)
        .map(entry => {
          const rect = entry.target.getBoundingClientRect();
          return {
            id: entry.target.id,
            top: rect.top,
            intersectionRatio: entry.intersectionRatio
          };
        })
        .sort((a, b) => {
          if (Math.abs(a.top - NAVBAR_OFFSET) < Math.abs(b.top - NAVBAR_OFFSET)) {
            return -1;
          }
          if (Math.abs(a.top - NAVBAR_OFFSET) > Math.abs(b.top - NAVBAR_OFFSET)) {
            return 1;
          }
          return b.intersectionRatio - a.intersectionRatio;
        });
      
      // 移除所有激活态
      headingLinkMap.forEach(link => {
        link.classList.remove('active');
      });
      
      // 激活最接近视口顶部的标题对应的链接
      if (visibleHeadings.length > 0) {
        const targetId = visibleHeadings[0].id;
        const linkToActivate = headingLinkMap.get(targetId);
        if (linkToActivate) {
          const isNewActive = activeLink !== linkToActivate;
          linkToActivate.classList.add('active');
          activeLink = linkToActivate;
          
          // 自动滚动大纲使激活项可见
          if (isNewActive) {
            requestAnimationFrame(() => {
              linkToActivate.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'nearest'
              });
            });
          }
        }
      }
    }, observerOptions);
    
    // 观察所有标题
    headingsToObserve.forEach(heading => {
      observer.observe(heading);
    });
  }
  
  /**
   * 初始化：确保 DOM 完全加载后再生成大纲
   */
  function init() {
    // 使用多种方式确保目录生成时机正确
    function tryGenerateOutline() {
      const docContent = document.querySelector('.doc-content');
      if (docContent && docContent.children.length > 0) {
        // 检查是否有后端生成的 TOC
        const tocContainer = document.querySelector('.toc');
        if (tocContainer) {
          // 如果有后端 TOC，初始化它的交互功能
          initBackendTOC();
        } else {
          // 否则使用 JavaScript 生成大纲
          generateOutline();
        }
      } else {
        // 如果内容还没加载，延迟重试
        setTimeout(tryGenerateOutline, 100);
      }
    }
    
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        // DOM 加载完成后，再等待一下确保内容渲染完成
        setTimeout(tryGenerateOutline, 50);
      });
    } else {
      // DOM 已经加载完成，延迟执行确保内容已渲染
      setTimeout(tryGenerateOutline, 50);
    }
    
    // 监听批注加载完成事件，重新生成大纲
    window.addEventListener('annotationsLoaded', function() {
      // 延迟重新生成，确保 DOM 更新完成
      setTimeout(generateOutline, 100);
    });
    
    // 使用 MutationObserver 监听内容变化，自动重新生成目录
    const docContent = document.querySelector('.doc-content');
    if (docContent) {
      const observer = new MutationObserver(function(mutations) {
        // 当内容发生变化时，重新生成目录
        let shouldRegenerate = false;
        mutations.forEach(function(mutation) {
          if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            // 检查是否有新的标题节点被添加
            mutation.addedNodes.forEach(function(node) {
              if (node.nodeType === 1) { // Element node
                if (node.tagName && /^H[123]$/.test(node.tagName)) {
                  shouldRegenerate = true;
                } else if (node.querySelectorAll) {
                  const headings = node.querySelectorAll('h1, h2, h3');
                  if (headings.length > 0) {
                    shouldRegenerate = true;
                  }
                }
              }
            });
          }
        });
        
        if (shouldRegenerate) {
          setTimeout(generateOutline, 100);
        }
      });
      
      observer.observe(docContent, {
        childList: true,
        subtree: true
      });
    }
  }
  
  // 执行初始化
  init();
  
  // 注意：目录展开/收起功能由 annotations.js 中的 initOutlineToggle() 统一处理
  // 这里不再重复实现，避免事件监听器冲突
})();

/**
 * Toast 通知系统
 * 提供优雅的全局通知功能，替代浏览器原生 alert()
 */
(function() {
  'use strict';
  
  /**
   * 显示 Toast 通知
   * @param {string} message - 通知消息
   * @param {string} type - 通知类型：'success' | 'error' | 'info'，默认为 'success'
   * @param {number} duration - 显示时长（毫秒），默认 3000ms
   */
  function showToast(message, type = 'success', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) {
      console.error('Toast container not found');
      return;
    }
    
    // 创建 Toast 元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // 添加到容器
    container.appendChild(toast);
    
    // 触发动画
    requestAnimationFrame(() => {
      toast.classList.add('toast-show');
    });
    
    // 自动移除
    setTimeout(() => {
      toast.classList.remove('toast-show');
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300); // 等待淡出动画完成
    }, duration);
  }
  
  // 暴露到全局作用域
  window.showToast = showToast;
})();

/**
 * 确认对话框系统
 * 提供优雅的确认对话框功能，替代浏览器原生 confirm()
 */
(function() {
  'use strict';
  
  /**
   * 显示确认对话框
   * @param {string} message - 确认消息
   * @param {string} title - 对话框标题，默认为 "确认操作"
   * @param {Object} options - 选项配置（可选）
   * @param {string} options.confirmText - 确认按钮文本，默认为 "确定"
   * @param {string} options.cancelText - 取消按钮文本，默认为 "取消"
   * @returns {Promise<boolean>} - 返回 Promise，用户点击确定返回 true，取消返回 false
   */
  function showConfirmDialog(message, title = 'Confirm', options = {}) {
    return new Promise((resolve) => {
      const overlay = document.getElementById('confirm-dialog-overlay');
      if (!overlay) {
        console.error('Confirm dialog overlay not found');
        resolve(false);
        return;
      }
      
      const heading = overlay.querySelector('.confirm-dialog-heading');
      const description = overlay.querySelector('.confirm-dialog-description');
      const acceptButton = overlay.querySelector('.confirm-dialog-accept-button');
      const declineButton = overlay.querySelector('.confirm-dialog-decline-button');
      
      // 设置内容
      heading.textContent = title;
      description.textContent = message;
      acceptButton.textContent = options.confirmText || 'OK';
      declineButton.textContent = options.cancelText || 'Cancel';
      
      // 设置确认按钮样式
      acceptButton.className = 'confirm-dialog-accept-button';
      if (options.confirmColor === 'danger') {
        acceptButton.classList.add('confirm-dialog-btn-danger');
      }
      
      // 清理之前的事件监听器（通过克隆按钮）
      const newAcceptButton = acceptButton.cloneNode(true);
      const newDeclineButton = declineButton.cloneNode(true);
      acceptButton.parentNode.replaceChild(newAcceptButton, acceptButton);
      declineButton.parentNode.replaceChild(newDeclineButton, declineButton);
      
      // 重新设置样式
      newAcceptButton.className = acceptButton.className;
      if (options.confirmColor === 'danger') {
        newAcceptButton.classList.add('confirm-dialog-btn-danger');
      }
      
      // 确定按钮事件
      const acceptHandler = function() {
        hideConfirm();
        resolve(true);
      };
      newAcceptButton.addEventListener('click', acceptHandler);
      
      // 取消按钮事件
      const declineHandler = function() {
        hideConfirm();
        resolve(false);
      };
      newDeclineButton.addEventListener('click', declineHandler);
      
      // 点击遮罩层关闭
      const overlayClickHandler = function(e) {
        if (e.target === overlay) {
          hideConfirm();
          resolve(false);
        }
      };
      overlay.addEventListener('click', overlayClickHandler);
      
      // ESC 键关闭
      const escHandler = function(e) {
        if (e.key === 'Escape') {
          hideConfirm();
          resolve(false);
        }
      };
      document.addEventListener('keydown', escHandler);
      
      // 显示对话框
      overlay.style.display = 'flex';
      requestAnimationFrame(() => {
        overlay.classList.add('confirm-dialog-show');
      });
      
      function hideConfirm() {
        overlay.classList.remove('confirm-dialog-show');
        setTimeout(() => {
          overlay.style.display = 'none';
          document.removeEventListener('keydown', escHandler);
          overlay.removeEventListener('click', overlayClickHandler);
        }, 200);
      }
    });
  }
  
  // 暴露到全局作用域
  window.showConfirmDialog = showConfirmDialog;
  // 创建别名以保持兼容性
  window.showConfirm = showConfirmDialog;
})();

/**
 * 回到顶部按钮功能
 * 基于 Uiverse.io 样式实现
 */
(function() {
  'use strict';
  
  const SCROLL_THRESHOLD = 300; // 滚动超过 300px 时显示按钮
  
  function initScrollToTop() {
    const scrollButton = document.getElementById('scroll-to-top');
    if (!scrollButton) return;
    
    // 检查滚动位置并显示/隐藏按钮
    function toggleScrollButton() {
      const scrollY = window.pageYOffset || document.documentElement.scrollTop;
      
      if (scrollY > SCROLL_THRESHOLD) {
        scrollButton.classList.add('show');
      } else {
        scrollButton.classList.remove('show');
      }
    }
    
    // 点击按钮平滑滚动到顶部
    scrollButton.addEventListener('click', function() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
    
    // 监听滚动事件
    let ticking = false;
    function onScroll() {
      if (!ticking) {
        window.requestAnimationFrame(function() {
          toggleScrollButton();
          ticking = false;
        });
        ticking = true;
      }
    }
    
    window.addEventListener('scroll', onScroll, { passive: true });
    
    // 初始化时检查一次
    toggleScrollButton();
  }
  
  // 页面加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScrollToTop);
  } else {
    initScrollToTop();
  }
})();

/**
 * 文章删除功能
 * 在文章容器右上角显示删除按钮，点击后弹出确认对话框
 */
(function() {
  'use strict';
  
  function initDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.note-delete-btn');
    if (!deleteButtons.length) return;
    
    deleteButtons.forEach(function(button) {
      button.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const noteId = button.getAttribute('data-note-id');
        const noteItem = button.closest('.note-list-item');
        const noteTitle = noteItem ? noteItem.querySelector('.note-title')?.textContent?.trim() || '这篇文章' : '这篇文章';
        
        // 显示确认删除对话框
        if (window.showConfirmDialog) {
          window.showConfirmDialog(
            `确定要删除"${noteTitle}"吗？此操作不可恢复。`,
            '确认删除',
            {
              confirmText: '确定',
              cancelText: '取消',
              confirmColor: 'danger'
            }
          ).then(function(confirmed) {
            if (confirmed) {
              // 执行删除操作
              deleteNote(noteId, noteItem);
            }
          });
        } else {
          // 如果没有确认对话框，使用浏览器原生确认
          if (confirm(`确定要删除"${noteTitle}"吗？此操作不可恢复。`)) {
            deleteNote(noteId, noteItem);
          }
        }
      });
    });
  }
  
  function deleteNote(noteId, noteItem) {
    // 发送删除请求
    fetch(`/api/note/${noteId}/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(function(response) {
      if (!response.ok) {
        throw new Error('删除失败');
      }
      return response.json();
    })
    .then(function(data) {
      if (data.success) {
        // 添加淡出动画
        if (noteItem) {
          noteItem.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
          noteItem.style.opacity = '0';
          noteItem.style.transform = 'translateX(-20px)';
          
          // 等待动画完成后移除元素
          setTimeout(function() {
            noteItem.remove();
            
            // 检查是否还有文章，如果没有则显示空提示
            const noteList = document.querySelector('.note-list');
            if (noteList && noteList.querySelectorAll('.note-list-item').length === 0) {
              const pageSection = document.querySelector('.page-section');
              if (pageSection) {
                const emptyTip = document.createElement('p');
                emptyTip.className = 'empty-tip';
                emptyTip.textContent = '还没有任何素材，点击右上角"新建素材"开始录入。';
                noteList.parentNode.insertBefore(emptyTip, noteList);
                noteList.remove();
              }
            }
          }, 300);
        } else {
          // 如果没有找到元素，直接刷新页面
          window.location.reload();
        }
      } else {
        throw new Error(data.message || '删除失败');
      }
    })
    .catch(function(error) {
      console.error('删除文章失败:', error);
      alert('删除失败，请稍后重试。');
    });
  }
  
  // 初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDeleteButtons);
  } else {
    initDeleteButtons();
  }
})();

/**
 * 求真务实·滚轮开门见锁沉浸式锁定系统
 * 实现：滚轮向下拉开幕布，超过40%显示密码层，解锁后文字淡出0.8s
 */
(function() {
  'use strict';
  
  const LOCK_PASSWORD = '0739';
  // 将解锁状态持久化到 localStorage，并增加有效期，确保跨标签页/浏览器重启共享状态
  const LOCK_STORAGE_KEY = 'lockScreenUnlocked_v2';
  const LOCK_MAX_AGE_DAYS = 7; // 解锁状态默认有效期（单位：天）
  const SCROLL_THRESHOLD = 1000; // 累积滚动1000px才完全拉开
  const PASSWORD_REVEAL_THRESHOLD = 0.4; // 幕布拉开40%时显示密码层
  const SVG_FADE_OUT_THRESHOLD = 0.8; // 幕布拉开80%时图片渐隐
  const TEXT_FADE_OUT_DURATION = 800; // 文字淡出持续时间（毫秒）
  const IS_TOUCH_DEVICE = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;
  
  // 延迟获取元素，确保 DOM 已加载
  let lockScreen, passwordInput, lockTextLayer, passwordLayer, curtainTop, curtainBottom, lockScreenBtn, contentBlurOverlay;
  const isMobile = window.innerWidth <= 768;
  
  function getElements() {
    lockScreen = document.getElementById('lock-screen');
    passwordInput = document.getElementById('lock-password-input');
    lockTextLayer = document.getElementById('lock-text-layer');
    passwordLayer = document.getElementById('lock-password-layer');
    curtainTop = document.querySelector('.curtain-top');
    curtainBottom = document.querySelector('.curtain-bottom');
    lockScreenBtn = document.getElementById('lock-screen-btn');
    contentBlurOverlay = document.getElementById('content-blur-overlay');
    
    return lockScreen && passwordInput && lockTextLayer && passwordLayer && curtainTop && curtainBottom;
  }
  
  // 等待 DOM 加载完成后再初始化
  function waitForElements(callback) {
    if (getElements()) {
      callback();
    } else {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
          setTimeout(() => waitForElements(callback), 50);
        });
      } else {
        setTimeout(() => waitForElements(callback), 50);
      }
    }
  }
  
  let scrollDelta = 0; // 累积的滚动距离
  let isUnlocking = false; // 是否正在解锁（防止重复触发）
  let lastTouchY = null; // 记录触摸起点，用于模拟滚轮
  
  /**
   * 检查是否已解锁（从 localStorage 读取，并校验有效期）
   */
  function isUnlocked() {
    try {
      const raw = window.localStorage.getItem(LOCK_STORAGE_KEY);
      if (!raw) return false;

      let data = null;
      try {
        data = JSON.parse(raw);
      } catch (e) {
        // 旧版本可能直接存的是 'true' 字符串，兼容处理：视为已解锁但无过期时间
        if (raw === 'true') {
          return true;
        }
        return false;
      }

      if (!data || !data.unlocked) {
        return false;
      }

      // 没有过期时间，视为未解锁（防御性处理）
      if (!data.expiresAt) {
        return false;
      }

      const now = Date.now();
      if (now > data.expiresAt) {
        // 已过期，主动清理本地缓存
        window.localStorage.removeItem(LOCK_STORAGE_KEY);
        return false;
      }

      return true;
    } catch (e) {
      return false;
    }
  }
  
  /**
   * 保存解锁状态到 sessionStorage
   */
  function saveUnlockState(unlocked) {
    try {
      if (unlocked) {
        const expiresAt =
          Date.now() + LOCK_MAX_AGE_DAYS * 24 * 60 * 60 * 1000;
        const payload = {
          unlocked: true,
          expiresAt,
        };
        window.localStorage.setItem(LOCK_STORAGE_KEY, JSON.stringify(payload));
      } else {
        window.localStorage.removeItem(LOCK_STORAGE_KEY);
      }
    } catch (e) {
      console.warn('无法保存解锁状态:', e);
    }
  }
  
  /**
   * 验证密码
   */
  function verifyPassword(password) {
    return password === LOCK_PASSWORD;
  }
  
  
  /**
   * 重新锁定屏幕（点击锁定按钮时调用）
   */
  function relockScreen() {
    // 清除解锁状态
    saveUnlockState(false);
    
    // 重置状态
    isUnlocking = false;
    scrollDelta = 0;
    
    // 重新创建锁定屏（如果已被移除）
    if (!lockScreen || !lockScreen.parentNode) {
      createLockScreen();
      waitForElements(() => {
        initLockScreenFeatures();
        applyLockState();
      });
      return;
    }
    
    // 重置SVG透明度和可见性
    if (lockTextLayer) {
      lockTextLayer.style.opacity = '1';
      lockTextLayer.style.visibility = 'visible';
      if (lockSvg) {
        lockSvg.style.opacity = '1';
      }
    }
    
    // 重置幕布位置
    if (curtainTop) {
      curtainTop.style.transform = 'translateY(0)';
    }
    if (curtainBottom) {
      curtainBottom.style.transform = 'translateY(0)';
    }
    
    // 隐藏密码层
    passwordLayer.classList.remove('visible');
    passwordInput.value = '';
    
    // 重新创建毛玻璃遮罩层（如果不存在）
    if (!contentBlurOverlay || !contentBlurOverlay.parentNode) {
      if (!document.getElementById('content-blur-overlay')) {
        const blurOverlay = document.createElement('div');
        blurOverlay.id = 'content-blur-overlay';
        document.body.insertAdjacentElement('beforeend', blurOverlay);
        contentBlurOverlay = blurOverlay;
      } else {
        contentBlurOverlay = document.getElementById('content-blur-overlay');
      }
    }
    
    // 重新应用锁定状态
    document.body.classList.add('lock-screen-active');
  }
  
  /**
   * 创建锁定屏 DOM（如果不存在）
   */
  function createLockScreen() {
    if (document.getElementById('lock-screen')) {
      return; // 已存在
    }
    
    const lockScreenHTML = `
      <div id="lock-screen">
        <div id="lock-text-layer">
          <img src="/static/images/实事求是.jpg" alt="实事求是" class="lock-img" />
        </div>
        <div class="curtain-top"></div>
        <div class="curtain-bottom"></div>
        <div id="lock-password-layer">
          <div id="lock-password-title">请输入解锁密码</div>
          <input 
            type="password" 
            id="lock-password-input" 
            placeholder="输入密码解锁"
            autocomplete="off"
          />
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', lockScreenHTML);
    
    // 创建毛玻璃遮罩层（如果不存在，且为 PC 端）
    if (!isMobile && !document.getElementById('content-blur-overlay')) {
      const blurOverlay = document.createElement('div');
      blurOverlay.id = 'content-blur-overlay';
      document.body.insertAdjacentElement('beforeend', blurOverlay);
      contentBlurOverlay = blurOverlay;
    }
  }
  
  /**
   * 更新幕布位置（根据滚动距离）
   */
  function updateCurtainPosition() {
    if (!lockScreen || !lockScreen.parentNode || isUnlocked() || !curtainTop || !curtainBottom) return;
    
    const openPercent = Math.min(scrollDelta / SCROLL_THRESHOLD, 1);
    
    requestAnimationFrame(() => {
      // 上幕布向上移动（translateY(-100vh)）
      curtainTop.style.transform = `translateY(${-openPercent * 100}vh)`;
      // 下幕布向下移动（translateY(100vh)）
      curtainBottom.style.transform = `translateY(${openPercent * 100}vh)`;
      
      // 当幕布拉开超过40%时，显示密码层（见证奇迹）
      if (openPercent >= PASSWORD_REVEAL_THRESHOLD && passwordLayer) {
        passwordLayer.classList.add('visible');
      } else if (openPercent < PASSWORD_REVEAL_THRESHOLD && passwordLayer) {
        passwordLayer.classList.remove('visible');
      }
      
      // 当幕布拉开达到80%时，图片文字渐隐消失
      if (openPercent >= SVG_FADE_OUT_THRESHOLD && lockTextLayer) {
        lockTextLayer.style.opacity = '0';
        lockTextLayer.style.visibility = 'hidden';
      } else if (openPercent < SVG_FADE_OUT_THRESHOLD && lockTextLayer) {
        lockTextLayer.style.opacity = '1';
        lockTextLayer.style.visibility = 'visible';
      }
    });
  }
  
  /**
   * 处理密码输入
   */
  function handlePasswordSubmit() {
    if (isUnlocking) return; // 防止重复触发
    
    const password = passwordInput.value.trim();
    
    if (!password) {
      return;
    }
    
    if (verifyPassword(password)) {
      // 密码正确，开始解锁流程
      isUnlocking = true;
      
      // 隐藏密码层
      passwordLayer.classList.remove('visible');
      passwordInput.value = '';
      passwordInput.blur();
      
      // 图片文字淡出（0.8s）
      if (lockTextLayer) {
        lockTextLayer.style.opacity = '0';
      }
      
      // 等待文字淡出完成后，移除所有锁定元素
      setTimeout(() => {
        if (lockScreen && lockScreen.parentNode) {
          lockScreen.remove();
        }
        // 移除毛玻璃遮罩层
        if (contentBlurOverlay && contentBlurOverlay.parentNode) {
          contentBlurOverlay.remove();
        }
        document.body.classList.remove('lock-screen-active');
        saveUnlockState(true);
        
        // 重置状态
        isUnlocking = false;
        scrollDelta = 0;
      }, TEXT_FADE_OUT_DURATION);
    } else {
      // 密码错误，震动提示
      passwordLayer.style.animation = 'shake 0.5s ease';
      setTimeout(() => {
        passwordLayer.style.animation = '';
        passwordInput.value = '';
        passwordInput.focus();
      }, 500);
    }
  }
  
  /**
   * 处理滚轮事件（向下滚动拉开幕布）
   */
  function handleWheel(e) {
    // 锁定状态下禁用body原生滚动
    if (lockScreen && lockScreen.parentNode && !isUnlocked()) {
      e.preventDefault();
      e.stopPropagation();
      
      // 只响应向下滚动拉开幕布
      if (e.deltaY > 0) {
        scrollDelta += e.deltaY;
        updateCurtainPosition();
      }
    }
  }
  
  /**
   * 处理触摸开始（移动端模拟滚轮）
   */
  function handleTouchStart(e) {
    if (lockScreen && lockScreen.parentNode && !isUnlocked()) {
      if (e.touches && e.touches.length > 0) {
        lastTouchY = e.touches[0].clientY;
      }
      // 阻止页面本身的滚动
      e.preventDefault();
    }
  }

  /**
   * 处理触摸滑动（向上滑动手指，相当于向下滚轮）
   */
  function handleTouchMove(e) {
    if (lockScreen && lockScreen.parentNode && !isUnlocked()) {
      if (!e.touches || e.touches.length === 0) return;
      const currentY = e.touches[0].clientY;
      if (lastTouchY == null) {
        lastTouchY = currentY;
        return;
      }
      const deltaY = lastTouchY - currentY; // 手指向上滑，deltaY 为正
      if (deltaY > 0) {
        // 适当放大一点，让移动端滑几下就能到达阈值
        scrollDelta += deltaY * 3;
        updateCurtainPosition();
      }
      lastTouchY = currentY;
      e.preventDefault();
    }
  }

  /**
   * 触摸结束时重置起点
   */
  function handleTouchEnd(e) {
    if (lockScreen && lockScreen.parentNode && !isUnlocked()) {
      lastTouchY = null;
      e.preventDefault();
    }
  }
  
  /**
   * 防止键盘滚动
   */
  function handleKeyDown(e) {
    if (lockScreen && lockScreen.parentNode && !isUnlocked()) {
      if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(e.key)) {
        e.preventDefault();
      }
    }
  }
  
  // 初始化所有事件监听器和功能
  function initLockScreenFeatures() {
    // 密码输入框回车提交
    passwordInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        handlePasswordSubmit();
      }
    });

    // 放大可点击区域：点击密码层任意位置，都尝试聚焦输入框（适配 iOS 触摸）
    if (passwordLayer && passwordInput) {
      passwordLayer.addEventListener('click', function() {
        try {
          passwordInput.focus();
        } catch (err) {
          // 某些 iOS 场景下仍可能被系统拦截，这里静默降级
        }
      });
    }
    
    // PC 端沉浸式滚轮开门逻辑：移动端不再需要这套复杂交互
    if (!isMobile) {
      // 监听滚轮事件（PC 端：禁用原生滚动，实现滚轮拉开幕布）
      window.addEventListener('wheel', handleWheel, { passive: false });

      // 监听触摸事件（平板等设备：用手指上滑代替滚轮）
      window.addEventListener('touchstart', handleTouchStart, { passive: false });
      window.addEventListener('touchmove', handleTouchMove, { passive: false });
      window.addEventListener('touchend', handleTouchEnd, { passive: false });
      
      // 防止键盘滚动
      window.addEventListener('keydown', handleKeyDown);
    }
    
    // 添加密码错误时的震动动画
    const style = document.createElement('style');
    style.textContent = `
      @keyframes shake {
        0%, 100% { transform: translate(-50%, -50%); }
        10%, 30%, 50%, 70%, 90% { transform: translate(calc(-50% - 10px), -50%); }
        20%, 40%, 60%, 80% { transform: translate(calc(-50% + 10px), -50%); }
      }
    `;
    document.head.appendChild(style);
    
    // 检查是否已解锁
    function applyLockState() {
      if (isUnlocked()) {
        // 已解锁，移除锁定屏和毛玻璃遮罩
        if (lockScreen && lockScreen.parentNode) {
          // 先从视觉和交互层面彻底禁用，再物理移除（兼容 iOS 触摸命中规则）
          lockScreen.style.pointerEvents = 'none';
          lockScreen.style.opacity = '0';
          lockScreen.style.display = 'none';
          lockScreen.remove();
        }
        if (contentBlurOverlay && contentBlurOverlay.parentNode) {
          contentBlurOverlay.style.pointerEvents = 'none';
          contentBlurOverlay.style.opacity = '0';
          contentBlurOverlay.style.display = 'none';
          contentBlurOverlay.remove();
        }
        document.body.classList.remove('lock-screen-active');
      } else {
        // 未解锁：根据终端类型走不同逻辑
        if (lockScreen) {
          lockScreen.style.display = 'block';
        }

        // PC 端：保留原有毛玻璃和沉浸式体验
        if (!isMobile) {
          // 确保毛玻璃遮罩层存在
          if (!contentBlurOverlay || !contentBlurOverlay.parentNode) {
            if (!document.getElementById('content-blur-overlay')) {
              const blurOverlay = document.createElement('div');
              blurOverlay.id = 'content-blur-overlay';
              document.body.insertAdjacentElement('beforeend', blurOverlay);
              contentBlurOverlay = blurOverlay;
            } else {
              contentBlurOverlay = document.getElementById('content-blur-overlay');
            }
          }
        }

        document.body.classList.add('lock-screen-active');

        if (isMobile) {
          // 移动端极简逻辑：
          // 1. 立即展示密码层（配合 CSS 纯白背景）
          // 2. 延迟 0.5 秒强制聚焦输入框，唤起键盘
          if (passwordLayer) {
            passwordLayer.classList.add('visible');
          }
          if (passwordInput) {
            passwordInput.style.opacity = '1';
            setTimeout(() => {
              try {
                passwordInput.focus();
              } catch (err) {
                // 某些 iOS WebView 仍可能拦截，这里静默失败即可
              }
            }, 500);
          }
        } else {
          // PC 端：首次进入锁定状态时展示密码层，避免必须依赖滚轮/滑动才能解锁
          if (passwordLayer) {
            passwordLayer.classList.add('visible');
          }
          // 对触摸设备做体验优化：在动画完全结束后自动聚焦一次，确保键盘弹出
          if (IS_TOUCH_DEVICE && passwordInput) {
            // 幕布动画约 0.3s，文字淡出约 0.8s，这里预留 2s 兜底
            setTimeout(() => {
              try {
                passwordInput.focus();
              } catch (err) {
                // iOS 某些环境可能依旧拦截，此处兜底即可
              }
            }, 2000);
          }
        }
      }
    }
    
    applyLockState();
    
    // 锁定按钮点击事件（即时响应）
    if (lockScreenBtn) {
      lockScreenBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        relockScreen();
      });
    }
  }
  
  // 等待元素加载完成后初始化
  waitForElements(initLockScreenFeatures);
  
})();
