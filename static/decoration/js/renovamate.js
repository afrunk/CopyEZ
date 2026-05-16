// ============================================================
// RenovaMate - Shared JavaScript
// ============================================================

// Project state (from Flask backend via window.projectData)
var projectState = {
  totalBudget: 0,
  actualSpent: 0,
  estimatedCost: 0,
  projectName: '',
  area: '',
  style: '',
  currentStage: '',
  projectId: null
};

// Initialize from window.projectData if available (set by Flask template)
if (window.projectData) {
  projectState.projectId = window.projectData.id;
  projectState.projectName = window.projectData.name || '';
  projectState.area = window.projectData.area || '';
  projectState.style = window.projectData.style || '';
  projectState.totalBudget = window.projectData.budget || 0;
  projectState.currentStage = window.projectData.stage || '';
}

// Format number with thousand separators
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Parse formatted number
function parseFormattedNumber(str) {
  return parseInt(str.replace(/,/g, '')) || 0;
}

// 获取平台信息（全局函数）
function getPlatformInfo(url) {
  if (!url) return null;
  var lower = url.toLowerCase();
  if (lower.includes('xiaohongshu.com') || lower.includes('xhslink.com')) {
    return { name: '小红书', icon: '📕', color: '#FF2442', bg: '#FFF0F3' };
  }
  if (lower.includes('douyin.com') || lower.includes('v.douyin.com')) {
    return { name: '抖音', icon: '🎵', color: '#000000', bg: '#F5F5F5' };
  }
  if (lower.includes('taobao.com') || lower.includes('tmall.com')) {
    return { name: '淘宝', icon: '🛒', color: '#FF5000', bg: '#FFF5F0' };
  }
  if (lower.includes('jd.com') || lower.includes('jd.hk')) {
    return { name: '京东', icon: '📦', color: '#E1251B', bg: '#FFF0F0' };
  }
  if (lower.includes('pinduoduo.com') || lower.includes('pdd')) {
    return { name: '拼多多', icon: '🛍️', color: '#E1251B', bg: '#FFF0F0' };
  }
  if (lower.includes('weixin.qq.com') || lower.includes('mp.weixin')) {
    return { name: '微信', icon: '💬', color: '#07C160', bg: '#F0FFF5' };
  }
  if (lower.includes('bilibili.com') || lower.includes('b23.tv')) {
    return { name: 'B站', icon: '📺', color: '#00A1D6', bg: '#F0FAFF' };
  }
  if (lower.includes('zhihu.com')) {
    return { name: '知乎', icon: '💡', color: '#0066FF', bg: '#F0F8FF' };
  }
  if (lower.includes('youzhan')) {
    return { name: '有赞', icon: '🏪', color: '#FF6B00', bg: '#FFF8F0' };
  }
  if (lower.includes('meituan') || lower.includes('dianping')) {
    return { name: '美团', icon: '🍔', color: '#FFD100', bg: '#FFFBE6' };
  }
  return null; // 不支持的平台
}

// 修复 URL，添加协议前缀
function fixUrl(url) {
  if (!url) return '';
  url = url.trim();
  // 如果 URL 不以 http:// 或 https:// 开头，则添加 https://
  if (!/^https?:\/\//i.test(url)) {
    url = 'https://' + url;
  }
  return url;
}

// Toast notification
function showToast(message) {
  let toast = document.querySelector('.toast-message');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast-message';
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(function() {
    toast.classList.remove('show');
  }, 2000);
}

// Image upload handler for decoration notes
// fileInput: the <input type="file"> element
// hiddenUrlInputId: the ID of the hidden input to store the uploaded URL
// previewId: the ID of the preview div
function handleImageUpload(fileInput, hiddenUrlInputId, previewId) {
  var file = fileInput.files[0];
  if (!file) return;

  var preview = document.getElementById(previewId);
  var urlInput = document.getElementById(hiddenUrlInputId);

  // Validate file type
  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件');
    return;
  }

  // Show loading state on preview
  if (preview) {
    preview.innerHTML = '<span class="img-upload-placeholder" style="color: var(--accent-orange);">上传中...</span>';
  }

  // Upload file
  var formData = new FormData();
  formData.append('image', file);

  fetch(apiBase + '/api/upload/image', {
    method: 'POST',
    body: formData
  })
  .then(function(res) {
    return res.json();
  })
  .then(function(data) {
    if (!data.success) {
      showToast(data.message || '图片上传失败');
      // Reset preview
      if (preview) {
        preview.innerHTML = '<span class="img-upload-placeholder">点击上传</span>';
        preview.classList.remove('has-image');
      }
      return;
    }

    // Success - update URL and show preview
    var url = data.url;
    if (urlInput) urlInput.value = url;

    if (preview) {
      preview.innerHTML = '<img src="' + url + '" alt="预览"><button type="button" class="img-upload-remove" onclick="event.stopPropagation(); removeImageUpload(\'' + hiddenUrlInputId + '\', \'' + previewId + '\', \'' + fileInput.id + '\')"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>';
      preview.classList.add('has-image');
    }

    showToast('图片上传成功');
  })
  .catch(function(err) {
    console.error('Image upload failed:', err);
    showToast('图片上传失败，请重试');
    // Reset preview
    if (preview) {
      preview.innerHTML = '<span class="img-upload-placeholder">点击上传</span>';
      preview.classList.remove('has-image');
    }
  });
}

// Remove uploaded image
function removeImageUpload(hiddenUrlInputId, previewId, fileInputId) {
  var urlInput = document.getElementById(hiddenUrlInputId);
  var preview = document.getElementById(previewId);
  var fileInput = document.getElementById(fileInputId);

  if (urlInput) urlInput.value = '';
  if (fileInput) fileInput.value = '';

  if (preview) {
    preview.innerHTML = '<span class="img-upload-placeholder">点击上传</span>';
    preview.classList.remove('has-image');
  }
}

// New image upload handler for flexible layout (add modal)
function handleNewImageUpload(fileInput) {
  var file = fileInput.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件');
    return;
  }

  var container = document.getElementById('noteImageContainer');
  var addBtn = container.querySelector('.img-upload-add-btn');

  // Show loading
  var loadingHtml = '<div class="img-upload-item uploading">' +
    '<div class="img-upload-preview"><span class="img-upload-placeholder">上传中...</span></div>' +
    '</div>';
  container.insertBefore(document.createRange().createContextualFragment(loadingHtml), addBtn);

  var formData = new FormData();
  formData.append('image', file);

  fetch(apiBase + '/api/upload/image', {
    method: 'POST',
    body: formData
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (!data.success) {
      showToast(data.message || '图片上传失败');
      container.removeChild(container.querySelector('.img-upload-item.uploading'));
      return;
    }

    // Remove loading placeholder
    var loadingItem = container.querySelector('.img-upload-item.uploading');
    if (loadingItem) container.removeChild(loadingItem);

    var url = data.url;
    var index = Date.now();

    // Create image item
    var imgItem = document.createElement('div');
    imgItem.className = 'img-upload-item';
    imgItem.innerHTML =
      '<input type="hidden" id="noteImg_' + index + '" value="' + url + '">' +
      '<div class="img-upload-preview has-image">' +
        '<img src="' + url + '" alt="预览">' +
        '<button type="button" class="img-upload-remove" onclick="removeNewImage(this, \'noteImg_' + index + '\')">' +
          '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>' +
        '</button>' +
      '</div>';

    container.insertBefore(imgItem, addBtn);
    showToast('图片上传成功');

    // Clear file input for next upload
    fileInput.value = '';
  })
  .catch(function(err) {
    console.error('Image upload failed:', err);
    showToast('图片上传失败，请重试');
    container.removeChild(container.querySelector('.img-upload-item.uploading'));
    fileInput.value = '';
  });
}

// New image upload handler for edit modal
function handleNewImageUploadEdit(fileInput) {
  var file = fileInput.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件');
    return;
  }

  var container = document.getElementById('editNoteImageContainer');
  var addBtn = container.querySelector('.img-upload-add-btn');

  // Show loading
  var loadingHtml = '<div class="img-upload-item uploading">' +
    '<div class="img-upload-preview"><span class="img-upload-placeholder">上传中...</span></div>' +
    '</div>';
  container.insertBefore(document.createRange().createContextualFragment(loadingHtml), addBtn);

  var formData = new FormData();
  formData.append('image', file);

  fetch(apiBase + '/api/upload/image', {
    method: 'POST',
    body: formData
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (!data.success) {
      showToast(data.message || '图片上传失败');
      container.removeChild(container.querySelector('.img-upload-item.uploading'));
      return;
    }

    // Remove loading placeholder
    var loadingItem = container.querySelector('.img-upload-item.uploading');
    if (loadingItem) container.removeChild(loadingItem);

    var url = data.url;
    var index = 'edit_' + Date.now();

    // Create image item
    var imgItem = document.createElement('div');
    imgItem.className = 'img-upload-item';
    imgItem.innerHTML =
      '<input type="hidden" id="' + index + '" value="' + url + '">' +
      '<div class="img-upload-preview has-image">' +
        '<img src="' + url + '" alt="预览">' +
        '<button type="button" class="img-upload-remove" onclick="removeNewImage(this, \'' + index + '\')">' +
          '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>' +
        '</button>' +
      '</div>';

    container.insertBefore(imgItem, addBtn);
    showToast('图片上传成功');

    fileInput.value = '';
  })
  .catch(function(err) {
    console.error('Image upload failed:', err);
    showToast('图片上传失败，请重试');
    container.removeChild(container.querySelector('.img-upload-item.uploading'));
    fileInput.value = '';
  });
}

// Remove image from flexible layout
function removeNewImage(btn, hiddenInputId) {
  var item = btn.closest('.img-upload-item');
  if (item) {
    item.parentNode.removeChild(item);
  }
}

// Toggle sidebar collapse (PC/iPad only)
function toggleSidebar() {
  // On mobile, sidebar is always collapsed - don't allow expand
  if (window.innerWidth < 900) {
    showToast('移动端侧边栏保持收起');
    return;
  }

  document.body.classList.toggle('sidebar-collapsed');
  localStorage.setItem(
    'renovamate-sidebar-collapsed',
    document.body.classList.contains('sidebar-collapsed') ? '1' : '0'
  );
}

// Toggle mobile sidebar
function toggleMobileSidebar() {
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebarOverlay');

  if (sidebar && overlay) {
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');
  }
}

// Modal functions
function openModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Image Lightbox functions
var lightboxImages = [];
var lightboxCurrentIndex = 0;

function openImageLightbox(imageUrl, images) {
  // 解析 images（可能是 JSON 字符串或数组）
  var parsedImages = images;
  if (typeof images === 'string') {
    try {
      parsedImages = JSON.parse(images);
    } catch(e) {
      parsedImages = [imageUrl];
    }
  }
  // Store all images for navigation
  lightboxImages = Array.isArray(parsedImages) ? parsedImages : [imageUrl];
  lightboxCurrentIndex = lightboxImages.indexOf(imageUrl);
  if (lightboxCurrentIndex < 0) lightboxCurrentIndex = 0;

  // Create lightbox if not exists
  var lightbox = document.getElementById('imageLightbox');
  if (!lightbox) {
    var lbHtml = '<div id="imageLightbox" class="image-lightbox" onclick="handleLightboxClick(event)">' +
      '<button class="lightbox-nav lightbox-prev" onclick="event.stopPropagation();lightboxPrev()">' +
      '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/></svg>' +
      '</button>' +
      '<img id="lightboxImage" src="" alt="放大图片">' +
      '<button class="lightbox-close" onclick="event.stopPropagation();closeImageLightbox()">' +
      '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>' +
      '</button>' +
      '<button class="lightbox-nav lightbox-next" onclick="event.stopPropagation();lightboxNext()">' +
      '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/></svg>' +
      '</button>' +
      '<div class="lightbox-counter" id="lightboxCounter"></div>' +
      '</div>';
    document.body.insertAdjacentHTML('beforeend', lbHtml);
    lightbox = document.getElementById('imageLightbox');

    // Add keyboard listener
    document.addEventListener('keydown', handleLightboxKeydown);
  }

  updateLightboxImage();
  lightbox.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function updateLightboxImage() {
  var img = document.getElementById('lightboxImage');
  var counter = document.getElementById('lightboxCounter');
  if (img && lightboxImages.length > 0) {
    img.src = lightboxImages[lightboxCurrentIndex];
  }
  if (counter) {
    counter.textContent = (lightboxCurrentIndex + 1) + ' / ' + lightboxImages.length;
  }

  // Update nav button visibility
  var prevBtn = document.querySelector('.lightbox-prev');
  var nextBtn = document.querySelector('.lightbox-next');
  if (prevBtn) prevBtn.style.opacity = lightboxImages.length <= 1 ? '0' : '1';
  if (nextBtn) nextBtn.style.opacity = lightboxImages.length <= 1 ? '0' : '1';
}

function lightboxPrev() {
  if (lightboxImages.length <= 1) return;
  lightboxCurrentIndex = (lightboxCurrentIndex - 1 + lightboxImages.length) % lightboxImages.length;
  updateLightboxImage();
}

function lightboxNext() {
  if (lightboxImages.length <= 1) return;
  lightboxCurrentIndex = (lightboxCurrentIndex + 1) % lightboxImages.length;
  updateLightboxImage();
}

function handleLightboxClick(event) {
  // Close when clicking outside the image
  if (event.target.id === 'imageLightbox' || event.target.tagName === 'IMG') {
    closeImageLightbox();
  }
}

function handleLightboxKeydown(e) {
  var lightbox = document.getElementById('imageLightbox');
  if (!lightbox || !lightbox.classList.contains('active')) return;

  if (e.key === 'ArrowLeft') {
    lightboxPrev();
  } else if (e.key === 'ArrowRight') {
    lightboxNext();
  } else if (e.key === 'Escape') {
    closeImageLightbox();
  }
}

function closeImageLightbox() {
  var lightbox = document.getElementById('imageLightbox');
  if (lightbox) {
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Update budget display (topbar + hero cards)
function updateBudgetDisplay() {
  // Topbar chips (use IDs for reliability)
  var topbarTotal = document.getElementById('topbar-total-budget');
  var topbarSpent = document.getElementById('topbar-actual-spent');
  var topbarRemaining = document.getElementById('topbar-remaining');

  if (topbarTotal) {
    topbarTotal.textContent = formatNumber(projectState.totalBudget) + ' 元';
  }
  if (topbarSpent) {
    topbarSpent.textContent = formatNumber(projectState.actualSpent) + ' 元';
  }

  // Calculate remaining
  var remaining = projectState.totalBudget - projectState.actualSpent;

  if (topbarRemaining) {
    topbarRemaining.textContent = formatNumber(remaining) + ' 元';
    topbarRemaining.className = 'value ' + (remaining < 0 ? 'over' : 'saved');
  }

  // Hero card total budget
  var heroTotal = document.querySelector('.hero-project-card .hero-total-budget');
  if (heroTotal) {
    heroTotal.textContent = formatNumber(projectState.totalBudget);
  }

  // Hero card remaining
  var heroRemaining = document.querySelector('.hero-project-card .hero-remaining');
  if (heroRemaining) {
    heroRemaining.textContent = formatNumber(remaining) + ' 元';
    heroRemaining.style.color = remaining > 0 ? '#86EFAC' : '#FCA5A5';
  }

  // Homepage hero card: 预计花费 + 实际已花
  var heroItems = document.querySelectorAll('.hero-project-card .hero-project-grid .hero-project-item');
  if (heroItems.length >= 2) {
    // heroItems[0]: 预计花费
    if (heroItems[0]) {
      var valEl = heroItems[0].querySelector('.value');
      if (valEl) valEl.textContent = '¥' + formatNumber(projectState.estimatedCost) + ' 元';
    }
    // heroItems[1]: 实际已花
    if (heroItems[1]) {
      var valEl = heroItems[1].querySelector('.value');
      if (valEl) valEl.textContent = '¥' + formatNumber(projectState.actualSpent) + ' 元';
    }
  }

  // Core data cards
  var totalBudgetEl = document.querySelector('[data-budget-type="total"] .stat-value');
  if (totalBudgetEl) {
    totalBudgetEl.textContent = formatNumber(projectState.totalBudget);
  }

  var remainingBudgetEl = document.querySelector('[data-budget-type="remaining"] .stat-value');
  if (remainingBudgetEl) {
    remainingBudgetEl.textContent = formatNumber(remaining);
  }

  // Update settings modal if open
  var settingsActualSpent = document.getElementById('settingsActualSpent');
  if (settingsActualSpent) {
    settingsActualSpent.textContent = formatNumber(projectState.actualSpent) + ' 元';
  }
}

// Open todo completion confirmation
var currentTodoItem = null;
var currentTodoTitle = '';
var currentTodoCategory = '';

function openTodoConfirm(item) {
  currentTodoItem = item;
  currentTodoTitle = item.dataset.title || '';
  currentTodoCategory = item.dataset.category || '';

  // Update confirm modal content
  var confirmText = document.querySelector('.todo-confirm-text');
  if (confirmText) {
    confirmText.textContent = '是否要为"' + currentTodoTitle + '"添加一条装修手册记录？';
  }

  openModal('todoConfirmModal');
}

function confirmTodoDone(action) {
  if (!currentTodoItem) return;

  if (action === 'complete') {
    currentTodoItem.classList.add('done');
    closeModal('todoConfirmModal');
    showToast('已完成待办');
  } else if (action === 'addNote') {
    // Open note modal with pre-filled data
    closeModal('todoConfirmModal');
    currentTodoItem.classList.add('done');

    // Try to open notes page with pre-filled data
    var noteTitle = encodeURIComponent(currentTodoTitle);
    var noteCategory = encodeURIComponent(currentTodoCategory);
    window.location.href = '/decoration/notes?title=' + noteTitle + '&category=' + noteCategory;

    showToast('待办已完成，正在跳转到装修手册');
  } else {
    // Cancel - do nothing
    closeModal('todoConfirmModal');
  }

  currentTodoItem = null;
}

// Add new todo
function addNewTodo() {
  var todoContent = document.getElementById('newTodoContent');
  var todoCategory = document.getElementById('newTodoCategory');
  var todoPriority = document.getElementById('newTodoPriority');
  var todoNote = document.getElementById('newTodoNote');

  var content = todoContent ? todoContent.value.trim() : '';
  var category = todoCategory ? todoCategory.value : '其他';
  var priority = todoPriority ? todoPriority.value : '普通';

  if (!content) {
    showToast('请填写待办内容');
    return;
  }

  // Create new todo item
  var todoList = document.querySelector('.todo-list');
  if (!todoList) return;

  var priorityClass = '';
  if (priority === '紧急') priorityClass = 'priority-urgent';
  else if (priority === '重要') priorityClass = 'priority-important';

  var newTodo = document.createElement('div');
  newTodo.className = 'todo-item animate-in ' + priorityClass;
  newTodo.dataset.category = category;
  newTodo.dataset.title = content;

  newTodo.innerHTML =
    '<div class="todo-checkbox"></div>' +
    '<div class="todo-text">' + content + '</div>' +
    '<span class="todo-tag">' + category + '</span>';

  // Insert at top
  todoList.insertBefore(newTodo, todoList.firstChild);

  // Bind click events
  bindTodoItemEvents(newTodo);

  // Update pending count
  updateTodoCount();

  // Reset form and close modal
  if (todoContent) todoContent.value = '';
  if (todoCategory) todoCategory.selectedIndex = 0;
  if (todoPriority) todoPriority.selectedIndex = 0;
  if (todoNote) todoNote.value = '';

  closeModal('newTodoModal');
  showToast('已添加新待办');
}

// Update todo pending count
function updateTodoCount() {
  var todos = document.querySelectorAll('.todo-item:not(.done)');
  var count = todos.length;

  var countBadge = document.querySelector('.todo-section-badge');
  if (countBadge) {
    countBadge.textContent = count + ' 项待处理';
  }
}

// Bind todo item events
function bindTodoItemEvents(item) {
  var checkbox = item.querySelector('.todo-checkbox');
  if (checkbox) {
    checkbox.addEventListener('click', function(e) {
      e.stopPropagation();
      if (!item.classList.contains('done')) {
        openTodoConfirm(item);
      } else {
        item.classList.remove('done');
      }
    });
  }

  item.addEventListener('click', function(e) {
    if (!e.target.closest('.todo-checkbox')) {
      if (!item.classList.contains('done')) {
        openTodoConfirm(item);
      }
    }
  });
}

// Category card navigation
var categoryAnchors = {
  '中央空调': 'air-conditioner',
  '门窗': 'windows',
  '瓷砖': 'tiles',
  '地板': 'floor',
  '水电': 'water-electricity',
  '木工': 'woodwork',
  '智能家居': 'smart-home',
  '全屋定制': 'custom-cabinet'
};

function navigateToCategory(category) {
  var anchor = categoryAnchors[category];
  if (anchor) {
    window.location.href = '/decoration/compare#' + anchor;
  } else {
    window.location.href = '/decoration/compare';
    showToast('已进入分类比较，后续可定位到具体分类');
  }
}

// Table row selection
function selectRow(row) {
  var table = row.closest('table');
  if (table) {
    table.querySelectorAll('tbody tr').forEach(function(r) {
      r.classList.remove('selected');
      var radio = r.querySelector('.radio-circle');
      if (radio) {
        radio.classList.remove('checked');
      }
    });
    row.classList.add('selected');
    var radio = row.querySelector('.radio-circle');
    if (radio) {
      radio.classList.add('checked');
    }
  }
}

// Toggle TOC section (for manual page)
function toggleTocSection(btn) {
  var section = btn.closest('.manual-toc-section');
  if (section) {
    section.classList.toggle('open');
    btn.classList.toggle('active');
  }
}

// Toggle chapter (for manual page)
function toggleChapter(header) {
  var chapter = header.closest('.manual-chapter');
  if (chapter) {
    chapter.classList.toggle('open');
  }
}

// Go to progress page
function goToProgress() {
  window.location.href = '/decoration/progress';
}

// Go to notes page
function goToNotes() {
  window.location.href = '/decoration/notes';
}

function goToCompareItem(compareItemId, categoryId) {
  // Navigate to the appropriate compare detail page based on category
  if (categoryId) {
    var catName = getCategoryNameById(categoryId);
    if (catName === '中央空调') {
      window.location.href = '/decoration/compare/air-conditioner';
      return;
    }
  }
  showToast('该分类详情页尚未接入');
}

// ── Kanban Card Edit ──

// Stage name map for card display
var stageNameMap = {
  'design': '设计',
  'demolition': '拆改',
  'water': '水电',
  'mud': '泥工',
  'wood': '木工',
  'paint': '油漆',
  'install': '安装',
  'soft': '软装'
};

// Status label & color map
var statusConfig = {
  'pending':  { label: '待开始', color: '#9CA3AF', cssClass: 'status-pending' },
  'ongoing':  { label: '进行中', color: 'var(--accent-orange)', cssClass: 'status-ongoing' },
  'review':   { label: '待验收', color: 'var(--accent-yellow)', cssClass: 'status-review' },
  'done':     { label: '已完成', color: 'var(--accent-green)', cssClass: 'status-done' }
};

// Bind click-to-edit on all kanban cards
function bindKanbanCardEvents() {
  document.querySelectorAll('.kanban-card[data-task-id]').forEach(function(card) {
    // Skip if already bound
    if (card.dataset.editBound === '1') return;
    card.dataset.editBound = '1';

    card.addEventListener('click', function(e) {
      // Don't open edit modal if clicking a button/link inside the card
      var target = e.target;
      if (target.closest('button') || target.closest('a')) return;
      openEditTaskModal(card);
    });
  });
}

// Open edit modal and populate with card data
function openEditTaskModal(card) {
  document.getElementById('editTaskId').value = card.dataset.taskId || '';
  document.getElementById('editTaskTitle').value = card.dataset.title || '';
  document.getElementById('editTaskStage').value = card.dataset.stage || 'design';
  document.getElementById('editTaskStatus').value = card.dataset.status || 'pending';
  document.getElementById('editTaskBudget').value = card.dataset.budget || '';
  document.getElementById('editTaskActual').value = card.dataset.actual || '';
  document.getElementById('editTaskOwner').value = card.dataset.owner || '';
  document.getElementById('editTaskNote').value = card.dataset.note || '';
  document.getElementById('editTaskAddNote').checked = false;
  openModal('editTaskModal');
}

// Save edited task
function saveEditedTask() {
  var taskId = document.getElementById('editTaskId').value;
  var card = document.querySelector('.kanban-card[data-task-id="' + taskId + '"]');

  if (!card) {
    showToast('未找到任务卡片');
    return;
  }

  var title = document.getElementById('editTaskTitle').value.trim();
  var stage = document.getElementById('editTaskStage').value;
  var status = document.getElementById('editTaskStatus').value;
  var budget = document.getElementById('editTaskBudget').value.trim();
  var actual = document.getElementById('editTaskActual').value.trim();
  var owner = document.getElementById('editTaskOwner').value.trim();
  var note = document.getElementById('editTaskNote').value.trim();
  var addNote = document.getElementById('editTaskAddNote').checked;

  if (!title) {
    showToast('请填写任务名称');
    return;
  }

  var oldStage = card.dataset.stage;
  var oldStatus = card.dataset.status;

  // Update dataset
  card.dataset.title = title;
  card.dataset.stage = stage;
  card.dataset.status = status;
  card.dataset.budget = budget;
  card.dataset.actual = actual;
  card.dataset.owner = owner;
  card.dataset.note = note;

  // Update card visual
  var config = statusConfig[status] || statusConfig['pending'];
  var stageName = stageNameMap[stage] || stage;

  card.innerHTML =
    '<div class="kanban-card-title">' + title + '</div>' +
    '<div class="kanban-card-meta">' +
      '<span class="kanban-chip">' + stageName + '</span>' +
      (budget ? '<span class="kanban-chip">¥' + formatNumber(parseInt(budget) || 0) + '</span>' : '') +
    '</div>' +
    '<div class="kanban-card-status-label" style="font-size:.6875rem;color:' + config.color + ';margin-bottom:6px;">' + config.label + '</div>' +
    (status === 'ongoing' ? '<div style="margin-bottom:8px;"><div class="progress-bar-track" style="height:3px;"><div class="progress-bar-fill" style="width:50%;"></div></div></div>' : '') +
    '<div class="kanban-card-footer">' +
      '<span>' + (owner || '未填写') + (status === 'ongoing' ? ' · 50%' : '') + '</span>' +
      '<span class="kanban-card-link" onclick="goToNotes()">📖 手册</span>' +
    '</div>';

  // Re-apply click-to-edit after innerHTML replacement
  card.dataset.editBound = '0';
  bindKanbanCardEvents();

  // Re-apply stopPropagation on new buttons
  card.querySelectorAll('button, a').forEach(function(el) {
    el.addEventListener('click', function(e) { e.stopPropagation(); });
  });

  // Move card to correct container if stage or status changed
  if (stage !== oldStage || status !== oldStatus) {
    var targetContainer = document.querySelector('[data-stage="' + stage + '"][data-status="' + status + '"]');
    if (targetContainer) {
      targetContainer.appendChild(card);
    }
    // Update column counts
    updateKanbanColumnCounts();
    // Update group header counts
    updateKanbanGroupCounts();
  }

  closeModal('editTaskModal');

  if (addNote) {
    showToast('任务已更新，可同步到装修手册');
  } else {
    showToast('任务已更新');
  }
}

// Update column task counts
function updateKanbanColumnCounts() {
  document.querySelectorAll('.kanban-column').forEach(function(col) {
    var cards = col.querySelectorAll('.kanban-card');
    var countEl = col.querySelector('.kanban-col-count');
    if (countEl) countEl.textContent = cards.length;
  });
}

// Update group total task counts
function updateKanbanGroupCounts() {
  document.querySelectorAll('.kanban-group').forEach(function(group) {
    var cards = group.querySelectorAll('.kanban-card');
    var countEl = group.querySelector('.kanban-group-count');
    if (countEl) countEl.textContent = cards.length + ' 个任务';
  });
}

// ── Save Progress Task (新建任务) ──

// Generate a unique task ID
function generateTaskId() {
  return 'task-' + Date.now() + '-' + Math.floor(Math.random() * 1000);
}

// Save note entry (装修手册)
function saveNoteEntry() {
  var title = document.getElementById('noteTitle');
  var content = document.getElementById('noteContent');
  var stage = document.getElementById('noteStage');
  var tags = document.getElementById('noteTags');
  var source = document.getElementById('noteSource');
  
  title = title ? title.value.trim() : '';
  content = content ? content.value.trim() : '';
  stage = stage ? stage.value : '设计阶段';
  tags = tags ? tags.value.trim() : '';
  source = source ? source.value.trim() : '';
  
  if (!title) {
    showToast('请填写记录标题');
    return;
  }
  
  // Find the first open chapter body or the first chapter body
  var target = document.querySelector('.manual-chapter.open .manual-chapter-body') 
            || document.querySelector('.manual-chapter .manual-chapter-body');
  
  if (target) {
    var entry = document.createElement('div');
    entry.className = 'manual-entry';
    
    var today = new Date().toISOString().slice(0, 10);
    
    var tagsHtml = '';
    if (tags && tags.trim()) {
      var tagList = tags.split(/[，,]/).filter(function(t) { return t && t.trim(); });
      if (tagList.length > 0) {
        tagsHtml = '<div class="manual-entry-tags">' + 
          tagList.map(function(t) { 
            return '<span class="note-tag">' + t.trim() + '</span>'; 
          }).join('') + 
          '</div>';
      }
    }
    
    var sourceHtml = source ? '<div style="font-size:.75rem;color:var(--text-muted);margin-top:6px;">来源: ' + source + '</div>' : '';
    
    entry.innerHTML =
      '<div class="manual-entry-header">' +
        '<span class="manual-entry-date">' + today + '</span>' +
      '</div>' +
      '<div class="manual-entry-title">' + title + '</div>' +
      '<div class="manual-entry-content">' + (content || '暂无内容') + '</div>' +
      sourceHtml +
      (tagsHtml ? tagsHtml : '');
    
    // Insert before the "添加内容" button if exists
    var addBtn = target.querySelector('.manual-add-btn, .manual-add-btn[style*="margin-top"]');
    if (addBtn) {
      target.insertBefore(entry, addBtn);
    } else {
      target.appendChild(entry);
    }
  }
  
  closeModal('noteEntryModal');
  showToast('已添加装修手册记录');
  
  // Reset form
  var inputs = document.querySelectorAll('#noteEntryModal input, #noteEntryModal textarea, #noteEntryModal select');
  inputs.forEach(function(input) {
    if (input.tagName === 'SELECT') {
      input.selectedIndex = 0;
    } else {
      input.value = '';
    }
  });
}

// Save progress task (via API)
function saveProgressTask() {
  var title = document.getElementById('taskTitle');
  var status = document.getElementById('taskStatus');
  var stage = document.getElementById('taskStage');
  var budget = document.getElementById('taskBudget');
  var actual = document.getElementById('taskActual');
  var owner = document.getElementById('taskOwner');
  var note = document.getElementById('taskNote');

  title = title ? title.value.trim() : '';
  status = status ? status.value : 'pending';
  stage = stage ? stage.value : 'design';
  budget = budget ? budget.value.trim() : '0';
  actual = actual ? actual.value.trim() : '0';
  owner = owner ? owner.value.trim() : '';
  note = note ? note.value.trim() : '';

  if (!title) {
    showToast('请填写任务名称');
    return;
  }

  var payload = {
    title: title,
    stage: stage,
    status: status,
    budget_amount: parseInt(budget) || 0,
    actual_amount: parseInt(actual) || 0,
    owner: owner,
    note: note,
    category_id: parseInt(document.getElementById('taskCategory').value) || null
  };

  fetch(apiBase + '/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    closeModal('taskModal');
    showToast('已添加装修任务');
    // Reset form
    var inputs = document.querySelectorAll('#taskModal input, #taskModal textarea, #taskModal select');
    inputs.forEach(function(input) {
      if (input.tagName === 'SELECT') input.selectedIndex = 0;
      else input.value = '';
    });
    loadTasksFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to save task:', err);
    showToast('保存失败');
  });
}

// Load tasks from API
function loadTasksFromAPI() {
  fetch(apiBase + '/api/tasks')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') {
        return;
      }
      progressTasks = data.data || [];
      renderAllKanbanCards();
      updateProgressSummary();
      renderHomeTodoList(); // update home page todo list
    })
    .catch(function(err) {
      console.error('Failed to load tasks:', err);
    });
}

// Progress task data
var progressTasks = [];

// Render all kanban cards from API data
function renderAllKanbanCards() {
  // Clear existing cards (keep empty tips)
  document.querySelectorAll('.kanban-card[data-task-id]').forEach(function(card) {
    card.remove();
  });

  progressTasks.forEach(function(task) {
    renderKanbanCard(task);
  });

  // Update counts
  updateKanbanColumnCounts();
  updateKanbanGroupCounts();
}

// Render a single kanban card from task data
function renderKanbanCard(task) {
  var stageName = stageNameMap[task.stage] || task.stage || 'design';
  var config = statusConfig[task.status] || statusConfig['pending'];
  var targetContainer = document.querySelector('[data-stage="' + task.stage + '"][data-status="' + task.status + '"]');
  if (!targetContainer) return;

  var card = document.createElement('div');
  card.className = 'kanban-card';
  card.dataset.taskId = task.id;
  card.dataset.title = task.title || '';
  card.dataset.stage = task.stage || 'design';
  card.dataset.status = task.status || 'pending';
  card.dataset.budget = task.budget_amount || '';
  card.dataset.actual = task.actual_amount || '';
  card.dataset.owner = task.owner || '';
  card.dataset.note = task.note || '';
  card.dataset.categoryId = task.category_id || '';
  card.dataset.editBound = '1';

  var catLabel = getCategoryNameById(task.category_id);
  card.innerHTML =
    '<div class="kanban-card-title">' + (task.title || '') + '</div>' +
    '<div class="kanban-card-meta">' +
      '<span class="kanban-chip">' + stageName + '</span>' +
      (task.budget_amount ? '<span class="kanban-chip">¥' + formatNumber(task.budget_amount) + '</span>' : '') +
      (catLabel ? '<span class="kanban-chip">' + catLabel + '</span>' : '') +
    '</div>' +
    '<div class="kanban-card-status-label" style="font-size:.6875rem;color:' + config.color + ';margin-bottom:6px;">' + config.label + '</div>' +
    (task.status === 'ongoing' ? '<div style="margin-bottom:8px;"><div class="progress-bar-track" style="height:3px;"><div class="progress-bar-fill" style="width:50%;"></div></div></div>' : '') +
    '<div class="kanban-card-footer">' +
      '<span>' + (task.owner || '未填写') + (task.status === 'ongoing' ? ' · 50%' : '') + '</span>' +
      '<span class="kanban-card-link" onclick="goToNotes()">📖 手册</span>' +
    '</div>';

  card.addEventListener('click', function(e) {
    if (e.target.closest('button') || e.target.closest('a')) return;
    openEditTaskModal(card);
  });
  card.querySelectorAll('button, a').forEach(function(el) {
    el.addEventListener('click', function(e) { e.stopPropagation(); });
  });

  // Remove empty tip
  var emptyTip = targetContainer.querySelector('.kanban-empty-tip');
  if (emptyTip) emptyTip.remove();
  targetContainer.classList.remove('kanban-cards-empty');

  targetContainer.insertBefore(card, targetContainer.firstChild);
}

// Update progress overview summary
function updateProgressSummary() {
  var pending = 0, ongoing = 0, review = 0, done = 0;
  progressTasks.forEach(function(t) {
    if (t.status === 'pending') pending++;
    else if (t.status === 'ongoing') ongoing++;
    else if (t.status === 'review') review++;
    else if (t.status === 'done') done++;
  });
  var total = progressTasks.length;
  var percent = total > 0 ? Math.round(done / total * 100) : 0;

  // Update progress overview header
  var overviewValue = document.querySelector('.progress-overview-value');
  if (overviewValue) overviewValue.textContent = '约 ' + percent + '%';
  var progressBarFill = document.querySelector('.progress-overview .progress-bar-fill');
  if (progressBarFill) progressBarFill.style.width = percent + '%';
  var overviewSubtitle = document.querySelector('.progress-overview-header > div > div:last-child');
  if (overviewSubtitle && overviewSubtitle.style.fontSize === '.75rem') {
    overviewSubtitle.textContent = '待开始 ' + pending + ' · 进行中 ' + ongoing + ' · 待验收 ' + review + ' · 已完成 ' + done;
  }
}

// Open edit modal from card
function openEditTaskModalFromCard(card) {
  document.getElementById('editTaskId').value = card.dataset.taskId || '';
  document.getElementById('editTaskTitle').value = card.dataset.title || '';
  document.getElementById('editTaskStage').value = card.dataset.stage || 'design';
  document.getElementById('editTaskStatus').value = card.dataset.status || 'pending';
  document.getElementById('editTaskBudget').value = card.dataset.budget || '';
  document.getElementById('editTaskActual').value = card.dataset.actual || '';
  document.getElementById('editTaskOwner').value = card.dataset.owner || '';
  document.getElementById('editTaskNote').value = card.dataset.note || '';
  document.getElementById('editTaskAddNote').checked = false;
  var catSelect = document.getElementById('editTaskCategory');
  if (catSelect) {
    fillCategorySelects();
    catSelect.value = card.dataset.categoryId || '';
  }
  // 加载关联笔记
  loadTaskNotes(card.dataset.taskId || '');
  openModal('editTaskModal');
}

// 加载任务关联的笔记
function loadTaskNotes(taskId) {
  var container = document.getElementById('editTaskNotes');
  if (!container) return;

  if (!taskId) {
    container.innerHTML = '<span style="color:var(--text-muted);font-size:.8125rem;">暂无关联笔记</span>';
    return;
  }

  container.innerHTML = '<span style="color:var(--text-muted);font-size:.8125rem;">加载中...</span>';

  fetch(apiBase + '/api/tasks/' + taskId + '/notes')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'success' && data.data && data.data.length > 0) {
        var html = '';
        data.data.forEach(function(note) {
          var platformInfo = getPlatformInfo(note.source_url);
          var badge = '';
          if (platformInfo) {
            badge = '<span style="font-size:10px;">' + platformInfo.icon + '</span>';
          }
          html += '<span class="note-link-chip" style="cursor:pointer;background:' + (platformInfo ? platformInfo.bg : '#F3F4F6') + ';color:' + (platformInfo ? platformInfo.color : '#6B7280') + ';" ' +
                  'onclick="window.open(\'/decoration/notes\', \'_blank\')" title="' + (note.title || '') + '">' +
                  badge + ' ' + (note.title || '笔记') + '</span>';
        });
        container.innerHTML = html;
      } else {
        container.innerHTML = '<span style="color:var(--text-muted);font-size:.8125rem;">暂无关联笔记</span>';
      }
    })
    .catch(function() {
      container.innerHTML = '<span style="color:var(--text-muted);font-size:.8125rem;">加载失败</span>';
    });
}

// Save edited task (via API)
function saveEditedTask() {
  var taskId = document.getElementById('editTaskId').value;
  if (!taskId) {
    showToast('未找到任务');
    return;
  }

  var title = document.getElementById('editTaskTitle').value.trim();
  var stage = document.getElementById('editTaskStage').value;
  var status = document.getElementById('editTaskStatus').value;
  var budget = document.getElementById('editTaskBudget').value.trim();
  var actual = document.getElementById('editTaskActual').value.trim();
  var owner = document.getElementById('editTaskOwner').value.trim();
  var taskNote = document.getElementById('editTaskNote').value.trim();
  var addNote = document.getElementById('editTaskAddNote').checked;

  if (!title) {
    showToast('请填写任务名称');
    return;
  }

  var payload = {
    title: title,
    stage: stage,
    status: status,
    budget_amount: parseInt(budget) || 0,
    actual_amount: parseInt(actual) || 0,
    owner: owner,
    note: taskNote,
    category_id: parseInt(document.getElementById('editTaskCategory').value) || null
  };

  fetch(apiBase + '/api/tasks/' + taskId, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    closeModal('editTaskModal');

    // 如果勾选了"状态更新后添加手册记录"，创建一条手册记录
    if (addNote) {
      var notePayload = {
        title: '任务状态更新：' + title,
        content: '任务「' + title + '」状态已更新为「' + getStatusName(status) + '」。',
        stage: stage,
        task_id: parseInt(taskId),
        tags: ['任务进度', '自动记录']
      };
      fetch(apiBase + '/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(notePayload)
      })
      .then(function(res) { return res.json(); })
      .then(function(noteData) {
        if (noteData.status === 'success') {
          showToast('任务已更新，并已添加装修手册记录');
        } else {
          showToast('任务已更新，但手册记录创建失败');
        }
      })
      .catch(function(err) {
        console.error('Failed to create note:', err);
        showToast('任务已更新，但手册记录创建失败');
      });
    } else {
      showToast('任务已更新');
    }

    loadTasksFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to save edited task:', err);
    showToast('保存失败');
  });
}

// 获取状态中文名称
function getStatusName(status) {
  var statusMap = {
    'pending': '待处理',
    'ongoing': '进行中',
    'review': '待验收',
    'done': '已完成'
  };
  return statusMap[status] || status;
}

// 从编辑弹窗删除任务
function deleteTaskFromEdit() {
  var taskId = document.getElementById('editTaskId').value;
  if (!taskId) return;
  if (!confirm('确认删除该装修任务吗？')) return;

  fetch(apiBase + '/api/tasks/' + taskId, { method: 'DELETE' })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '删除失败');
      return;
    }
    closeModal('editTaskModal');
    // 从看板移除卡片（使用字符串比较）
    var card = document.querySelector('.kanban-card[data-task-id="' + taskId + '"]');
    if (card) card.remove();
    // 从内存数据移除
    progressTasks = progressTasks.filter(function(t) { return String(t.id) !== taskId; });
    // 重新计算统计
    updateProgressSummary();
    showToast('任务已删除');
  })
  .catch(function(err) {
    console.error('Failed to delete task:', err);
    showToast('删除失败');
  });
}

// Override openEditTaskModal to use card dataset
var _originalOpenEditTaskModal = openEditTaskModal;
function openEditTaskModal(card) {
  if (typeof card === 'string') {
    card = document.querySelector('.kanban-card[data-task-id="' + card + '"]');
  }
  if (!card) return;
  openEditTaskModalFromCard(card);
}

// ═══════════════════════════════════════════
// 分类比较页面 (/decoration/compare)
// ═══════════════════════════════════════════

// ── Category Group Data (loaded from API)
var categoryGroups = [];

// ── Sub-category Data (empty by default — no fake data)
var subCategories = [];

// ── State ──
var currentGroupFilter = 'all';  // 'all' or group id
var currentView = 'card';         // 'card' or 'table'

// ── API Base URL ──
var apiBase = '/decoration';

// ── Lookup Data (统一关联数据缓存) ──
var renovaLookupData = {
  categories: [],
  tasks: [],
  compare_items: [],
  notes: []
};

function loadLookupData(callback) {
  fetch(apiBase + '/api/lookup-data')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'success' && data.data) {
        renovaLookupData = data.data;
      }
      if (callback) callback();
    })
    .catch(function() {
      // silently fail, leave empty arrays
      if (callback) callback();
    });
}

function fillCategorySelects() {
  var selects = document.querySelectorAll('[data-fill-category]');
  selects.forEach(function(sel) {
    var currentVal = sel.value;
    sel.innerHTML = '<option value="">不关联</option>';
    var data = window.renovaLookupData.categories || [];
    if (data.length === 0) {
      sel.innerHTML = '<option value="">暂无可关联数据</option>';
    } else {
      data.forEach(function(cat) {
        var label = cat.group_name ? cat.name + ' · ' + cat.group_name : cat.name;
        sel.innerHTML += '<option value="' + cat.id + '">' + label + '</option>';
      });
    }
    if (currentVal) sel.value = currentVal;
  });
}

function fillTaskSelects() {
  var selects = document.querySelectorAll('[data-fill-task]');
  selects.forEach(function(sel) {
    var currentVal = sel.value;
    sel.innerHTML = '<option value="">不关联</option>';
    var data = window.renovaLookupData.tasks || [];
    if (data.length === 0) {
      sel.innerHTML = '<option value="">暂无可关联数据</option>';
    } else {
      data.forEach(function(task) {
        sel.innerHTML += '<option value="' + task.id + '">' + task.title + '</option>';
      });
    }
    if (currentVal) sel.value = currentVal;
  });
}

function fillCompareItemSelects() {
  var selects = document.querySelectorAll('[data-fill-compare-item]');
  selects.forEach(function(sel) {
    var currentVal = sel.value;
    sel.innerHTML = '<option value="">不关联</option>';
    var data = window.renovaLookupData.compare_items || [];
    if (data.length === 0) {
      sel.innerHTML = '<option value="">暂无可关联数据</option>';
    } else {
      data.forEach(function(item) {
        var label = item.brand + (item.model ? ' ' + item.model : '');
        label += item.category_name ? ' (' + item.category_name + ')' : '';
        sel.innerHTML += '<option value="' + item.id + '">' + label + '</option>';
      });
    }
    if (currentVal) sel.value = currentVal;
  });
}

function getCategoryNameById(id) {
  if (!id) return '';
  var found = renovaLookupData.categories.find(function(c) { return c.id == id; });
  return found ? found.name : '';
}

function getTaskTitleById(id) {
  if (!id) return '';
  var found = renovaLookupData.tasks.find(function(t) { return t.id == id; });
  return found ? found.title : '';
}

function getCompareItemLabelById(id) {
  if (!id) return '';
  var found = renovaLookupData.compare_items.find(function(item) { return item.id == id; });
  if (!found) return '';
  return found.brand + (found.model ? ' ' + found.model : '');
}

// ── Load Category Groups from API ──
function loadCategoryGroupsFromAPI() {
  fetch(apiBase + '/api/groups')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error' && data.message === '请先创建装修项目') {
        // No project exists, show message
        var grid = document.getElementById('categoryGroupGrid');
        if (grid) {
          grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;padding:32px;text-align:center;">' +
            '<p>请先创建装修项目</p>' +
            '<p style="margin-top:8px;font-size:.875rem;color:var(--text-muted);">在首页总览中点击"创建装修项目"按钮</p>' +
            '<button class="btn btn-primary" onclick="location.href=\'/decoration\'" style="margin-top:16px;">去首页总览</button></div>';
        }
        // Disable add button
        var btnAddGroup = document.getElementById('btnAddGroup');
        if (btnAddGroup) { btnAddGroup.disabled = true; btnAddGroup.style.opacity = '0.5'; }
        var btnAddSubcat = document.getElementById('btnAddSubcat');
        if (btnAddSubcat) { btnAddSubcat.disabled = true; btnAddSubcat.style.opacity = '0.5'; }
        return;
      }
      categoryGroups = data.data || [];
      renderCategoryGroups();
      renderFilterPills();
      fillGroupSelect();
      // Load sub-categories after groups are loaded
      loadCategoriesFromAPI();
    })
    .catch(function(err) {
      console.error('Failed to load category groups:', err);
      showToast('加载分类大类失败');
    });
}

// ── Load Sub-categories from API ──
function loadCategoriesFromAPI() {
  fetch(apiBase + '/api/categories')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') {
        showToast(data.message || '加载子分类失败');
        return;
      }
      subCategories = data.data || [];
      var filtered = getFilteredSubcats();
      renderSubcatCards(filtered);
      renderSubcatTable(filtered);
    })
    .catch(function(err) {
      console.error('Failed to load categories:', err);
      showToast('加载子分类失败');
    });
}

// ── Group Helpers ──
function getGroupById(id) {
  // Handle both numeric (from API) and string (legacy) IDs
  var numId = parseInt(id, 10);
  return categoryGroups.find(function(g) { return g.id === id || g.id === numId; });
}
function getGroupName(id) {
  var g = getGroupById(id);
  return g ? g.name : (id || '未知');
}
function getSubcatCountByGroup(groupId) {
  var numId = parseInt(groupId, 10);
  return subCategories.filter(function(c) { return c.group_id === numId || c.group_id === groupId; }).length;
}

// ── Status Helpers ──
var subcatStatusConfig = {
  'not_started':    { label: '未开始',   cssClass: 'status-not-started', shortLabel: '未开始' },
  'comparing':      { label: '比价中',   cssClass: 'status-comparing',    shortLabel: '比价中' },
  'selected':       { label: '已选方案', cssClass: 'status-selected',     shortLabel: '已选' },
  'ongoing':        { label: '进行中',   cssClass: 'status-ongoing',      shortLabel: '进行中' },
  'pending_confirm':{ label: '待确认',   cssClass: 'status-pending',      shortLabel: '待确认' }
};
function getStatusLabel(status) {
  var s = subcatStatusConfig[status] || subcatStatusConfig['not_started'];
  return s.label;
}

// ── Render: Category Groups ──
function renderCategoryGroups() {
  var grid = document.getElementById('categoryGroupGrid');
  if (!grid) return;

  grid.innerHTML = '';

  if (categoryGroups.length === 0) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;padding:32px;text-align:center;">' +
      '<p>暂无分类大类<br>请先添加设备系统、主材选择、施工项目等分类大类。</p>' +
      '<button class="btn btn-primary" onclick="openGroupModal()" style="margin-top:16px;">' +
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>' +
      '新增大类</button></div>';
    return;
  }

  categoryGroups.forEach(function(g) {
    if (!g.is_enabled) return;
    var count = getSubcatCountByGroup(g.id);
    var isActive = currentGroupFilter === g.id || currentGroupFilter === String(g.id);
    var card = document.createElement('div');
    card.className = 'category-group-card animate-in' + (isActive ? ' active' : '');
    card.dataset.groupId = g.id;
    card.innerHTML =
      '<div class="category-group-icon" style="background:rgba(234,88,12,.1);color:var(--accent-orange);font-size:1.25rem;">' + g.icon + '</div>' +
      '<div class="category-group-info">' +
        '<div class="category-group-name">' + g.name + '</div>' +
        '<div class="category-group-count">' + count + ' 个子分类</div>' +
      '</div>' +
      '<button class="cat-action-btn cat-edit" title="编辑" onclick="event.stopPropagation();openGroupModal(\'' + g.id + '\')">' +
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/></svg>' +
      '</button>' +
      '<button class="cat-action-btn cat-delete" title="删除" onclick="event.stopPropagation();deleteGroup(\'' + g.id + '\')">' +
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg>' +
      '</button>';
    card.addEventListener('click', function(e) {
      if (e.target.closest('.cat-action-btn')) return;
      setGroupFilter(g.id);
    });
    grid.appendChild(card);
  });
}

// ── Render: Filter Pills ──
function renderFilterPills() {
  var container = document.getElementById('filterPills');
  if (!container) return;

  container.innerHTML = '';

  // All pill
  var allPill = document.createElement('div');
  allPill.className = 'sub-cat-pill' + (currentGroupFilter === 'all' ? ' active' : '');
  allPill.dataset.group = 'all';
  allPill.innerHTML = '全部 <span class="count">' + subCategories.length + '</span>';
  allPill.addEventListener('click', function() { setGroupFilter('all'); });
  container.appendChild(allPill);

  // Group pills
  categoryGroups.forEach(function(g) {
    if (!g.is_enabled) return;
    var count = getSubcatCountByGroup(g.id);
    var pill = document.createElement('div');
    pill.className = 'sub-cat-pill' + (currentGroupFilter === g.id ? ' active' : '');
    pill.dataset.group = g.id;
    pill.innerHTML = g.name + ' <span class="count">' + count + '</span>';
    pill.addEventListener('click', function() { setGroupFilter(g.id); });
    container.appendChild(pill);
  });
}

// ── Set Group Filter ──
function setGroupFilter(groupId) {
  currentGroupFilter = groupId;
  var filtered = getFilteredSubcats();

  // Update title & count
  var title = document.getElementById('subcatTitle');
  var countEl = document.getElementById('subcatCount');
  if (title) {
    var label = groupId === 'all' ? '所有子分类' : getGroupName(groupId);
    title.childNodes[0].textContent = label + ' ';
  }
  if (countEl) {
    countEl.textContent = '(' + filtered.length + ')';
  }

  // Sync group cards
  document.querySelectorAll('#categoryGroupGrid .category-group-card').forEach(function(card) {
    card.classList.toggle('active', card.dataset.groupId === groupId);
  });

  renderFilterPills();
  renderSubcatCards(filtered);
  renderSubcatTable(filtered);
}

// ── Get Filtered Subcats ──
function getFilteredSubcats() {
  if (currentGroupFilter === 'all') return subCategories;
  var numFilter = parseInt(currentGroupFilter, 10);
  return subCategories.filter(function(c) { return c.group_id === numFilter || c.group_id === currentGroupFilter; });
}

// ── Render: Sub-category Cards ──
function renderSubcatCards(items) {
  var grid = document.getElementById('subcatCardGrid');
  var emptyEl = document.getElementById('subcatCardEmpty');
  if (!grid) return;
  grid.innerHTML = '';

  if (items.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    return;
  }
  if (emptyEl) emptyEl.style.display = 'none';

  items.forEach(function(c) {
    var statusCfg = subcatStatusConfig[c.status] || subcatStatusConfig['not_started'];
    var group = getGroupById(c.group_id);
    var groupColor = group ? 'rgba(234,88,12,.1)' : 'rgba(168,162,158,.12)';
    var budgetStr = c.budget ? '¥' + formatNumber(c.budget) : '未填写';

    var card = document.createElement('div');
    card.className = 'category-card animate-in';
    card.dataset.catId = c.id;
    card.innerHTML =
      '<span class="category-status-tag status-tag ' + statusCfg.cssClass + '">' + statusCfg.label + '</span>' +
      '<div class="category-icon" style="background:' + groupColor + ';color:var(--accent-orange);font-size:1.25rem;">' + (group ? group.icon : '📦') + '</div>' +
      '<div class="category-info">' +
        '<div class="category-name">' + c.name + '</div>' +
        '<div class="category-desc">' + (c.description || '待开始') + '</div>' +
      '</div>' +
      '<div class="category-budget">' + budgetStr + '</div>' +
      '<div class="category-card-actions">' +
        '<button class="cat-action-btn cat-edit" title="编辑" onclick="event.stopPropagation();openSubcatModal(\'' + c.id + '\')">' +
          '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/></svg>' +
        '</button>' +
        '<button class="cat-action-btn cat-delete" title="删除" onclick="event.stopPropagation();deleteSubcat(\'' + c.id + '\')">' +
          '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg>' +
        '</button>' +
      '</div>';

    // Card body click → navigate
    card.addEventListener('click', function() {
      navigateToCategoryDetail(c.id, c.name);
    });

    grid.appendChild(card);
  });
}

// ── Render: Sub-category Table ──
function renderSubcatTable(items) {
  var tbody = document.getElementById('subcatTableBody');
  var emptyEl = document.getElementById('subcatTableEmpty');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (items.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    return;
  }
  if (emptyEl) emptyEl.style.display = 'none';

  items.forEach(function(c) {
    var statusCfg = subcatStatusConfig[c.status] || subcatStatusConfig['not_started'];
    var budgetStr = c.budget ? '¥' + formatNumber(c.budget) : '—';
    var viewModeLabel = c.view_mode === 'card' ? '卡片模式' : c.view_mode === 'table' ? '表格模式' : '清单模式';

    var row = document.createElement('tr');
    row.innerHTML =
      '<td><strong>' + c.name + '</strong></td>' +
      '<td><span class="kanban-chip">' + getGroupName(c.group_id) + '</span></td>' +
      '<td><span class="status-tag ' + statusCfg.cssClass + '">' + statusCfg.label + '</span></td>' +
      '<td style="font-weight:600;">' + budgetStr + '</td>' +
      '<td style="text-align:center;">—</td>' +
      '<td>' + viewModeLabel + '</td>' +
      '<td style="text-align:center;">' +
        '<button class="btn btn-sm btn-ghost" onclick="navigateToCategoryDetail(\'' + c.id + '\',\'' + c.name + '\')">进入</button>' +
        '<button class="btn btn-sm btn-secondary" style="margin-left:4px;" onclick="openSubcatModal(\'' + c.id + '\')">编辑</button>' +
        '<button class="btn btn-sm btn-ghost" style="margin-left:4px;color:var(--accent-red);" onclick="deleteSubcat(\'' + c.id + '\')">删除</button>' +
      '</td>';

    // Add row click handler for central air conditioner
    if (c.name === '中央空调') {
      row.addEventListener('click', function(e) {
        // Don't navigate if clicking on buttons
        if (e.target.closest('button')) return;
        navigateToCategoryDetail(c.id, c.name);
      });
      row.style.cursor = 'pointer';
    }

    tbody.appendChild(row);
  });
}

// ── View Toggle ──
function setView(view) {
  currentView = view;
  var cardContainer = document.getElementById('cardViewContainer');
  var tableContainer = document.getElementById('tableViewContainer');
  var cardTab = document.getElementById('btnCardView');
  var tableTab = document.getElementById('btnTableView');

  if (view === 'card') {
    if (cardContainer) cardContainer.style.display = '';
    if (tableContainer) tableContainer.style.display = 'none';
    if (cardTab) cardTab.classList.add('active');
    if (tableTab) tableTab.classList.remove('active');
  } else {
    if (cardContainer) cardContainer.style.display = 'none';
    if (tableContainer) tableContainer.style.display = '';
    if (cardTab) cardTab.classList.remove('active');
    if (tableTab) tableTab.classList.add('active');
  }
}

// ── Navigate to Category Detail ──
function navigateToCategoryDetail(catId, catName) {
  // Match by id or by name "中央空调"
  if (catId === 'c-ac' || catName === '中央空调') {
    window.location.href = '/decoration/compare/air-conditioner';
  } else {
    showToast('该分类详情后续接入');
  }
}

// ── Group Modal ──
function openGroupModal(id) {
  var modal = document.getElementById('groupModal');
  var title = document.getElementById('groupModalTitle');
  var nameInput = document.getElementById('groupModalName');
  var iconInput = document.getElementById('groupModalIcon');
  var descInput = document.getElementById('groupModalDesc');
  var orderInput = document.getElementById('groupModalOrder');
  var enabledSelect = document.getElementById('groupModalEnabled');
  var idInput = document.getElementById('groupModalId');

  if (!modal) return;

  idInput.value = id || '';
  if (id) {
    var numId = parseInt(id, 10);
    var g = getGroupById(numId);
    if (g) {
      if (title) title.textContent = '编辑大类';
      if (nameInput) nameInput.value = g.name;
      if (iconInput) iconInput.value = g.icon;
      if (descInput) descInput.value = g.description || '';
      if (orderInput) orderInput.value = g.sort_order || 0;
      if (enabledSelect) enabledSelect.value = g.is_enabled ? '1' : '0';
      document.querySelectorAll('#groupIconPicker .icon-option').forEach(function(el) {
        el.classList.toggle('selected', el.dataset.icon === g.icon);
      });
    }
  } else {
    if (title) title.textContent = '新增大类';
    if (nameInput) nameInput.value = '';
    if (iconInput) iconInput.value = '🏠';
    if (descInput) descInput.value = '';
    if (orderInput) orderInput.value = '99';
    if (enabledSelect) enabledSelect.value = '1';
    document.querySelectorAll('#groupIconPicker .icon-option').forEach(function(el) {
      el.classList.toggle('selected', el.dataset.icon === '🏠');
    });
  }

  openModal('groupModal');
}

function saveGroupModal() {
  var idInput = document.getElementById('groupModalId');
  var nameInput = document.getElementById('groupModalName');
  var iconInput = document.getElementById('groupModalIcon');
  var descInput = document.getElementById('groupModalDesc');
  var orderInput = document.getElementById('groupModalOrder');
  var enabledSelect = document.getElementById('groupModalEnabled');

  var name = nameInput ? nameInput.value.trim() : '';
  if (!name) { showToast('请填写大类名称'); return; }

  var icon = iconInput ? iconInput.value : '🏠';
  var desc = descInput ? descInput.value.trim() : '';
  var order = parseInt((orderInput ? orderInput.value : '99')) || 99;
  var enabled = (enabledSelect ? enabledSelect.value : '1') === '1';

  var payload = {
    name: name,
    icon: icon,
    description: desc,
    sort_order: order,
    is_enabled: enabled
  };

  var isEdit = idInput && idInput.value;
  var url = isEdit ? apiBase + '/api/groups/' + idInput.value : apiBase + '/api/groups';
  var method = isEdit ? 'PUT' : 'POST';

  fetch(url, {
    method: method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    showToast(isEdit ? '大类已更新' : '大类「' + name + '」已添加');
    closeModal('groupModal');
    loadCategoryGroupsFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to save group:', err);
    showToast('保存失败');
  });
}

function deleteGroup(groupId) {
  var g = getGroupById(groupId);
  if (!g) return;
  var groupName = g.name;
  if (!confirm('确定要删除大类「' + groupName + '」吗？删除后该大类下的子分类将移至"全部"。')) return;

  fetch(apiBase + '/api/groups/' + groupId, {
    method: 'DELETE'
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '删除失败');
      return;
    }
    if (currentGroupFilter === groupId || currentGroupFilter === String(groupId)) {
      setGroupFilter('all');
    }
    loadCategoryGroupsFromAPI();
    showToast('大类已删除');
  })
  .catch(function(err) {
    console.error('Failed to delete group:', err);
    showToast('删除失败');
  });
}

// ── Sub-category Modal ──
function fillGroupSelect() {
  var sel = document.getElementById('subcatModalGroup');
  if (!sel) return;
  sel.innerHTML = '';
  if (categoryGroups.length === 0) {
    var opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '请先添加大类';
    sel.appendChild(opt);
    return;
  }
  categoryGroups.forEach(function(g) {
    if (!g.is_enabled) return;
    var opt = document.createElement('option');
    opt.value = g.id;
    opt.textContent = g.name;
    sel.appendChild(opt);
  });
}

function openSubcatModal(id) {
  // Require project and at least one group to exist
  if (!id) {
    // For new subcat, check if we have groups
    if (categoryGroups.length === 0) {
      showToast('请先添加分类大类');
      return;
    }
  }
  fillGroupSelect();
  var modal = document.getElementById('subcatModal');
  var title = document.getElementById('subcatModalTitle');
  var idInput = document.getElementById('subcatModalId');
  var nameInput = document.getElementById('subcatModalName');
  var groupSelect = document.getElementById('subcatModalGroup');
  var statusSelect = document.getElementById('subcatModalStatus');
  var budgetInput = document.getElementById('subcatModalBudget');
  var viewSelect = document.getElementById('subcatModalView');
  var noteInput = document.getElementById('subcatModalNote');

  if (!modal) return;

  idInput.value = id || '';
  if (id) {
    var numId = parseInt(id, 10);
    var c = subCategories.find(function(x) { return x.id === numId; });
    if (c) {
      if (title) title.textContent = '编辑子分类';
      if (nameInput) nameInput.value = c.name;
      if (groupSelect) groupSelect.value = c.group_id;
      if (statusSelect) statusSelect.value = c.status;
      if (budgetInput) budgetInput.value = c.budget || '';
      if (viewSelect) viewSelect.value = c.view_mode || 'card';
      if (noteInput) noteInput.value = c.description || '';
    }
  } else {
    if (title) title.textContent = '新增子分类';
    if (nameInput) nameInput.value = '';
    if (groupSelect) {
      if (currentGroupFilter !== 'all') {
        groupSelect.value = currentGroupFilter;
      } else if (categoryGroups.length > 0) {
        groupSelect.selectedIndex = 0;
      }
    }
    if (statusSelect) statusSelect.value = 'not_started';
    if (budgetInput) budgetInput.value = '';
    if (viewSelect) viewSelect.value = 'card';
    if (noteInput) noteInput.value = '';
  }

  openModal('subcatModal');
}

function saveSubcatModal() {
  var idInput = document.getElementById('subcatModalId');
  var nameInput = document.getElementById('subcatModalName');
  var groupSelect = document.getElementById('subcatModalGroup');
  var statusSelect = document.getElementById('subcatModalStatus');
  var budgetInput = document.getElementById('subcatModalBudget');
  var viewSelect = document.getElementById('subcatModalView');
  var noteInput = document.getElementById('subcatModalNote');

  var name = nameInput ? nameInput.value.trim() : '';
  if (!name) { showToast('请填写分类名称'); return; }

  var groupId = groupSelect ? groupSelect.value : '';
  if (!groupId) { showToast('请选择所属大类'); return; }
  var status = statusSelect ? statusSelect.value : 'not_started';
  var budget = parseFloat((budgetInput ? budgetInput.value : '0')) || 0;
  var viewMode = viewSelect ? viewSelect.value : 'card';
  var description = noteInput ? noteInput.value.trim() : '';

  var payload = {
    name: name,
    group_id: parseInt(groupId, 10),
    status: status,
    budget: budget,
    view_mode: viewMode,
    description: description
  };

  var isEdit = idInput && idInput.value;
  var url = apiBase + '/api/categories' + (isEdit ? '/' + idInput.value : '');
  var method = isEdit ? 'PUT' : 'POST';

  fetch(url, {
    method: method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') {
        showToast(data.message || '保存失败');
        return;
      }
      showToast(isEdit ? '分类已更新' : '分类「' + name + '」已添加');
      closeModal('subcatModal');
      // Reload from API
      loadCategoriesFromAPI();
      loadCategoryGroupsFromAPI();
    })
    .catch(function(err) {
      console.error('Failed to save category:', err);
      showToast('保存失败');
    });
}

function deleteSubcat(catId) {
  var numId = parseInt(catId, 10);
  var c = subCategories.find(function(x) { return x.id === numId; });
  if (!c) return;
  if (!confirm('确定要删除分类「' + c.name + '」吗？此操作不可恢复。')) return;

  fetch(apiBase + '/api/categories/' + catId, {
    method: 'DELETE'
  })
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') {
        showToast(data.message || '删除失败');
        return;
      }
      showToast('分类「' + c.name + '」已删除');
      // Reload from API
      loadCategoriesFromAPI();
      loadCategoryGroupsFromAPI();
    })
    .catch(function(err) {
      console.error('Failed to delete category:', err);
      showToast('删除失败');
    });
}

// ── Settings (stub) ──
function openCompareSettings() {
  showToast('项目设置后续接入');
}

// ── Initialize Compare Page ──
function initComparePage() {
  loadCategoryGroupsFromAPI();
  setView('card');

  // Group header buttons
  var btnAddGroup = document.getElementById('btnAddGroup');
  if (btnAddGroup) {
    btnAddGroup.addEventListener('click', function() { openGroupModal(null); });
  }

  // Add subcat button
  var btnAddSubcat = document.getElementById('btnAddSubcat');
  if (btnAddSubcat) {
    btnAddSubcat.addEventListener('click', function() { openSubcatModal(null); });
  }

  // View tabs
  var btnCardView = document.getElementById('btnCardView');
  var btnTableView = document.getElementById('btnTableView');
  if (btnCardView) {
    btnCardView.addEventListener('click', function() { setView('card'); });
  }
  if (btnTableView) {
    btnTableView.addEventListener('click', function() { setView('table'); });
  }

  // Icon picker
  document.querySelectorAll('#groupIconPicker .icon-option').forEach(function(el) {
    el.addEventListener('click', function() {
      var icon = this.dataset.icon;
      document.querySelectorAll('#groupIconPicker .icon-option').forEach(function(x) { x.classList.remove('selected'); });
      this.classList.add('selected');
      var iconInput = document.getElementById('groupModalIcon');
      if (iconInput) iconInput.value = icon;
    });
  });
}

// Auto-init when compare page is detected
function checkAndInitComparePage() {
  if (document.getElementById('categoryGroupGrid')) {
    initComparePage();
  }
}

// ═══════════════════════════════════════════
// 中央空调详情页 (/decoration/compare/air-conditioner)
// ═══════════════════════════════════════════

// AC Plan data (empty by default — no fake data)
var acPlans = [];

var currentAcView = 'table';
var currentFilter = 'all';
var currentSort = null; // null = no sort, 'price-asc'
var currentSearch = '';

// Render star rating
function renderStars(rating) {
  var fullStars = Math.floor(rating);
  var stars = '';
  for (var i = 0; i < 5; i++) {
    stars += i < fullStars ? '★' : '☆';
  }
  return '<div class="plan-rating"><span class="stars">' + stars + '</span><span class="value">' + rating.toFixed(1) + '</span></div>';
}

// Get filtered and sorted plans
function getFilteredPlans() {
  var filtered = acPlans.filter(function(plan) {
    // Filter by selected
    if (currentFilter === 'selected' && !plan.selected) return false;
    // Filter by search
    if (currentSearch) {
      var keyword = currentSearch.toLowerCase();
      var match = plan.brand.toLowerCase().indexOf(keyword) > -1 ||
                  plan.model.toLowerCase().indexOf(keyword) > -1 ||
                  plan.note.toLowerCase().indexOf(keyword) > -1;
      return match;
    }
    return true;
  });

  // Sort
  if (currentSort === 'price-asc') {
    filtered.sort(function(a, b) { return a.price - b.price; });
  }

  return filtered;
}

// Update plan count display
function updatePlanCount() {
  var countEl = document.getElementById('acPlanCount');
  var countEl2 = document.getElementById('acPlanCountToolbar');
  var countEl3 = document.getElementById('acPlanCountOverview');
  var totalCount = acPlans.length;
  var visibleCount = getFilteredPlans().length;
  var text = visibleCount + ' / ' + totalCount + ' 个方案';
  if (countEl) countEl.textContent = text;
  if (countEl2) countEl2.textContent = text;
  if (countEl3) countEl3.textContent = totalCount;
}

// Render table rows (Notion-style)
function renderAcPlanTable() {
  var tbody = document.getElementById('acPlanTableBody');
  var emptyEl = document.getElementById('acTableEmpty');
  if (!tbody) return;
  tbody.innerHTML = '';

  var plans = getFilteredPlans();

  if (plans.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    return;
  }
  if (emptyEl) emptyEl.style.display = 'none';

  plans.forEach(function(plan) {
    var row = document.createElement('tr');
    row.className = 'plan-row' + (plan.selected ? ' selected' : '');
    row.dataset.brand = plan.brand;
    row.dataset.model = plan.model;
    row.dataset.price = plan.price;
    row.dataset.selected = plan.selected;

    row.innerHTML =
      '<td class="sticky-col col-select">' +
        '<div class="radio-circle' + (plan.selected ? ' checked' : '') + '" onclick="selectAirconPlan(\'' + plan.id + '\')"></div>' +
      '</td>' +
      '<td class="sticky-col col-brand"><span class="plan-brand">' + plan.brand + '</span></td>' +
      '<td>' + plan.model + '</td>' +
      '<td class="plan-config">' + plan.power + ' / ' + plan.units + '</td>' +
      '<td><span class="plan-price">¥' + formatNumber(plan.price) + '</span></td>' +
      '<td>' + plan.outdoor + ' 外机 / ' + plan.indoor + ' 内机</td>' +
      '<td><span class="kanban-chip">' + plan.efficiency + '</span></td>' +
      '<td>' + plan.warranty + '</td>' +
      '<td>' + renderStars(plan.rating) + '</td>' +
      '<td><button class="plan-attachment" onclick="showToast(\'图片预览后续接入\')"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"/></svg>图片</button></td>' +
      '<td><button class="plan-attachment" onclick="showToast(\'图片预览后续接入\')"><svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/></svg>报价单</button></td>' +
      '<td><span class="plan-note" title="' + plan.note + '" onclick="showToast(\'' + plan.note + '\')">' + plan.note + '</span></td>' +
      '<td>' +
        '<div class="plan-actions">' +
          (plan.selected ?
            '<button class="plan-action-btn selected">已选中</button>' :
            '<button class="plan-action-btn primary" onclick="selectAirconPlan(\'' + plan.id + '\')">选为最终</button>') +
          '<button class="plan-action-btn" onclick="editAirconPlan(\'' + plan.id + '\')">编辑</button>' +
          '<button class="plan-action-btn danger" onclick="deleteAirconPlan(\'' + plan.id + '\')">删除</button>' +
        '</div>' +
      '</td>';
    tbody.appendChild(row);
  });

  updatePlanCount();
}

// Render card view
function renderAcPlanCards() {
  var container = document.getElementById('acPlanCards');
  var emptyEl = document.getElementById('acCardEmpty');
  if (!container) return;
  container.innerHTML = '';

  var plans = getFilteredPlans();

  if (plans.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    return;
  }
  if (emptyEl) emptyEl.style.display = 'none';

  plans.forEach(function(plan) {
    var card = document.createElement('div');
    card.className = 'ac-plan-card' + (plan.selected ? ' selected' : '');
    card.innerHTML =
      '<div class="ac-plan-card-header">' +
        '<div>' +
          '<div class="ac-plan-card-brand">' + plan.brand + '</div>' +
          '<div class="ac-plan-card-model">' + plan.model + '</div>' +
        '</div>' +
        '<div class="ac-plan-card-price">¥' + formatNumber(plan.price) + '</div>' +
      '</div>' +
      '<div class="ac-plan-card-body">' +
        '<div class="ac-plan-card-meta">' +
          '<div class="ac-plan-card-meta-item">' +
            '<span class="ac-plan-card-meta-label">一拖几</span>' +
            '<span class="ac-plan-card-meta-value">' + plan.units + '</span>' +
          '</div>' +
          '<div class="ac-plan-card-meta-item">' +
            '<span class="ac-plan-card-meta-label">能效等级</span>' +
            '<span class="ac-plan-card-meta-value">' + plan.efficiency + '</span>' +
          '</div>' +
          '<div class="ac-plan-card-meta-item">' +
            '<span class="ac-plan-card-meta-label">内机数量</span>' +
            '<span class="ac-plan-card-meta-value">' + plan.indoor + ' 台</span>' +
          '</div>' +
          '<div class="ac-plan-card-meta-item">' +
            '<span class="ac-plan-card-meta-label">保修</span>' +
            '<span class="ac-plan-card-meta-value">' + plan.warranty + '</span>' +
          '</div>' +
        '</div>' +
        '<div class="ac-plan-card-rating">' +
          '<span class="stars">' + '★'.repeat(Math.floor(plan.rating)) + '☆'.repeat(5 - Math.floor(plan.rating)) + '</span>' +
          '<span class="value">' + plan.rating.toFixed(1) + '</span>' +
          '<span class="label">推荐指数</span>' +
        '</div>' +
        '<div class="ac-plan-card-note">' + plan.note + '</div>' +
        '<div class="ac-plan-card-footer">' +
          (plan.selected ?
            '<button class="btn btn-sm btn-primary">已选中</button>' :
            '<button class="btn btn-sm btn-secondary" onclick="selectAirconPlan(\'' + plan.id + '\')">选为最终方案</button>') +
          '<button class="btn btn-sm btn-ghost" onclick="editAirconPlan(\'' + plan.id + '\')">编辑</button>' +
          '<button class="btn btn-sm btn-ghost" style="color:var(--accent-red);" onclick="deleteAirconPlan(\'' + plan.id + '\')">删除</button>' +
        '</div>' +
      '</div>';
    container.appendChild(card);
  });

  updatePlanCount();
}

// Select a plan as the final choice (via API)
function selectAirconPlan(planId) {
  fetch(apiBase + '/api/compare-items/' + planId + '/select', {
    method: 'POST'
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '选择失败');
      return;
    }
    showToast('已选为最终方案');
    loadAcPlansFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to select plan:', err);
    showToast('选择失败');
  });
}

// Update overview card with selected plan info
function updateAirconOverview(plan) {
  var planNameEl = document.getElementById('acPlanName');
  var costEl = document.getElementById('acPlanCost');
  var statusEl = document.getElementById('acOverviewStatus');
  var statusTextEl = document.getElementById('acStatusText');
  var decisionList = document.getElementById('acDecisionList');
  var decisionEmpty = document.getElementById('acDecisionEmpty');

  if (plan) {
    var price = plan.total_price || plan.price || 0;
    if (planNameEl) planNameEl.textContent = plan.brand + ' ' + plan.model;
    if (costEl) costEl.textContent = '¥' + formatNumber(price);
    if (statusEl) {
      statusEl.className = 'ac-overview-status selected';
    }
    if (statusTextEl) statusTextEl.textContent = '已选方案';
    if (decisionList && decisionEmpty) {
      decisionEmpty.textContent = '已选中 ' + plan.brand + ' ' + plan.model + '，建议在付款前确认是否包含铜管、打孔、排水、检修口等费用。';
    }
  } else {
    if (planNameEl) planNameEl.textContent = '未选择';
    if (costEl) costEl.textContent = '¥0';
    if (statusEl) {
      statusEl.className = 'ac-overview-status';
    }
    if (statusTextEl) statusTextEl.textContent = '暂无方案';
    if (decisionList && decisionEmpty) {
      decisionEmpty.textContent = '添加多个方案后，系统可以帮助你对比价格、配置和风险点。';
    }
  }
}

// Filter plans
function filterAirconPlans(type) {
  currentFilter = type;

  // Update filter tab UI
  document.querySelectorAll('.ac-filter-tab').forEach(function(tab) {
    tab.classList.toggle('active', tab.dataset.filter === type);
  });

  renderAcPlanTable();
  if (currentAcView === 'card') {
    renderAcPlanCards();
  }
}

// Search plans
function searchAirconPlans(keyword) {
  currentSearch = keyword;
  renderAcPlanTable();
  if (currentAcView === 'card') {
    renderAcPlanCards();
  }
}

// Sort by price
function sortAirconPlansByPrice() {
  var sortBtn = document.querySelector('.ac-sort-btn');
  if (currentSort === 'price-asc') {
    currentSort = null;
    if (sortBtn) sortBtn.classList.remove('active');
  } else {
    currentSort = 'price-asc';
    if (sortBtn) sortBtn.classList.add('active');
  }
  renderAcPlanTable();
  if (currentAcView === 'card') {
    renderAcPlanCards();
  }
}

// Edit plan
function editAirconPlan(planId) {
  var plan = acPlans.find(function(p) { return p.id === planId; });
  if (!plan) {
    showToast('方案不存在');
    return;
  }

  // Fill form
  var inputs = [
    { id: 'planBrand', val: plan.brand },
    { id: 'planModel', val: plan.model },
    { id: 'planPower', val: plan.spec || '' },
    { id: 'planUnits', val: plan.room_count || '' },
    { id: 'planPrice', val: plan.total_price || '' },
    { id: 'planOutdoor', val: plan.outdoor_unit_count || '' },
    { id: 'planIndoor', val: plan.indoor_unit_count || '' },
    { id: 'planWarranty', val: plan.warranty || '' },
    { id: 'planRating', val: plan.rating || '' },
    { id: 'planNote', val: plan.note || '' }
  ];
  inputs.forEach(function(item) {
    var el = document.getElementById(item.id);
    if (el) el.value = item.val;
  });
  var effSelect = document.getElementById('planEfficiency');
  if (effSelect) effSelect.value = plan.energy_level || '';

  // Store edit mode flag
  window.editingPlanId = planId;

  // Change modal title
  var title = document.querySelector('#addPlanModal .modal-header h3');
  if (title) title.textContent = '编辑方案';

  openModal('addPlanModal');
}

// Delete plan (via API)
function deleteAirconPlan(planId) {
  var plan = acPlans.find(function(p) { return p.id === planId; });
  if (!plan) {
    showToast('方案不存在');
    return;
  }

  if (!confirm('确定要删除「' + plan.brand + ' ' + plan.model + '」方案吗？')) return;

  fetch(apiBase + '/api/compare-items/' + planId, {
    method: 'DELETE'
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '删除失败');
      return;
    }
    showToast('方案已删除');
    loadAcPlansFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to delete plan:', err);
    showToast('删除失败');
  });
}

// Select plan as final
function selectAirconPlan(planId) {
  fetch(apiBase + '/api/compare-items/' + planId + '/select', {
    method: 'POST'
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '选择失败');
      return;
    }
    showToast('已选为最终方案');
    loadAcPlansFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to select plan:', err);
    showToast('选择失败');
  });
}

// Toggle between table and card view
function toggleAcView(view) {
  currentAcView = view;
  var tableView = document.getElementById('acTableView');
  var cardView = document.getElementById('acCardView');

  if (view === 'table') {
    if (tableView) tableView.style.display = '';
    if (cardView) cardView.style.display = 'none';
  } else {
    if (tableView) tableView.style.display = 'none';
    if (cardView) cardView.style.display = '';
    renderAcPlanCards();
  }

  // Update tab buttons
  document.querySelectorAll('.ac-view-toggle .view-tab').forEach(function(tab) {
    tab.classList.toggle('active', tab.dataset.view === view);
  });
}

// Open add plan modal
function openAddPlanModal() {
  if (!window.acCategoryId) {
    showToast('请先添加中央空调分类');
    return;
  }
  // Reset form
  var inputs = ['planBrand', 'planModel', 'planPower', 'planUnits', 'planPrice', 'planOutdoor', 'planIndoor', 'planWarranty', 'planRating', 'planNote'];
  inputs.forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.value = '';
  });
  var effSelect = document.getElementById('planEfficiency');
  if (effSelect) effSelect.selectedIndex = 0;

  openModal('addPlanModal');
}

// Save new plan (to API, supports both create and edit)
function saveNewPlan() {
  var brand = document.getElementById('planBrand');
  var model = document.getElementById('planModel');
  var power = document.getElementById('planPower');
  var units = document.getElementById('planUnits');
  var price = document.getElementById('planPrice');
  var outdoor = document.getElementById('planOutdoor');
  var indoor = document.getElementById('planIndoor');
  var efficiency = document.getElementById('planEfficiency');
  var warranty = document.getElementById('planWarranty');
  var rating = document.getElementById('planRating');
  var note = document.getElementById('planNote');

  brand = brand ? brand.value.trim() : '';
  model = model ? model.value.trim() : '';
  power = power ? power.value.trim() : '';
  units = units ? units.value.trim() : '';
  price = price ? parseInt(price.value) || 0 : 0;
  outdoor = outdoor ? parseInt(outdoor.value) || 0 : 0;
  indoor = indoor ? parseInt(indoor.value) || 0 : 0;
  efficiency = efficiency ? efficiency.value : '';
  warranty = warranty ? warranty.value.trim() : '';
  rating = rating ? parseFloat(rating.value) || 0 : 0;
  note = note ? note.value.trim() : '';

  if (!brand) {
    showToast('请填写品牌');
    return;
  }
  if (!model) {
    showToast('请填写型号');
    return;
  }

  var categoryId = window.acCategoryId;
  if (!categoryId) {
    showToast('请先添加中央空调分类');
    return;
  }
  var isEdit = window.editingPlanId;

  var payload = {
    category_id: categoryId,
    brand: brand,
    model: model,
    spec: power,
    room_count: 0,
    total_price: price,
    outdoor_unit_count: outdoor,
    indoor_unit_count: indoor,
    energy_level: efficiency,
    warranty: warranty,
    rating: rating,
    note: note
  };

  var url = isEdit ? apiBase + '/api/compare-items/' + isEdit : apiBase + '/api/compare-items';
  var method = isEdit ? 'PUT' : 'POST';

  fetch(url, {
    method: method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    showToast(isEdit ? '方案已更新' : '已新增方案');
    closeModal('addPlanModal');
    window.editingPlanId = null;
    // Reset modal title
    var title = document.querySelector('#addPlanModal .modal-header h3');
    if (title) title.textContent = '新增中央空调方案';
    loadAcPlansFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to save plan:', err);
    showToast('保存失败');
  });
}

// ============================================================
// 通用参数字段定义系统 - 支持多种产品类型
// ============================================================

// 产品类型分组定义
var PARAM_FIELD_CATEGORIES = {
  'basic': { name: '基本信息', icon: '📋', color: '#6366F1' },
  'spec': { name: '规格参数', icon: '📐', color: '#8B5CF6' },
  'price': { name: '价格相关', icon: '💰', color: '#10B981' },
  'quality': { name: '质量指标', icon: '⭐', color: '#F59E0B' },
  'service': { name: '服务保障', icon: '🛡️', color: '#3B82F6' },
  'media': { name: '图文资料', icon: '🖼️', color: '#EC4899' },
  'custom': { name: '自定义字段', icon: '✏️', color: '#64748B' }
};

// 通用参数字段定义（按类别分组）
var PARAM_FIELD_DEFS = [
  // ========== 基本信息 ==========
  { key: 'brand', name: '品牌', category: 'basic', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: false },
  { key: 'model', name: '型号', category: 'basic', type: 'text', 
    presets: { ac: true, floor: true, sofa: false, curtain: false, lighting: true, paint: true, door: true, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'origin', name: '产地/进口', category: 'basic', type: 'select', 
    options: ['国产', '进口', '合资'], 
    presets: { ac: true, floor: true, sofa: true, curtain: false, lighting: true, paint: false, door: true, ceiling: false },
    defaultVisible: false, defaultHighlight: false },
  { key: 'supplier', name: '供应商', category: 'basic', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'contact', name: '联系方式', category: 'basic', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },

  // ========== 规格参数 ==========
  { key: 'power', name: '功率/匹数', category: 'spec', type: 'text', 
    presets: { ac: true, floor: false, sofa: false, curtain: false, lighting: true, paint: false, door: false, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'capacity', name: '容量/规格', category: 'spec', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: false, paint: true, door: false, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'dimensions', name: '尺寸/规格', category: 'spec', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: false, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: false },
  { key: 'weight', name: '重量', category: 'spec', type: 'text', 
    presets: { ac: true, floor: false, sofa: true, curtain: false, lighting: true, paint: false, door: false, ceiling: false },
    defaultVisible: false, defaultHighlight: false },
  { key: 'material', name: '材质', category: 'spec', type: 'select', 
    options: [], // 根据产品类型动态填充
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: false, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: false },
  { key: 'color', name: '颜色/色号', category: 'spec', type: 'text', 
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'units', name: '一拖几/套餐', category: 'spec', type: 'text', 
    presets: { ac: true, floor: false, sofa: false, curtain: false, lighting: false, paint: false, door: false, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'outdoor_units', name: '外机数量', category: 'spec', type: 'number', 
    presets: { ac: true, floor: false, sofa: false, curtain: false, lighting: false, paint: false, door: false, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'indoor_units', name: '内机数量', category: 'spec', type: 'number', 
    presets: { ac: true, floor: false, sofa: false, curtain: false, lighting: false, paint: false, door: false, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'coverage', name: '覆盖面积', category: 'spec', type: 'text', 
    presets: { ac: true, floor: false, sofa: false, curtain: false, lighting: true, paint: true, door: false, ceiling: false },
    defaultVisible: false, defaultHighlight: false },
  { key: 'features', name: '功能特点', category: 'spec', type: 'text', 
    presets: { ac: true, floor: false, sofa: true, curtain: false, lighting: true, paint: false, door: false, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'tech_spec', name: '技术参数', category: 'spec', type: 'textarea', 
    presets: { ac: true, floor: true, sofa: false, curtain: false, lighting: true, paint: true, door: false, ceiling: false },
    defaultVisible: false, defaultHighlight: false },
  
  // ========== 价格相关 ==========
  { key: 'price', name: '总价', category: 'price', type: 'amount', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: true },
  { key: 'unit_price', name: '单价', category: 'price', type: 'amount', 
    presets: { ac: false, floor: true, sofa: false, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'quantity', name: '数量', category: 'price', type: 'number', 
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: false },
  { key: 'area', name: '面积', category: 'price', type: 'text', 
    presets: { ac: false, floor: true, sofa: false, curtain: true, lighting: false, paint: true, door: false, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'install_fee', name: '安装费', category: 'price', type: 'amount', 
    presets: { ac: true, floor: true, sofa: false, curtain: true, lighting: true, paint: false, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'shipping_fee', name: '运费', category: 'price', type: 'amount', 
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'discount', name: '折扣/优惠', category: 'price', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },

  // ========== 质量指标 ==========
  { key: 'energy_level', name: '能效等级', category: 'quality', type: 'select', 
    options: ['一级', '二级', '三级', '四级', '五级'], 
    presets: { ac: true, floor: false, sofa: false, curtain: false, lighting: true, paint: false, door: false, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'rating', name: '推荐指数', category: 'quality', type: 'rating', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: true },
  { key: 'quality_level', name: '质量等级', category: 'quality', type: 'select', 
    options: ['优等品', '一等品', '合格品'], 
    presets: { ac: false, floor: true, sofa: true, curtain: false, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'certification', name: '认证/环保', category: 'quality', type: 'select', 
    options: ['E0级', 'E1级', 'E2级', 'F4星', '无醛', '十环认证', '3C认证', 'CE认证'], 
    presets: { ac: false, floor: true, sofa: true, curtain: false, lighting: false, paint: true, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: false },
  { key: 'warranty', name: '保修年限', category: 'quality', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: false, lighting: true, paint: false, door: true, ceiling: false },
    defaultVisible: true, defaultHighlight: false },
  { key: 'lifespan', name: '预期寿命', category: 'quality', type: 'text', 
    presets: { ac: true, floor: true, sofa: true, curtain: false, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },

  // ========== 服务保障 ==========
  { key: 'has_install', name: '含安装服务', category: 'service', type: 'boolean', 
    presets: { ac: true, floor: true, sofa: false, curtain: true, lighting: true, paint: false, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'has_delivery', name: '含送货服务', category: 'service', type: 'boolean', 
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'return_policy', name: '退换政策', category: 'service', type: 'text', 
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: false, door: false, ceiling: false },
    defaultVisible: false, defaultHighlight: false },
  { key: 'install_date', name: '预约安装日期', category: 'service', type: 'date', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: false, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'delivery_date', name: '预计到货日期', category: 'service', type: 'date', 
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },

  // ========== 图文资料 ==========
  { key: 'product_image', name: '产品图片', category: 'media', type: 'image', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: false },
  { key: 'quote_image', name: '报价单图片', category: 'media', type: 'image', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'scene_image', name: '场景效果图', category: 'media', type: 'image', 
    presets: { ac: false, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'manual_url', name: '产品手册链接', category: 'media', type: 'text', 
    presets: { ac: true, floor: false, sofa: false, curtain: false, lighting: true, paint: false, door: false, ceiling: false },
    defaultVisible: false, defaultHighlight: false },

  // ========== 自定义字段 ==========
  { key: 'note', name: '备注说明', category: 'custom', type: 'textarea', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: true, defaultHighlight: false },
  { key: 'pros', name: '优点', category: 'custom', type: 'textarea', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false },
  { key: 'cons', name: '缺点', category: 'custom', type: 'textarea', 
    presets: { ac: true, floor: true, sofa: true, curtain: true, lighting: true, paint: true, door: true, ceiling: true },
    defaultVisible: false, defaultHighlight: false }
];

// 产品类型预设配置
var PARAM_PRESETS = {
  'ac': { 
    name: '中央空调', 
    icon: '❄️', 
    description: '空调/新风/暖气等暖通设备',
    fields: ['brand', 'model', 'power', 'units', 'price', 'outdoor_units', 'indoor_units', 'energy_level', 'warranty', 'product_image', 'quote_image', 'note', 'rating']
  },
  'floor': { 
    name: '地板/地砖', 
    icon: '🏠', 
    description: '木地板/复合地板/瓷砖/石材等地面材料',
    fields: ['brand', 'model', 'material', 'color', 'dimensions', 'price', 'unit_price', 'quantity', 'area', 'install_fee', 'certification', 'quality_level', 'warranty', 'product_image', 'quote_image', 'scene_image', 'note', 'rating']
  },
  'sofa': { 
    name: '沙发/家具', 
    icon: '🛋️', 
    description: '沙发/床/柜子等软装家具',
    fields: ['brand', 'model', 'material', 'color', 'dimensions', 'capacity', 'price', 'quantity', 'shipping_fee', 'warranty', 'lifespan', 'product_image', 'quote_image', 'scene_image', 'note', 'rating']
  },
  'curtain': { 
    name: '窗帘/布艺', 
    icon: '🪟', 
    description: '窗帘/地毯/墙布等布艺软装',
    fields: ['brand', 'material', 'color', 'dimensions', 'price', 'quantity', 'area', 'install_fee', 'shipping_fee', 'product_image', 'scene_image', 'note', 'rating']
  },
  'lighting': { 
    name: '灯具/开关', 
    icon: '💡', 
    description: '灯具/开关插座/智能家居',
    fields: ['brand', 'model', 'power', 'color', 'dimensions', 'features', 'price', 'unit_price', 'quantity', 'install_fee', 'shipping_fee', 'energy_level', 'warranty', 'product_image', 'quote_image', 'scene_image', 'note', 'rating']
  },
  'paint': { 
    name: '涂料/墙漆', 
    icon: '🎨', 
    description: '乳胶漆/艺术漆/硅藻泥等墙面材料',
    fields: ['brand', 'model', 'color', 'capacity', 'price', 'unit_price', 'area', 'certification', 'features', 'warranty', 'lifespan', 'product_image', 'scene_image', 'note', 'rating']
  },
  'door': { 
    name: '门窗/楼梯', 
    icon: '🚪', 
    description: '木门/铝合金窗/楼梯/扶手',
    fields: ['brand', 'model', 'material', 'color', 'dimensions', 'price', 'quantity', 'install_fee', 'shipping_fee', 'warranty', 'product_image', 'quote_image', 'scene_image', 'note', 'rating']
  },
  'ceiling': { 
    name: '吊顶/背景墙', 
    icon: '🏗️', 
    description: '石膏板吊顶/铝扣板/电视背景墙',
    fields: ['brand', 'material', 'dimensions', 'price', 'area', 'install_fee', 'shipping_fee', 'warranty', 'product_image', 'scene_image', 'note', 'rating']
  }
};

// 当前选中的产品类型
var currentProductPreset = 'ac';

// 参数字段设置（用户配置）
var paramFieldSettings = {};

// Open param settings modal
function openParamSettingsModal() {
  // 加载保存的设置或使用默认值
  loadParamFieldSettings();
  renderParamFieldsList();
  openModal('paramSettingsModal');
}

// 加载字段设置
function loadParamFieldSettings() {
  var saved = localStorage.getItem('param_field_settings');
  if (saved) {
    try {
      var data = JSON.parse(saved);
      paramFieldSettings = data.settings || {};
      currentProductPreset = data.preset || 'ac';
    } catch(e) {
      paramFieldSettings = {};
      currentProductPreset = 'ac';
    }
  }

  // 合并默认值
  PARAM_FIELD_DEFS.forEach(function(field) {
    if (typeof paramFieldSettings[field.key] === 'undefined') {
      paramFieldSettings[field.key] = {
        visible: field.defaultVisible,
        highlight: field.defaultHighlight
      };
    }
  });
}

// 获取当前产品类型的可见字段
function getVisibleFieldsForPreset(preset) {
  return PARAM_FIELD_DEFS.filter(function(field) {
    return field.presets && field.presets[preset];
  });
}

// 渲染字段列表（简化版 - 所有字段平铺）
function renderParamFieldsList() {
  var container = document.getElementById('paramFieldsList');
  if (!container) return;

  var html = '';

  // 添加自定义字段按钮
  html += '<div class="param-add-field-bar">';
  html += '<input type="text" id="newFieldName" class="param-add-input" placeholder="输入新字段名称...">';
  html += '<select id="newFieldType" class="param-add-select">';
  html += '<option value="text">文本</option>';
  html += '<option value="number">数字</option>';
  html += '<option value="amount">金额</option>';
  html += '<option value="select">下拉选项</option>';
  html += '<option value="textarea">长文本</option>';
  html += '<option value="date">日期</option>';
  html += '<option value="boolean">开关</option>';
  html += '<option value="rating">评分</option>';
  html += '<option value="image">图片</option>';
  html += '</select>';
  html += '<button class="btn btn-sm btn-primary" onclick="addCustomField()">+ 添加字段</button>';
  html += '</div>';

  // 字段列表标题
  html += '<div class="param-fields-header">';
  html += '<span class="ph-col ph-col-check">显示</span>';
  html += '<span class="ph-col ph-col-star">★</span>';
  html += '<span class="ph-col ph-col-name">字段名称</span>';
  html += '<span class="ph-col ph-col-type">类型</span>';
  html += '<span class="ph-col ph-col-options">选项</span>';
  html += '</div>';

  // 渲染所有字段
  html += '<div class="param-fields-rows">';
  PARAM_FIELD_DEFS.forEach(function(field) {
    var settings = paramFieldSettings[field.key] || { visible: field.defaultVisible, highlight: field.defaultHighlight };
    var typeLabel = getFieldTypeLabel(field.type);
    
    html += '<div class="param-field-row' + (settings.highlight ? ' highlight' : '') + '" data-field="' + field.key + '">';
    
    // 勾选框
    html += '<div class="pf-cell pf-cell-check">';
    html += '<input type="checkbox" id="pf_' + field.key + '" ' + (settings.visible ? 'checked' : '') + ' ' +
            'onchange="toggleParamField(\'' + field.key + '\', \'visible\')">';
    html += '</div>';
    
    // 高亮按钮
    html += '<div class="pf-cell pf-cell-star">';
    html += '<button class="param-star-btn' + (settings.highlight ? ' active' : '') + '" ' +
            'onclick="toggleParamField(\'' + field.key + '\', \'highlight\')">★</button>';
    html += '</div>';
    
    // 字段名称
    html += '<div class="pf-cell pf-cell-name">';
    html += '<span class="field-name">' + field.name + '</span>';
    html += '</div>';
    
    // 类型选择
    html += '<div class="pf-cell pf-cell-type">';
    html += '<select class="field-type-select" onchange="changeFieldType(\'' + field.key + '\', this.value)">';
    var types = ['text', 'number', 'amount', 'select', 'textarea', 'date', 'boolean', 'rating', 'image'];
    var typeNames = { 'text': '文本', 'number': '数字', 'amount': '金额', 'select': '下拉', 'textarea': '长文本', 'date': '日期', 'boolean': '开关', 'rating': '评分', 'image': '图片' };
    types.forEach(function(t) {
      html += '<option value="' + t + '"' + (field.type === t ? ' selected' : '') + '>' + typeNames[t] + '</option>';
    });
    html += '</select>';
    html += '</div>';
    
    // 选项（仅下拉类型显示）
    html += '<div class="pf-cell pf-cell-options">';
    if (field.type === 'select') {
      html += '<input type="text" class="field-options-input" placeholder="选项用|分隔" ' +
              'value="' + (field.options ? field.options.join('|') : '') + '" ' +
              'onchange="updateFieldOptions(\'' + field.key + '\', this.value)">';
    }
    html += '</div>';
    
    html += '</div>';
  });
  html += '</div>';

  container.innerHTML = html;
}

// 添加自定义字段
function addCustomField() {
  var nameInput = document.getElementById('newFieldName');
  var typeSelect = document.getElementById('newFieldType');
  
  if (!nameInput || !typeSelect) return;
  
  var name = nameInput.value.trim();
  var type = typeSelect.value;
  
  if (!name) {
    showToast('请输入字段名称');
    return;
  }
  
  // 检查是否已存在
  var exists = PARAM_FIELD_DEFS.some(function(f) { return f.key === 'custom_' + name.toLowerCase().replace(/\s+/g, '_'); });
  if (exists) {
    showToast('字段已存在');
    return;
  }
  
  var key = 'custom_' + Date.now();
  var newField = {
    key: key,
    name: name,
    category: 'custom',
    type: type,
    options: type === 'select' ? [] : undefined,
    presets: {},
    defaultVisible: true,
    defaultHighlight: false
  };
  
  PARAM_FIELD_DEFS.push(newField);
  paramFieldSettings[key] = { visible: true, highlight: false };
  
  nameInput.value = '';
  renderParamFieldsList();
  showToast('已添加字段 "' + name + '"');
}

// 修改字段类型
function changeFieldType(fieldKey, newType) {
  var field = PARAM_FIELD_DEFS.find(function(f) { return f.key === fieldKey; });
  if (field) {
    field.type = newType;
    if (newType === 'select' && !field.options) {
      field.options = [];
    }
    renderParamFieldsList();
  }
}

// 更新字段选项
function updateFieldOptions(fieldKey, optionsStr) {
  var field = PARAM_FIELD_DEFS.find(function(f) { return f.key === fieldKey; });
  if (field) {
    field.options = optionsStr.split('|').map(function(o) { return o.trim(); }).filter(function(o) { return o; });
  }
}

// 获取字段类型标签
function getFieldTypeLabel(type) {
  var labels = {
    'text': '文本',
    'number': '数字',
    'amount': '金额',
    'select': '下拉',
    'textarea': '长文本',
    'date': '日期',
    'boolean': '开关',
    'rating': '评分',
    'image': '图片'
  };
  return labels[type] || type;
}

// 切换参数字类别
function switchParamCategory(categoryKey) {
  // 切换 tab 样式
  document.querySelectorAll('.param-category-tab').forEach(function(tab) {
    tab.classList.toggle('active', tab.dataset.category === categoryKey);
  });
  // 切换内容显示
  document.querySelectorAll('.param-category-section').forEach(function(section) {
    section.style.display = section.id === 'paramCategory_' + categoryKey ? 'block' : 'none';
  });
}

// 切换字段设置
function toggleParamField(key, type) {
  if (!paramFieldSettings[key]) {
    paramFieldSettings[key] = { visible: true, highlight: false };
  }
  if (type === 'visible') {
    var checkbox = document.getElementById('pf_' + key);
    paramFieldSettings[key].visible = checkbox.checked;
    var nameEl = checkbox.parentElement.querySelector('.param-field-name');
    if (nameEl) nameEl.classList.toggle('show', checkbox.checked);
  } else if (type === 'highlight') {
    paramFieldSettings[key].highlight = !paramFieldSettings[key].highlight;
    var item = document.querySelector('.param-field-item[data-field="' + key + '"]');
    if (item) {
      item.classList.toggle('highlight', paramFieldSettings[key].highlight);
      var star = item.querySelector('.param-field-star');
      if (star) star.classList.toggle('active', paramFieldSettings[key].highlight);
    }
  }
}

// 应用预设
function applyParamPreset(presetKey) {
  var preset = PARAM_PRESETS[presetKey];
  if (!preset) return;

  currentProductPreset = presetKey;
  
  // 更新按钮样式
  document.querySelectorAll('.param-preset-btn').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.preset === presetKey);
  });

  // 根据预设字段配置可见性
  PARAM_FIELD_DEFS.forEach(function(field) {
    if (!paramFieldSettings[field.key]) {
      paramFieldSettings[field.key] = { visible: true, highlight: false };
    }
    
    var inPreset = preset.fields.indexOf(field.key) >= 0;
    paramFieldSettings[field.key].visible = inPreset;
    // 预设中的关键字段高亮
    paramFieldSettings[field.key].highlight = inPreset && ['price', 'rating'].indexOf(field.key) >= 0;
  });

  renderParamFieldsList();
  showToast('已应用 "' + preset.name + '" 预设');
}

// 重置为默认设置
function resetParamSettings() {
  localStorage.removeItem('param_field_settings');
  paramFieldSettings = {};
  currentProductPreset = 'ac';
  PARAM_FIELD_DEFS.forEach(function(field) {
    paramFieldSettings[field.key] = {
      visible: field.defaultVisible,
      highlight: field.defaultHighlight
    };
  });
  renderParamFieldsList();
  showToast('已重置为默认设置');
}

// 保存并应用设置
function saveParamSettings() {
  localStorage.setItem('param_field_settings', JSON.stringify({
    settings: paramFieldSettings,
    preset: currentProductPreset
  }));
  applyParamFieldSettingsToTable();
  closeModal('paramSettingsModal');
  showToast('参数设置已保存');
}

// 应用设置到表格（兼容旧函数名）
function applyAcFieldSettingsToTable() {
  applyParamFieldSettingsToTable();
}

// 应用设置到表格
function applyParamFieldSettingsToTable() {
  var table = document.getElementById('acPlanTable');
  if (!table) return;

  // 更新参数字段统计
  var visibleCount = PARAM_FIELD_DEFS.filter(function(f) {
    var s = paramFieldSettings[f.key] || { visible: f.defaultVisible };
    return s.visible;
  }).length;
  var hintSpan = document.querySelector('.ac-params-section .ac-section-hint');
  if (hintSpan) hintSpan.textContent = '共 ' + visibleCount + ' 个字段';

  // 更新参数字段 chips
  var paramsGrid = document.querySelector('.ac-params-grid');
  if (paramsGrid) {
    var chipsHtml = '';
    PARAM_FIELD_DEFS.forEach(function(field) {
      var settings = paramFieldSettings[field.key] || { visible: field.defaultVisible, highlight: field.defaultHighlight };
      if (settings.visible) {
        var typeLabel = getFieldTypeLabel(field.type);
        chipsHtml += '<div class="ac-param-chip' + (settings.highlight ? ' highlight' : '') + '">' +
                    '<span class="param-type">' + typeLabel + '</span>' + field.name + '</div>';
      }
    });
    paramsGrid.innerHTML = chipsHtml;
  }
}

// 获取字段在表格中的列索引（兼容旧函数）
function getAcFieldColumnIndex(fieldKey) {
  var map = {
    'brand': 1, 'model': 2, 'power': 3, 'units': 4, 'price': 5,
    'outdoor_units': 6, 'indoor_units': 7, 'energy_level': 8, 'warranty': 9,
    'rating': 10, 'product_image': 11, 'quote_image': 12, 'note': 13
  };
  return map[fieldKey] || -1;
}

// Initialize AC detail page
function initAcDetailPage() {
  if (document.getElementById('acPlanTableBody')) {
    // 加载字段设置
    loadParamFieldSettings();
    // Load lookup data and plans in parallel, then render related manuals
    loadLookupData(function() {
      loadAcPlansFromAPI();
      loadAcRelatedNotes();
      // 应用保存的字段设置
      applyParamFieldSettingsToTable();
    });
  }
}

// Load and render related manual notes for AC detail page
function loadAcRelatedNotes() {
  var container = document.getElementById('acManualsList');
  var countBadge = document.getElementById('acManualCountBadge');
  var countOverview = document.getElementById('acManualCount');
  if (!container) return;

  var acCategoryId = window.acCategoryId;
  if (!acCategoryId) return;

  // Collect all compare_item IDs for current AC category
  var acCompareItemIds = [];
  if (window.renovaLookupData && window.renovaLookupData.compare_items) {
    window.renovaLookupData.compare_items.forEach(function(item) {
      if (item.category_id === acCategoryId) {
        acCompareItemIds.push(item.id);
      }
    });
  }

  // Filter notes: category matches OR compare_item is one of AC plans
  var relatedNotes = [];
  if (window.renovaLookupData && window.renovaLookupData.notes) {
    relatedNotes = window.renovaLookupData.notes.filter(function(note) {
      if (note.category_id === acCategoryId) return true;
      if (note.compare_item_id && acCompareItemIds.indexOf(note.compare_item_id) !== -1) return true;
      return false;
    });
  }

  // Update count badges
  if (countBadge) countBadge.textContent = relatedNotes.length + ' 条记录';
  if (countOverview) countOverview.textContent = relatedNotes.length + ' 条';

  // Render
  container.innerHTML = '';
  if (relatedNotes.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>暂无相关装修手册记录</p></div>';
    return;
  }

  relatedNotes.forEach(function(note) {
    var tags = [];
    try { 
      var rawTags = note.tags;
      if (typeof rawTags === 'string') {
        tags = JSON.parse(rawTags || '[]');
      } else if (Array.isArray(rawTags)) {
        tags = rawTags;
      }
    } catch(e) { tags = []; }
    // 确保 tags 是有效数组且有内容
    var validTags = Array.isArray(tags) ? tags.filter(function(t) { return t && t.trim(); }) : [];
    var tagsHtml = validTags.length > 0 ? '<div class="manual-entry-tags">' + validTags.slice(0, 3).map(function(t) {
      return '<span class="note-tag">' + t.trim() + '</span>';
    }).join('') + '</div>' : '';

    var catLabel = getCategoryNameById(note.category_id);
    var ciLabel = getCompareItemLabelById(note.compare_item_id);
    var chipsHtml = '';
    if (catLabel) chipsHtml += '<span class="note-link-chip">' + catLabel + '</span>';
    if (ciLabel) chipsHtml += '<span class="note-link-chip" style="background:rgba(37,99,235,.12);color:var(--accent-blue);">' + ciLabel + '</span>';

    var stageLabel = stageNameMap[note.stage] || note.stage || '设计';
    var contentSnippet = note.content ? note.content.substring(0, 120) + (note.content.length > 120 ? '...' : '') : '';

    var entryEl = document.createElement('div');
    entryEl.className = 'manual-entry';
    entryEl.innerHTML =
      '<div class="manual-entry-header">' +
        '<span class="manual-entry-date">' + stageLabel + '</span>' +
      '</div>' +
      '<div class="manual-entry-title">' + (note.title || '') + '</div>' +
      (contentSnippet ? '<div class="manual-entry-content">' + contentSnippet.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>' : '') +
      tagsHtml +
      (chipsHtml ? '<div class="manual-entry-links">' + chipsHtml + '</div>' : '');
    container.appendChild(entryEl);
  });
}

// 从 API 加载中央空调方案
function loadAcPlansFromAPI() {
  // 从 URL 获取分类 ID（默认中央空调分类 ID=1 或从页面属性读取）
  var categoryId = window.acCategoryId;
  if (!categoryId) {
    showToast('请先添加中央空调分类');
    return;
  }

  fetch(apiBase + '/api/compare-items/' + categoryId)
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') {
        showToast(data.message || '加载方案失败');
        return;
      }
      acPlans = data.data || [];
      renderAcPlanTable();
      renderAcPlanCards();
      updatePlanCount();
      updateAirconOverview(acPlans.find(function(p) { return p.is_selected; }) || null);
    })
    .catch(function(err) {
      console.error('Failed to load AC plans:', err);
      showToast('加载方案失败');
    });
}

// Load topbar budget data from API (called on every page)
function loadTopbarBudgetFromAPI() {
  fetch(apiBase + '/api/budget/summary')
    .then(function(res) { return res.json(); })
    .then(function(resp) {
      if (resp.status === 'error') return;
      var summary = resp.data || {};
      projectState.totalBudget = summary.total_budget || 0;
      projectState.actualSpent = summary.actual_spent || 0;
      projectState.estimatedCost = summary.estimated_cost || 0;
      updateBudgetDisplay();
    })
    .catch(function(err) {
      console.error('Failed to load topbar budget:', err);
    });
}

// ═══════════════════════════════════════════
// 预算控制页 (/decoration/budget)
// ═══════════════════════════════════════════

// Budget data (from API — no fake data)
var budgetCategories = [];  // renamed: each item has: category_id, category_name, plan_name, budget, spent, has_plan, status

// Expense records (from API — no fake data)
var expenseRecords = [];

var currentBudgetFilter = 'all';

// Format number
function formatBudgetNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Calculate totals
function calculateTotals() {
  var totalBudget = projectState.totalBudget || 0;
  var totalEstimated = 0;
  var totalSpent = 0;
  var overCount = 0;
  var savedAmount = 0;

  budgetCategories.forEach(function(cat) {
    totalEstimated += cat.budget || 0;
    totalSpent += cat.spent || 0;
    if (cat.status === 'over') {
      overCount++;
      savedAmount -= (cat.spent - cat.budget);
    } else if (cat.status === 'saved' && cat.has_plan) {
      savedAmount += (cat.budget - cat.spent);
    }
  });

  var usagePercent = totalBudget > 0 ? (totalSpent / totalBudget * 100).toFixed(1) : '0.0';
  var estimatedPercent = totalBudget > 0 ? (totalEstimated / totalBudget * 100).toFixed(1) : '0.0';

  return {
    totalBudget: totalBudget,
    totalEstimated: totalEstimated,
    totalSpent: totalSpent,
    remaining: totalBudget - totalSpent,
    estimatedLeft: totalBudget - totalEstimated,
    usagePercent: usagePercent,
    estimatedPercent: estimatedPercent,
    overCount: overCount,
    savedAmount: savedAmount
  };
}

// Update cockpit display
function updateCockpit() {
  var totals = calculateTotals();
  var hasBudget = totals.totalBudget > 0;

  // Update cockpit values
  var estimatedEl = document.getElementById('cockpitEstimated');
  var spentEl = document.getElementById('cockpitSpent');
  var remainingEl = document.getElementById('cockpitRemaining');
  var estimatedLeftEl = document.getElementById('cockpitEstimatedLeft');
  var usagePercentEl = document.getElementById('cockpitUsagePercent');
  var usageBarEl = document.getElementById('cockpitUsageBar');

  if (estimatedEl) estimatedEl.textContent = '¥' + formatBudgetNumber(totals.totalEstimated);
  if (spentEl) {
    spentEl.textContent = '¥' + formatBudgetNumber(totals.totalSpent);
    spentEl.className = 'cockpit-secondary-value ' + (hasBudget && totals.totalSpent > totals.totalBudget ? 'over' : 'saved');
  }
  if (remainingEl) {
    if (hasBudget) {
      remainingEl.textContent = '¥' + formatBudgetNumber(totals.remaining);
      remainingEl.className = 'cockpit-secondary-value ' + (totals.remaining < 0 ? 'over' : 'saved');
    } else {
      remainingEl.textContent = '未设置';
      remainingEl.className = 'cockpit-secondary-value';
    }
  }
  if (estimatedLeftEl) {
    if (hasBudget) {
      estimatedLeftEl.textContent = '¥' + formatBudgetNumber(totals.estimatedLeft);
      estimatedLeftEl.className = 'cockpit-secondary-value ' + (totals.estimatedLeft < 0 ? 'over' : '');
    } else {
      estimatedLeftEl.textContent = '未设置';
      estimatedLeftEl.className = 'cockpit-secondary-value';
    }
  }
  if (usagePercentEl) usagePercentEl.textContent = totals.usagePercent + '%';
  if (usageBarEl) usageBarEl.style.width = totals.usagePercent + '%';

  // Update legend
  var legendItems = document.querySelectorAll('.legend-item');
  if (legendItems[0]) legendItems[0].innerHTML = '<span class="legend-dot actual"></span>实际花费 ' + totals.usagePercent + '%';
  if (legendItems[1]) legendItems[1].innerHTML = '<span class="legend-dot estimated"></span>预计花费 ' + totals.estimatedPercent + '%';

  // Update stat cards
  var statCards = document.querySelectorAll('.budget-stat-card');
  if (statCards[0]) {
    statCards[0].querySelector('.budget-stat-value').textContent = '¥' + formatBudgetNumber(totals.totalEstimated);
  }
  if (statCards[1]) {
    statCards[1].querySelector('.budget-stat-value').textContent = '¥' + formatBudgetNumber(totals.totalSpent);
  }
  if (statCards[2]) {
    statCards[2].querySelector('.budget-stat-value').textContent = totals.overCount + ' 个';
    statCards[2].querySelector('.budget-stat-note').textContent = totals.overCount > 0 ? '' : '暂无超支分类';
  }
  if (statCards[3]) {
    statCards[3].querySelector('.budget-stat-value').textContent = '¥' + formatBudgetNumber(totals.savedAmount);
    statCards[3].querySelector('.budget-stat-note').textContent = totals.savedAmount > 0 ? '' : '暂无节省分类';
  }

  // Update status text
  var statusText = document.getElementById('cockpitStatusText');
  if (statusText) {
    if (!hasBudget) {
      statusText.textContent = '请先设置总预算，再添加分类方案和实际花费记录。';
    } else if (totals.overCount > 0) {
      statusText.textContent = '有 ' + totals.overCount + ' 个分类超支，请注意控制预算。';
    } else {
      statusText.textContent = '预算状态良好，实际支出低于总预算。';
    }
  }
}

// 从预算页跳转到分类
function goToCategoryFromBudget(categoryName) {
  if (categoryName === '中央空调') {
    window.location.href = '/decoration/compare/air-conditioner';
  } else if (categoryName) {
    // 跳转到分类比较页并定位到该分类
    navigateToCategory(categoryName);
  } else {
    window.location.href = '/decoration/compare';
  }
}

// Render budget table
function renderBudgetTable() {
  var tbody = document.getElementById('budgetTableBody');
  var emptyEl = document.getElementById('budgetTableEmpty');
  if (!tbody) return;
  tbody.innerHTML = '';

  var filtered = budgetCategories.filter(function(cat) {
    if (currentBudgetFilter === 'all') return true;
    if (currentBudgetFilter === 'over') return cat.status === 'over';
    if (currentBudgetFilter === 'saved') return cat.status === 'saved';
    if (currentBudgetFilter === 'equal') return cat.status === 'equal';
    if (currentBudgetFilter === 'pending') return !cat.has_plan;
    return true;
  });

  if (emptyEl) emptyEl.style.display = filtered.length === 0 ? 'block' : 'none';
  if (filtered.length === 0) return;

  filtered.forEach(function(cat) {
    var delta = cat.spent - cat.budget;
    var deltaClass = delta > 0 ? 'negative' : delta < 0 ? 'positive' : 'neutral';
    var deltaText = cat.spent === 0 ? '-' : (delta > 0 ? '-' : '+') + formatBudgetNumber(Math.abs(delta));

    var usageRate = cat.budget > 0 ? (cat.spent / cat.budget * 100).toFixed(0) : 0;
    var usageClass = usageRate > 100 ? 'over' : usageRate < 80 ? 'saved' : 'normal';

    var statusLabels = {
      'over': '超支',
      'saved': '节省',
      'equal': '持平',
      'pending': '未开始'
    };
    var statusClasses = {
      'over': 'status-over',
      'saved': 'status-selected',
      'equal': 'status-not-started',
      'pending': 'status-not-started'
    };

    var row = document.createElement('tr');
    row.className = cat.status === 'over' ? 'budget-row-over' : cat.status === 'saved' ? 'budget-row-saved' : !cat.has_plan ? 'budget-row-pending' : '';
    row.innerHTML =
      '<td><strong>' + (cat.category_name || cat.name || '') + '</strong></td>' +
      '<td style="color:' + (cat.plan_name && cat.plan_name !== '未选方案' ? 'var(--text-secondary)' : 'var(--text-muted)') + ';">' + (cat.plan_name || '待选方案') + '</td>' +
      '<td style="font-weight:600;">' + (cat.budget > 0 ? '¥' + formatBudgetNumber(cat.budget) : '-') + '</td>' +
      '<td style="font-weight:600;">' + (cat.spent > 0 ? '¥' + formatBudgetNumber(cat.spent) : '-') + '</td>' +
      '<td><span class="budget-delta ' + deltaClass + '">' + deltaText + '</span></td>' +
      '<td>' +
        '<div class="usage-rate">' +
          '<div class="usage-bar">' +
            '<div class="usage-bar-fill ' + usageClass + '" style="width:' + Math.min(usageRate, 100) + '%;"></div>' +
          '</div>' +
          '<span style="font-size:.75rem;color:var(--text-muted);">' + (cat.spent > 0 ? usageRate + '%' : '-') + '</span>' +
        '</div>' +
      '</td>' +
      '<td><span class="status-tag ' + statusClasses[cat.status] + '">' + statusLabels[cat.status] + '</span></td>' +
      '<td>' +
        '<button class="btn btn-ghost btn-sm" onclick="goToCategoryFromBudget(\'' + (cat.category_name || '') + '\')">查看</button>' +
        '<button class="btn btn-ghost btn-sm" style="margin-left:4px;" onclick="openExpenseModalForCategory(\'' + (cat.category_name || '') + '\')">记一笔</button>' +
      '</td>';
    tbody.appendChild(row);
  });
}

// Filter budget rows
function filterBudgetRows(filter) {
  currentBudgetFilter = filter;
  document.querySelectorAll('.budget-filter-tab').forEach(function(tab) {
    tab.classList.toggle('active', tab.dataset.filter === filter);
  });
  renderBudgetTable();
}

// Group expenses by month
function groupExpensesByMonth() {
  var groups = {};
  expenseRecords.forEach(function(exp) {
    var month = exp.date.substring(0, 7); // YYYY-MM
    var monthLabel = exp.date.substring(0, 4) + '年' + parseInt(exp.date.substring(5, 7)) + '月';
    if (!groups[month]) {
      groups[month] = { label: monthLabel, records: [], total: 0 };
    }
    groups[month].records.push(exp);
    groups[month].total += exp.amount;
  });
  return groups;
}

// Render expense records
function renderExpenseRecords() {
  var container = document.getElementById('expenseMonthGroups');
  if (!container) return;

  var groups = groupExpensesByMonth();
  var monthKeys = Object.keys(groups).sort().reverse();

  // Clear existing content but keep empty state div
  var emptyEl = document.getElementById('expenseEmpty');
  container.innerHTML = '';
  if (emptyEl) container.appendChild(emptyEl);

  if (monthKeys.length === 0) return;

  monthKeys.forEach(function(month) {
    var group = groups[month];
    var groupEl = document.createElement('div');
    groupEl.className = 'expense-month-group';

    groupEl.innerHTML =
      '<div class="expense-month-header">' +
        '<span class="expense-month-title">' + group.label + '</span>' +
        '<span class="expense-month-total">¥' + formatBudgetNumber(group.total) + '</span>' +
      '</div>' +
      '<div class="expense-flow-list" id="expenseList-' + month + '"></div>';

    container.appendChild(groupEl);

    var listEl = groupEl.querySelector('.expense-flow-list');
    group.records.sort(function(a, b) { return b.date.localeCompare(a.date); }).forEach(function(exp) {
      var itemEl = document.createElement('div');
      itemEl.className = 'expense-flow-item';
      itemEl.style.cursor = 'pointer';
      itemEl.dataset.expenseId = exp.id || exp._id || '';
      itemEl.onclick = function(e) {
        console.log('Expense item clicked, id:', exp.id || exp._id);
        openExpenseDetailModal(exp.id || exp._id);
      };

      var day = exp.date.substring(8, 10);
      var monthShort = exp.date.substring(5, 7) + '月';
      var chipsHtml = '';
      if (exp.category) {
        chipsHtml += '<span class="note-tag" style="margin-right:4px;">' + exp.category + '</span>';
      }
      if (exp.compare_item_label) {
        chipsHtml += '<span class="note-tag" style="background:rgba(37,99,235,.12);color:var(--accent-blue);margin-right:4px;">' + exp.compare_item_label + '</span>';
      }

      itemEl.innerHTML =
        '<div class="expense-flow-date">' +
          '<div class="expense-flow-day">' + day + '</div>' +
          '<div class="expense-flow-month">' + monthShort + '</div>' +
        '</div>' +
        '<div class="expense-flow-content">' +
          '<div class="expense-flow-category">' + chipsHtml + '</div>' +
          '<div class="expense-flow-name">' + exp.name + '</div>' +
          '<div class="expense-flow-meta">' +
            '<span class="expense-flow-method">' + exp.method + '</span>' +
            '<span class="expense-flow-receipt' + (exp.receipt ? '' : ' pending') + '">' + (exp.receipt ? '已上传票据' : '待上传票据') + '</span>' +
          '</div>' +
        '</div>' +
        '<div class="expense-flow-amount">¥' + formatBudgetNumber(exp.amount) + '</div>';

      listEl.appendChild(itemEl);
    });
  });
}

// Render recent expenses for home page (shows last 5)
function renderHomeRecentExpenses() {
  var container = document.getElementById('homeRecentExpenses');
  if (!container) return;
  
  // Get recent 5 expenses (already sorted by date desc in groupExpensesByMonth)
  var recent = expenseRecords.slice(0, 5);
  
  if (recent.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>暂无花费记录。</p></div>';
    return;
  }
  
  var html = '<div class="recent-expense-list">';
  recent.forEach(function(exp) {
    var day = exp.date ? exp.date.substring(8, 10) : '--';
    var monthShort = exp.date ? exp.date.substring(5, 7) + '月' : '';
    html +=
      '<div class="recent-expense-item" onclick="openExpenseDetailModal(\'' + (exp.id || exp._id) + '\')">' +
        '<div class="recent-expense-date">' +
          '<div class="recent-expense-day">' + day + '</div>' +
          '<div class="recent-expense-month">' + monthShort + '</div>' +
        '</div>' +
        '<div class="recent-expense-info">' +
          '<div class="recent-expense-category">' + (exp.category || '未分类') + '</div>' +
          '<div class="recent-expense-name">' + exp.name + '</div>' +
        '</div>' +
        '<div class="recent-expense-amount">¥' + formatBudgetNumber(exp.amount) + '</div>' +
      '</div>';
  });
  html += '</div>';
  container.innerHTML = html;
}

// Render home page category status (shows categories with plans selected)
function renderHomeCategoryStatus() {
  var container = document.getElementById('homeCategoryStatus');
  if (!container) return;
  
  // Get categories from lookup data
  var categories = window.renovaLookupData && window.renovaLookupData.categories ? window.renovaLookupData.categories : [];
  
  if (categories.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>暂无装修分类，请先添加分类。</p></div>';
    return;
  }
  
  // Count categories with selected plans
  var selectedCount = categories.filter(function(c) { return c.selected_plan_id; }).length;
  
  // Update hero stat
  var statValueEl = document.querySelector('.hero-project-card .stat-value.blue');
  if (statValueEl) {
    statValueEl.textContent = selectedCount;
  }
  var statMetaEl = document.querySelector('.hero-project-card .stat-meta');
  if (statMetaEl) {
    statMetaEl.textContent = '个分类已确定';
  }
  
  // Show categories with status
  var html = '<div class="home-category-list">';
  categories.forEach(function(cat) {
    var statusMap = { 'comparing': '对比中', 'selected': '已选定', 'pending': '待处理', 'done': '已完成' };
    var status = statusMap[cat.status] || cat.status || '';
    var statusClass = cat.status === 'selected' ? 'selected' : cat.status === 'comparing' ? 'comparing' : 'pending';
    html +=
      '<div class="home-category-item" onclick="location.href=\'/decoration/compare?cat=' + cat.id + '\'">' +
        '<span class="home-category-icon">' + (cat.icon || '📦') + '</span>' +
        '<div class="home-category-info">' +
          '<div class="home-category-name">' + (cat.name || '未命名') + '</div>' +
          '<div class="home-category-meta">' + (cat.group_name || '') + '</div>' +
        '</div>' +
        '<span class="home-category-status ' + statusClass + '">' + status + '</span>' +
      '</div>';
  });
  html += '</div>';
  container.innerHTML = html;
}

// Render home page todo list (shows ongoing tasks)
function renderHomeTodoList() {
  var container = document.getElementById('homeTodoList');
  var badge = document.getElementById('homeTodoBadge');
  if (!container) return;

  // Filter ongoing tasks
  var ongoingTasks = progressTasks.filter(function(t) {
    return t.status === 'ongoing' || t.status === 'pending' || t.status === 'review';
  });

  // Update badge
  if (badge) {
    badge.textContent = ongoingTasks.length + ' 项待处理';
  }

  if (ongoingTasks.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>暂无待办事项。</p></div>';
    return;
  }

  // Show max 5 tasks
  var showTasks = ongoingTasks.slice(0, 5);
  var html = '<div class="home-todo-list">';
  showTasks.forEach(function(task) {
    var stageLabels = { 'design': '设计', 'demolition': '拆改', 'water': '水电', 'mud': '泥工', 'wood': '木工', 'paint': '油漆', 'install': '安装', 'soft': '软装' };
    var statusLabels = { 'pending': '待开始', 'ongoing': '进行中', 'review': '待验收', 'done': '已完成' };
    var stageLabel = stageLabels[task.stage] || task.stage || '';
    var statusLabel = statusLabels[task.status] || task.status || '';
    var catName = '';
    if (task.category_id && window.renovaLookupData && window.renovaLookupData.categories) {
      var cat = window.renovaLookupData.categories.find(function(c) { return c.id === task.category_id; });
      if (cat) catName = cat.name;
    }
    html +=
      '<div class="home-todo-item" onclick="location.href=\'/decoration/progress\'">' +
        '<div class="home-todo-status ' + task.status + '"></div>' +
        '<div class="home-todo-content">' +
          '<div class="home-todo-title">' + (task.title || '未命名任务') + '</div>' +
          '<div class="home-todo-meta">' +
            (catName ? '<span class="home-todo-tag">' + catName + '</span>' : '') +
            (stageLabel ? '<span class="home-todo-tag stage">' + stageLabel + '</span>' : '') +
            '<span class="home-todo-status-label">' + statusLabel + '</span>' +
          '</div>' +
        '</div>' +
      '</div>';
  });
  html += '</div>';
  container.innerHTML = html;
}

// Render category analysis bars
function renderCategoryBars() {
  var container = document.getElementById('categoryBars');
  var emptyEl = document.getElementById('categoryBarsEmpty');
  if (!container) return;
  container.innerHTML = '';

  if (budgetCategories.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    return;
  }
  if (emptyEl) emptyEl.style.display = 'none';

  var maxBudget = Math.max.apply(null, budgetCategories.map(function(c) { return c.budget || 0; }));

  budgetCategories.forEach(function(cat) {
    var barEl = document.createElement('div');
    barEl.className = 'category-bar-item';

    var percent = (cat.budget / maxBudget * 100).toFixed(1);
    var barClass = cat.status === 'over' ? 'over' : cat.status === 'saved' ? 'saved' : !cat.has_plan ? 'pending' : 'normal';
    var valueClass = cat.status === 'over' ? 'over' : cat.status === 'saved' ? 'saved' : '';

    barEl.innerHTML =
      '<span class="category-bar-label">' + (cat.category_name || cat.name || '') + '</span>' +
      '<div class="category-bar-track">' +
        '<div class="category-bar-fill ' + barClass + '" style="width:' + percent + '%;">' +
          '<span class="category-bar-amount">' + (cat.spent > 0 ? '¥' + formatBudgetNumber(cat.spent) : '¥' + formatBudgetNumber(cat.budget)) + '</span>' +
        '</div>' +
      '</div>' +
      '<span class="category-bar-value ' + valueClass + '">' + (cat.spent > 0 ? '¥' + formatBudgetNumber(cat.spent) : '待定') + '</span>';

    container.appendChild(barEl);
  });
}

// Open expense modal
function openExpenseModal() {
  var dateInput = document.getElementById('expenseDate');
  var categorySelect = document.getElementById('expenseCategory');
  var nameInput = document.getElementById('expenseName');
  var amountInput = document.getElementById('expenseAmount');
  var methodSelect = document.getElementById('expenseMethod');
  var payeeInput = document.getElementById('expensePayee');
  var noteInput = document.getElementById('expenseNote');
  var compareItemSelect = document.getElementById('expenseCompareItem');

  if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
  if (nameInput) nameInput.value = '';
  if (amountInput) amountInput.value = '';
  if (methodSelect) methodSelect.selectedIndex = 0;
  if (payeeInput) payeeInput.value = '';
  if (noteInput) noteInput.value = '';
  if (compareItemSelect) compareItemSelect.selectedIndex = 0;

  // Populate lookup dropdowns (real categories and compare items)
  if (!window.renovaLookupData || !window.renovaLookupData.categories || window.renovaLookupData.categories.length === 0) {
    loadLookupData(function() { fillCategorySelects(); fillCompareItemSelects(); });
  } else {
    fillCategorySelects();
    fillCompareItemSelects();
  }

  openModal('expenseModal');
}

// Open expense modal with pre-filled category
function openExpenseModalForCategory(categoryName) {
  openExpenseModal();
  // After openExpenseModal populates the dropdown, find the category ID by name and select it
  if (categoryName && window.renovaLookupData && window.renovaLookupData.categories) {
    var matched = window.renovaLookupData.categories.find(function(c) { return c.name === categoryName; });
    if (matched) {
      var categorySelect = document.getElementById('expenseCategory');
      if (categorySelect) {
        categorySelect.value = matched.id;
      }
    }
  }
}

// Save expense (via API)
function saveExpense() {
  var dateInput = document.getElementById('expenseDate');
  var categorySelect = document.getElementById('expenseCategory');
  var nameInput = document.getElementById('expenseName');
  var amountInput = document.getElementById('expenseAmount');
  var methodSelect = document.getElementById('expenseMethod');
  var payeeInput = document.getElementById('expensePayee');
  var noteInput = document.getElementById('expenseNote');
  var compareItemSelect = document.getElementById('expenseCompareItem');

  var date = dateInput ? dateInput.value : '';
  var name = nameInput ? nameInput.value.trim() : '';
  var amount = amountInput ? parseInt(amountInput.value) || 0 : 0;
  var method = methodSelect ? methodSelect.value : '';
  var payee = payeeInput ? payeeInput.value.trim() : '';
  var note = noteInput ? noteInput.value.trim() : '';

  if (!date) { showToast('请选择支出日期'); return; }
  if (!name) { showToast('请填写支出名称'); return; }
  if (!amount) { showToast('请填写金额'); return; }

  var payload = {
    title: name,
    amount: amount,
    pay_date: date,
    pay_method: method || '银行卡',
    vendor: payee,
    note: note,
    category_id: parseInt(categorySelect ? categorySelect.value : '') || null,
    compare_item_id: parseInt(compareItemSelect ? compareItemSelect.value : '') || null
  };

  fetch(apiBase + '/api/expenses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    closeModal('expenseModal');
    showToast('已新增花费记录');
    // 先加载预算摘要，再加载花费记录（确保依赖关系正确）
    loadBudgetSummaryFromAPI(function() {
      loadExpensesFromAPI();
      updateBudgetDisplay();
    });
  })
  .catch(function(err) {
    console.error('Failed to save expense:', err);
    showToast('保存失败');
  });
}

// Open expense detail modal
function openExpenseDetailModal(expenseId) {
  console.log('openExpenseDetailModal called with:', expenseId);
  // Fetch expense detail from API
  fetch(apiBase + '/api/expenses/' + expenseId)
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') {
        showToast('获取详情失败');
        return;
      }
      showExpenseDetail(data.data);
    })
    .catch(function(err) {
      console.error('Failed to load expense detail:', err);
      showToast('获取详情失败');
    });
}

function showExpenseDetail(exp) {
  var expId = exp.id || exp._id || '';
  
  // Resolve category name
  var catName = '';
  if (exp.category_id && budgetCategories.length > 0) {
    var matched = budgetCategories.find(function(c) { return c.category_id === exp.category_id; });
    if (matched) catName = matched.category_name;
  }
  
  // Resolve compare_item label
  var ciLabel = '';
  if (exp.compare_item_id && window.renovaLookupData && window.renovaLookupData.compare_items) {
    var ci = window.renovaLookupData.compare_items.find(function(item) { return item.id === exp.compare_item_id; });
    if (ci) ciLabel = (ci.brand || '') + (ci.model ? ' ' + ci.model : '');
  }
  
  document.getElementById('expenseDetailId').value = expId;
  document.getElementById('expenseDetailTitle').textContent = exp.title || '费用详情';
  document.getElementById('expenseDetailSubtitle').textContent = '查看支出记录';
  document.getElementById('expenseDetailDate').textContent = exp.pay_date ? formatDate(exp.pay_date) : '-';
  document.getElementById('expenseDetailCategory').textContent = catName || '-';
  document.getElementById('expenseDetailName').textContent = exp.title || '-';
  document.getElementById('expenseDetailAmount').textContent = '¥' + formatBudgetNumber(exp.amount || 0);
  document.getElementById('expenseDetailMethod').textContent = exp.pay_method || '-';
  document.getElementById('expenseDetailPayee').textContent = exp.vendor || '-';
  document.getElementById('expenseDetailCompareItem').textContent = ciLabel || '-';
  
  var noteEl = document.getElementById('expenseDetailNote');
  var noteRow = document.getElementById('expenseDetailNoteRow');
  if (exp.note) {
    noteEl.textContent = exp.note;
    noteRow.style.display = 'flex';
  } else {
    noteEl.textContent = '-';
    noteRow.style.display = 'none';
  }
  
  openModal('expenseDetailModal');
}

// Delete expense
function deleteExpense() {
  var expenseId = document.getElementById('expenseDetailId').value;
  if (!expenseId) return;
  
  if (!confirm('确定要删除这条花费记录吗？')) return;
  
  fetch(apiBase + '/api/expenses/' + expenseId, {
    method: 'DELETE'
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '删除失败');
      return;
    }
    closeModal('expenseDetailModal');
    showToast('已删除花费记录');
    loadBudgetSummaryFromAPI();
    loadExpensesFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to delete expense:', err);
    showToast('删除失败');
  });
}

// Open expense modal for editing
var currentEditExpenseId = null;
var currentEditExpenseData = null;

function openExpenseModalForEdit() {
  var expenseId = document.getElementById('expenseDetailId').value;
  if (!expenseId) return;
  
  // Fetch latest data
  fetch(apiBase + '/api/expenses/' + expenseId)
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') {
        showToast('获取详情失败');
        return;
      }
      currentEditExpenseId = expenseId;
      currentEditExpenseData = data.data;
      populateEditForm(data.data);
      toggleEditMode(true);
    })
    .catch(function(err) {
      console.error('Failed to load expense for edit:', err);
      showToast('获取详情失败');
    });
}

function populateEditForm(exp) {
  document.getElementById('expenseEditId').value = exp.id;
  document.getElementById('expenseEditDate').value = exp.pay_date || '';
  document.getElementById('expenseEditName').value = exp.title || '';
  document.getElementById('expenseEditAmount').value = exp.amount || '';
  document.getElementById('expenseEditMethod').value = exp.pay_method || '';
  document.getElementById('expenseEditPayee').value = exp.vendor || '';
  document.getElementById('expenseEditNote').value = exp.note || '';
  
  // Set category
  var categorySelect = document.getElementById('expenseEditCategory');
  if (exp.category_id) {
    categorySelect.value = exp.category_id;
  }
  
  // Set compare item
  var compareItemSelect = document.getElementById('expenseEditCompareItem');
  if (exp.compare_item_id) {
    compareItemSelect.value = exp.compare_item_id;
  }
}

function toggleEditMode(editMode) {
  var viewEl = document.getElementById('expenseDetailView');
  var editEl = document.getElementById('expenseDetailEdit');
  var editBtn = document.getElementById('expenseDetailEditBtn');
  var saveBtn = document.getElementById('expenseDetailSaveBtn');
  var cancelBtn = document.getElementById('expenseDetailCancelBtn');
  var titleEl = document.getElementById('expenseDetailTitle');
  
  if (editMode) {
    viewEl.style.display = 'none';
    editEl.style.display = 'block';
    editBtn.style.display = 'none';
    saveBtn.style.display = '';
    cancelBtn.style.display = '';
    titleEl.textContent = '修改费用';
    document.getElementById('expenseDetailSubtitle').textContent = '编辑支出记录';
  } else {
    viewEl.style.display = 'block';
    editEl.style.display = 'none';
    editBtn.style.display = '';
    saveBtn.style.display = 'none';
    cancelBtn.style.display = 'none';
    titleEl.textContent = currentEditExpenseData ? currentEditExpenseData.title : '费用详情';
    document.getElementById('expenseDetailSubtitle').textContent = '查看支出记录';
  }
}

function cancelExpenseEdit() {
  currentEditExpenseId = null;
  currentEditExpenseData = null;
  toggleEditMode(false);
}

function saveExpenseEdit() {
  var expenseId = document.getElementById('expenseEditId').value;
  if (!expenseId) return;
  
  var dateInput = document.getElementById('expenseEditDate');
  var nameInput = document.getElementById('expenseEditName');
  var amountInput = document.getElementById('expenseEditAmount');
  var methodSelect = document.getElementById('expenseEditMethod');
  var payeeInput = document.getElementById('expenseEditPayee');
  var noteInput = document.getElementById('expenseEditNote');
  var categorySelect = document.getElementById('expenseEditCategory');
  var compareItemSelect = document.getElementById('expenseEditCompareItem');
  
  var date = dateInput ? dateInput.value : '';
  var name = nameInput ? nameInput.value.trim() : '';
  var amount = amountInput ? parseInt(amountInput.value) || 0 : 0;
  var method = methodSelect ? methodSelect.value : '';
  var payee = payeeInput ? payeeInput.value.trim() : '';
  var note = noteInput ? noteInput.value.trim() : '';
  
  if (!date) { showToast('请选择支出日期'); return; }
  if (!name) { showToast('请填写支出名称'); return; }
  if (!amount) { showToast('请填写金额'); return; }
  
  var payload = {
    title: name,
    amount: amount,
    pay_date: date,
    pay_method: method || '银行卡',
    vendor: payee,
    note: note,
    category_id: parseInt(categorySelect ? categorySelect.value : '') || null,
    compare_item_id: parseInt(compareItemSelect ? compareItemSelect.value : '') || null
  };
  
  fetch(apiBase + '/api/expenses/' + expenseId, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    showToast('已保存修改');
    currentEditExpenseId = null;
    currentEditExpenseData = data.data;
    toggleEditMode(false);
    showExpenseDetail(data.data);
    loadBudgetSummaryFromAPI();
    loadExpensesFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to save expense:', err);
    showToast('保存失败');
  });
}

// Initialize home page: load recent expenses and tasks
function initHomePage() {
  if (document.getElementById('homeRecentExpenses') || document.getElementById('homeTodoList') || document.getElementById('homeCategoryStatus')) {
    loadLookupData(function() {
      // Update home category status after lookup data loaded
      renderHomeCategoryStatus();
      // Load tasks and expenses
      loadTasksFromAPI();
      loadExpensesFromAPI();
    });
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  var parts = dateStr.split('-');
  if (parts.length === 3) {
    return parts[0] + '年' + parseInt(parts[1]) + '月' + parseInt(parts[2]) + '日';
  }
  return dateStr;
}

// Initialize budget page: load summary + expenses from API
function initBudgetPage() {
  if (document.getElementById('budgetTable') || document.getElementById('expenseMonthGroups')) {
    loadLookupData(function() {
      // 先加载预算摘要（包含分类数据）
      loadBudgetSummaryFromAPI(function() {
        // 预算摘要加载完成后再加载花费记录
        loadExpensesFromAPI();
      });
    });
  }
}

// Load budget summary from API
function loadBudgetSummaryFromAPI(callback) {
  fetch(apiBase + '/api/budget/summary')
    .then(function(res) { return res.json(); })
    .then(function(resp) {
      if (resp.status === 'error') return;
      var summary = resp.data || {};
      budgetCategories = summary.budget_items || [];
      projectState.estimatedCost = summary.estimated_cost || 0;
      projectState.actualSpent = summary.actual_spent || 0;
      updateCockpit();
      renderBudgetTable();
      renderCategoryBars();
      updateBudgetDisplay(); // update topbar budget chips
      if (callback) callback();
    })
    .catch(function(err) {
      console.error('Failed to load budget summary:', err);
      if (callback) callback();
    });
}

// Load expenses from API
function loadExpensesFromAPI() {
  fetch(apiBase + '/api/expenses')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') return;
      // Update budgetCategories with per-category spending
      expenseRecords = (data.data || []).map(function(e) {
        // Resolve category name from budgetCategories
        var catName = '';
        if (e.category_id) {
          var matched = budgetCategories.find(function(c) { return c.category_id === e.category_id; });
          if (matched) catName = matched.category_name;
        }
        // Resolve compare_item label from lookup data
        var ciLabel = '';
        if (e.compare_item_id && window.renovaLookupData && window.renovaLookupData.compare_items) {
          var ci = window.renovaLookupData.compare_items.find(function(item) { return item.id === e.compare_item_id; });
          if (ci) ciLabel = (ci.brand || '') + (ci.model ? ' ' + ci.model : '');
        }
        return {
          id: e.id,
          date: e.pay_date || '',
          category: catName,
          category_id: e.category_id,
          name: e.title,
          amount: e.amount,
          method: e.pay_method || '银行卡',
          payee: e.vendor || '',
          receipt: false,
          note: e.note || '',
          compare_item_id: e.compare_item_id || null,
          compare_item_label: ciLabel
        };
      });

      // Sync spent back to budgetCategories
      var spentByCat = {};
      expenseRecords.forEach(function(exp) {
        if (exp.category_id) {
          spentByCat[exp.category_id] = (spentByCat[exp.category_id] || 0) + (exp.amount || 0);
        }
      });
      budgetCategories.forEach(function(cat) {
        cat.spent = spentByCat[cat.category_id] || 0;
        // Recalculate status
        if (!cat.has_plan) {
          cat.status = 'pending';
        } else if (cat.spent > cat.budget) {
          cat.status = 'over';
        } else if (cat.budget > 0 && cat.spent === cat.budget) {
          cat.status = 'equal';
        } else if (cat.spent > 0) {
          cat.status = 'saved';
        } else {
          cat.status = 'pending';
        }
      });

      projectState.actualSpent = data.total || 0;
      updateCockpit();
      updateBudgetDisplay();
      renderExpenseRecords();
      renderBudgetTable();
      renderCategoryBars();
      renderHomeRecentExpenses(); // update home page recent expenses
    })
    .catch(function(err) {
      console.error('Failed to load expenses:', err);
    });
}

// ═══════════════════════════════════════════
// 装修手册页 (/decoration/notes) — Shared Notes Functions
// ═══════════════════════════════════════════

// Stage name mapping
var stageNames = {
  'design': '设计阶段',
  'demolition': '拆改阶段',
  'water': '水电阶段',
  'mud': '泥工阶段',
  'wood': '木工阶段',
  'paint': '油漆阶段',
  'install': '安装阶段',
  'soft': '软装阶段'
};

// Notes data from API
var notesData = [];

// Load notes from API
function loadNotesFromAPI() {
  fetch(apiBase + '/api/notes')
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.status === 'error') return;
      notesData = data.data || [];
      // Use try-catch to ensure updateNoteStageCounts runs even if renderAllNotes fails
      try {
        renderAllNotes();
      } catch(e) {
        console.error('Error rendering notes:', e);
      }
      updateNoteStageCounts();
    })
    .catch(function(err) {
      console.error('Failed to load notes:', err);
    });
}

// Render all notes from API data
function renderAllNotes() {
  // 先清空所有章节的记录（保留空状态）
  document.querySelectorAll('.manual-chapter').forEach(function(ch) {
    var entries = ch.querySelectorAll('.manual-entry');
    entries.forEach(function(e) { e.remove(); });
    // 恢复空状态
    var emptyState = ch.querySelector('.empty-state');
    if (emptyState) emptyState.style.display = '';
  });

  notesData.forEach(function(note) {
    try {
      renderNoteEntry(note);
    } catch(e) {
      console.error('Error rendering note:', note.id, e);
    }
  });
}

// Render a single note entry into its chapter
function renderNoteEntry(note) {
  var stage = note.stage || 'design';
  var chapterId = 'chapter-' + stage;
  var chapter = document.getElementById(chapterId);
  if (!chapter) return;

  var tags = [];
  try { 
    var rawTags = note.tags;
    if (typeof rawTags === 'string') {
      tags = JSON.parse(rawTags || '[]');
    } else if (Array.isArray(rawTags)) {
      tags = rawTags;
    }
  } catch(e) { tags = []; }
  var validTags = Array.isArray(tags) ? tags.filter(function(t) { return t && t.trim(); }) : [];
  var tagsHtml = '';
  if (validTags.length > 0) {
    tagsHtml = '<div class="manual-entry-tags">' + validTags.map(function(t) {
      return '<span class="note-tag">' + t.trim() + '</span>';
    }).join('') + '</div>';
  }

  var fixedSourceUrl = fixUrl(note.source_url);
  var platformInfo = getPlatformInfo(note.source_url);
  var sourceHtml = '';
  if (platformInfo) {
    sourceHtml = '<div class="manual-entry-source">' +
      '<a href="' + fixedSourceUrl.replace(/"/g, '&quot;') + '" target="_blank" class="source-link-badge" ' +
         'style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:16px;' +
         'background:' + platformInfo.bg + ';color:' + platformInfo.color + ';' +
         'font-size:12px;font-weight:500;text-decoration:none;transition:all 0.2s;" ' +
         'onmouseover="this.style.transform=\'scale(1.05)\'" onmouseout="this.style.transform=\'scale(1)\'" ' +
         'title="打开 ' + platformInfo.name + ' 链接">' +
        '<span>' + platformInfo.icon + '</span>' +
        '<span>' + platformInfo.name + '</span>' +
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="opacity:0.6;"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"/></svg>' +
      '</a>' +
    '</div>';
  } else if (note.source_url) {
    // 不支持的平台，只显示链接按钮
    sourceHtml = '<div class="manual-entry-source">' +
      '<a href="' + fixedSourceUrl.replace(/"/g, '&quot;') + '" target="_blank" class="source-link-badge" ' +
         'style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:16px;' +
         'background:#F3F4F6;color:#6B7280;font-size:12px;font-weight:500;text-decoration:none;" ' +
         'title="打开链接">' +
        '<span>🔗</span><span>网页链接</span>' +
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="opacity:0.6;"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"/></svg>' +
      '</a>' +
    '</div>';
  }
  var today = note.created_at ? note.created_at.split('T')[0] : new Date().toISOString().split('T')[0];

  // 构建图片 HTML
  var imageUrls = [];
  try { imageUrls = JSON.parse(note.image_urls || '[]'); } catch(e) {}
  var imagesHtml = '';
  if (imageUrls.length > 0) {
    imagesHtml = '<div class="manual-entry-images" data-images=\'' + JSON.stringify(imageUrls).replace(/'/g, "&#39;") + '\'>';
    imageUrls.forEach(function(url) {
      if (url) {
        var escapedUrl = url.replace(/'/g, "&#39;");
        imagesHtml += '<img src="' + escapedUrl + '" alt="附件图片" style="max-width:200px;max-height:150px;border-radius:4px;margin:4px;cursor:pointer;" data-src="' + escapedUrl + '" onerror="this.style.display=&apos;none&apos;;this.nextSibling.textContent=&apos;图片无法加载&apos;;">';
      }
    });
    imagesHtml += '</div>';
  }

  var entryHtml = '<div class="manual-entry" data-note-id="' + note.id + '" data-stage="' + stage + '" data-title="' + (note.title || '').replace(/"/g, '&quot;') + '" data-date="' + today + '" data-source="' + (note.source_url || '').replace(/"/g, '&quot;') + '" data-tags="' + (note.tags || '').replace(/"/g, '&quot;') + '" data-content="' + (note.content || '').replace(/"/g, '&quot;') + '" data-category-id="' + (note.category_id || '') + '" data-task-id="' + (note.task_id || '') + '" data-compare-item-id="' + (note.compare_item_id || '') + '" data-image-urls=\'' + JSON.stringify(imageUrls).replace(/'/g, '&#39;') + '\'>' +
    '<div class="manual-entry-actions">' +
      '<button class="note-action-btn" onclick="openEditNoteModal(\'' + note.id + '\')" title="编辑"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/></svg></button>' +
      '<button class="note-action-btn danger" onclick="deleteNoteAPI(\'' + note.id + '\')" title="删除"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg></button>' +
    '</div>' +
    '<div class="manual-entry-header"><span class="manual-entry-date">' + today + '</span></div>' +
    '<div class="manual-entry-title">' + (note.title || '') + '</div>' +
    '<div class="manual-entry-content">' + (note.content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>' +
    sourceHtml +
    imagesHtml +
    tagsHtml +
    '<div class="manual-entry-links">' +
      (getCategoryNameById(note.category_id) ? '<span class="note-link-chip" onclick="window.location.href=\'/decoration/compare\'">' + getCategoryNameById(note.category_id) + '</span>' : '') +
      (getTaskTitleById(note.task_id) ? '<span class="note-link-chip" onclick="window.location.href=\'/decoration/progress\'">' + getTaskTitleById(note.task_id) + '</span>' : '') +
      (getCompareItemLabelById(note.compare_item_id) ? '<span class="note-link-chip" onclick="goToCompareItem(' + (note.compare_item_id || 0) + ', ' + (note.category_id || 0) + ')">' + getCompareItemLabelById(note.compare_item_id) + '</span>' : '') +
    '</div>' +
  '</div>';

  // Remove empty state if present
  var emptyState = chapter.querySelector('.empty-state');
  if (emptyState) emptyState.remove();

  // Expand chapter
  if (!chapter.classList.contains('open')) {
    var toggle = chapter.querySelector('.manual-chapter-toggle svg');
    chapter.classList.add('open');
    if (toggle) toggle.style.transform = 'rotate(0deg)';
  }

  var addBtn = chapter.querySelector('.manual-add-btn');
  var body = chapter.querySelector('.manual-chapter-body');
  if (body) {
    var tempDiv = document.createElement('div');
    tempDiv.innerHTML = entryHtml;
    var newEntry = tempDiv.firstElementChild;
    body.insertBefore(newEntry, addBtn);
    // 绑定图片点击事件（避免 HTML 属性中的引号转义问题）
    bindImageClickEvents(newEntry);
  }
}

// 绑定图片点击事件（从 data-images 属性读取图片列表）
function bindImageClickEvents(entry) {
  var imagesContainer = entry.querySelector('.manual-entry-images');
  if (!imagesContainer) return;
  
  var imagesData = imagesContainer.getAttribute('data-images');
  if (!imagesData) return;
  
  try {
    var images = JSON.parse(imagesData);
    var imagesJson = JSON.stringify(images);
    var imgs = imagesContainer.querySelectorAll('img');
    
    imgs.forEach(function(img) {
      img.style.cursor = 'pointer';
      img.addEventListener('click', function() {
        openImageLightbox(img.getAttribute('src'), imagesJson);
      });
    });
  } catch(e) {
    console.error('Error binding image click events:', e);
  }
}

// Open new note modal for a specific stage
function openNoteModalForStage(stage) {
  var stageSelect = document.getElementById('noteStage');
  if (stageSelect) {
    for (var i = 0; i < stageSelect.options.length; i++) {
      if (stageSelect.options[i].value === stage) {
        stageSelect.selectedIndex = i;
        break;
      }
    }
  }
  // Clear form
  var fields = ['noteTitle', 'noteSource', 'noteTags', 'noteContent'];
  fields.forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.value = '';
  });
  var relatedTask = document.getElementById('noteRelatedTask');
  if (relatedTask) relatedTask.selectedIndex = 0;
  var relatedCat = document.getElementById('noteRelatedCategory');
  if (relatedCat) relatedCat.selectedIndex = 0;
  var relatedCi = document.getElementById('noteRelatedCompareItem');
  if (relatedCi) relatedCi.selectedIndex = 0;
  // Clear image upload previews
  for (var i = 1; i <= 3; i++) {
    var fileInput = document.getElementById('noteImage' + i);
    var urlInput = document.getElementById('noteImageUrl' + i);
    var preview = document.getElementById('notePreview' + i);
    if (fileInput) fileInput.value = '';
    if (urlInput) urlInput.value = '';
    if (preview) {
      preview.innerHTML = '<span class="img-upload-placeholder">点击上传图片</span>';
      preview.classList.remove('has-image');
    }
  }
  // Populate lookup dropdowns
  if (!window.renovaLookupData || !window.renovaLookupData.categories || window.renovaLookupData.categories.length === 0) {
    loadLookupData(function() { fillCategorySelects(); fillTaskSelects(); fillCompareItemSelects(); });
  } else {
    fillCategorySelects();
    fillTaskSelects();
    fillCompareItemSelects();
  }
  openModal('noteEntryModal');
}

// Save new note entry (via API)
function saveNoteEntry() {
  var title = document.getElementById('noteTitle').value.trim();
  var stage = document.getElementById('noteStage').value;
  var source = fixUrl(document.getElementById('noteSource').value.trim());
  var tagsStr = document.getElementById('noteTags') ? document.getElementById('noteTags').value.trim() : '';
  var content = document.getElementById('noteContent').value.trim();
  var relatedTask = document.getElementById('noteRelatedTask');
  var relatedCategory = document.getElementById('noteRelatedCategory');
  var taskVal = relatedTask ? relatedTask.value : '';
  var catVal = relatedCategory ? relatedCategory.value : '';

  if (!title) { showToast('请填写记录标题'); return; }
  if (!content) { showToast('请填写记录内容'); return; }

  // Parse tags
  var tagsList = [];
  if (tagsStr) {
    tagsList = tagsStr.split(/[,，]/).map(function(t) { return t.trim(); }).filter(function(t) { return t; });
  }

  // 收集图片链接 (新布局)
  var imageUrls = [];
  var container = document.getElementById('noteImageContainer');
  if (container) {
    var hiddenInputs = container.querySelectorAll('input[type="hidden"]');
    hiddenInputs.forEach(function(input) {
      if (input.value && input.value.trim()) {
        imageUrls.push(input.value.trim());
      }
    });
  }

  var payload = {
    title: title,
    stage: stage,
    source_url: source,
    content: content,
    tags: tagsList,
    image_urls: imageUrls,
    category_id: parseInt(document.getElementById('noteRelatedCategory').value) || null,
    task_id: parseInt(document.getElementById('noteRelatedTask').value) || null,
    compare_item_id: parseInt(document.getElementById('noteRelatedCompareItem').value) || null
  };

  fetch(apiBase + '/api/notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    closeModal('noteEntryModal');
    showToast('手册记录已新增');
    loadNotesFromAPI();
    // Reset image upload container (新布局)
    var imgContainer = document.getElementById('noteImageContainer');
    if (imgContainer) {
      var addBtn = imgContainer.querySelector('.img-upload-add-btn');
      var items = imgContainer.querySelectorAll('.img-upload-item');
      items.forEach(function(item) { imgContainer.removeChild(item); });
    }
  })
  .catch(function(err) {
    console.error('Failed to save note:', err);
    showToast('保存失败');
  });
}
function openEditNoteModal(noteId) {
  var entry = document.querySelector('[data-note-id="' + noteId + '"]');
  if (!entry) return;

  document.getElementById('editNoteId').value = noteId;
  var titleEl = document.getElementById('editNoteTitle');
  if (titleEl) titleEl.value = entry.dataset.title || '';
  var sourceEl = document.getElementById('editNoteSource');
  if (sourceEl) sourceEl.value = entry.dataset.source || '';
  var tagsEl = document.getElementById('editNoteTags');
  if (tagsEl) {
    // 正确解析 tags：可能是 JSON 数组字符串 ['tag1','tag2'] 或空数组 '[]'
    var rawTags = entry.dataset.tags || '';
    var tagsValue = '';
    try {
      if (rawTags) {
        var parsed = JSON.parse(rawTags);
        if (Array.isArray(parsed)) {
          tagsValue = parsed.filter(function(t) { return t && t.trim(); }).join('、');
        } else {
          tagsValue = rawTags;
        }
      }
    } catch(e) {
      tagsValue = rawTags;
    }
    tagsEl.value = tagsValue;
  }
  var contentEl = document.getElementById('editNoteContent');
  if (contentEl) contentEl.value = entry.dataset.content || '';

  var stageSelect = document.getElementById('editNoteStage');
  var stage = entry.dataset.stage || 'design';
  if (stageSelect) {
    for (var i = 0; i < stageSelect.options.length; i++) {
      if (stageSelect.options[i].value === stage) {
        stageSelect.selectedIndex = i;
        break;
      }
    }
  }
  // Fill dropdowns with lookup data and set selected values
  fillCategorySelects();
  fillTaskSelects();
  fillCompareItemSelects();
  var catSelect = document.getElementById('editNoteRelatedCategory');
  if (catSelect) catSelect.value = entry.dataset.categoryId || '';
  var taskSelect = document.getElementById('editNoteRelatedTask');
  if (taskSelect) taskSelect.value = entry.dataset.taskId || '';
  var compareSelect = document.getElementById('editNoteRelatedCompareItem');
  if (compareSelect) compareSelect.value = entry.dataset.compareItemId || '';

  // 回显图片 URL - 显示预览图
  var imgUrls = [];
  if (entry.dataset.imageUrls) {
    try {
      imgUrls = JSON.parse(entry.dataset.imageUrls);
    } catch(e) {}
  }
  
  var container = document.getElementById('editNoteImageContainer');
  var addBtn = container.querySelector('.img-upload-add-btn');
  
  // 清除旧图片（保留添加按钮）
  var oldItems = container.querySelectorAll('.img-upload-item');
  oldItems.forEach(function(item) { container.removeChild(item); });
  
  // 添加已有图片
  imgUrls.forEach(function(url, idx) {
    if (url) {
      var imgItem = document.createElement('div');
      imgItem.className = 'img-upload-item';
      imgItem.innerHTML =
        '<input type="hidden" id="editImg_' + idx + '" value="' + url + '">' +
        '<div class="img-upload-preview has-image">' +
          '<img src="' + url + '" alt="预览">' +
          '<button type="button" class="img-upload-remove" onclick="removeNewImage(this, \'editImg_' + idx + '\')">' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>' +
          '</button>' +
        '</div>';
      container.insertBefore(imgItem, addBtn);
    }
  });

  openModal('editNoteModal');
}

// Save edited note (via API)
function saveEditedNote() {
  var noteId = document.getElementById('editNoteId').value;
  if (!noteId) return;

  var title = document.getElementById('editNoteTitle').value.trim();
  var stage = document.getElementById('editNoteStage').value;
  var source = fixUrl(document.getElementById('editNoteSource').value.trim());
  var tagsStr = document.getElementById('editNoteTags') ? document.getElementById('editNoteTags').value.trim() : '';
  var content = document.getElementById('editNoteContent').value.trim();

  if (!title) { showToast('请填写记录标题'); return; }

  var tagsList = [];
  if (tagsStr) {
    tagsList = tagsStr.split(/[,，]/).map(function(t) { return t.trim(); }).filter(function(t) { return t; });
  }

  // 收集图片链接 (新布局)
  var imageUrls = [];
  var container = document.getElementById('editNoteImageContainer');
  if (container) {
    var hiddenInputs = container.querySelectorAll('input[type="hidden"]');
    hiddenInputs.forEach(function(input) {
      if (input.value && input.value.trim()) {
        imageUrls.push(input.value.trim());
      }
    });
  }

  var payload = {
    title: title,
    stage: stage,
    source_url: source,
    content: content,
    tags: tagsList,
    image_urls: imageUrls,
    category_id: parseInt(document.getElementById('editNoteRelatedCategory').value) || null,
    task_id: parseInt(document.getElementById('editNoteRelatedTask').value) || null,
    compare_item_id: parseInt(document.getElementById('editNoteRelatedCompareItem').value) || null
  };

  fetch(apiBase + '/api/notes/' + noteId, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '保存失败');
      return;
    }
    closeModal('editNoteModal');
    showToast('手册记录已更新');
    loadNotesFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to update note:', err);
    showToast('保存失败');
  });
}

// Delete note via API
function deleteNoteAPI(noteId) {
  if (!confirm('确认删除这条装修手册记录吗？')) return;
  fetch(apiBase + '/api/notes/' + noteId, { method: 'DELETE' })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '删除失败');
      return;
    }
    showToast('记录已删除');
    loadNotesFromAPI();
  })
  .catch(function(err) {
    console.error('Failed to delete note:', err);
    showToast('删除失败');
  });
}

// Update note counts in TOC and chapters
function updateNoteStageCounts() {
  var stages = ['design', 'demolition', 'water', 'mud', 'wood', 'paint', 'install', 'soft'];
  var stageNamesDisplay = {
    'design': '设计阶段',
    'demolition': '拆改阶段',
    'water': '水电阶段',
    'mud': '泥工阶段',
    'wood': '木工阶段',
    'paint': '油漆阶段',
    'install': '安装阶段',
    'soft': '软装阶段'
  };
  stages.forEach(function(stage) {
    // Count notes for this stage directly from notesData (not DOM, which may be collapsed)
    var count = notesData.filter(function(note) { return note.stage === stage; }).length;
    var tocCount = document.getElementById('toc-count-' + stage);
    if (tocCount) tocCount.textContent = count;
    // Update chapter meta
    var chapterId = 'chapter-' + stage;
    var chapter = document.getElementById(chapterId);
    if (chapter) {
      var meta = chapter.querySelector('.manual-chapter-meta span');
      if (meta) meta.textContent = count + ' 条记录';
    }
  });
}

// Initialize notes page
function initNotesPage() {
  if (document.querySelector('.manual-layout')) {
    document.querySelectorAll('.manual-chapter.open .manual-chapter-toggle svg').forEach(function(svg) { svg.style.transform = 'rotate(0deg)'; });
    document.querySelectorAll('.manual-chapter:not(.open) .manual-chapter-toggle svg').forEach(function(svg) { svg.style.transform = 'rotate(-90deg)'; });
    loadLookupData(function() {
      fillCategorySelects();
      fillTaskSelects();
      fillCompareItemSelects();
      loadNotesFromAPI();
    });
  }
}

// Delete note (via API)
function deleteNote(noteId) {
  if (!confirm('确认删除这条装修手册记录吗？')) return;

  fetch(apiBase + '/api/notes/' + noteId, { method: 'DELETE' })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.status === 'error') {
      showToast(data.message || '删除失败');
      return;
    }
    // 从内存数据中移除
    notesData = notesData.filter(function(n) { return n.id !== noteId; });
    // 重新渲染
    renderAllNotes();
    updateNoteStageCounts();
    showToast('记录已删除');
  })
  .catch(function(err) {
    console.error('Failed to delete note:', err);
    showToast('删除失败');
  });
}

// Update note counts in TOC and chapters
function updateNoteStageCounts() {
  var stages = ['design', 'demolition', 'water', 'mud', 'wood', 'paint', 'install', 'soft'];
  var stageNamesDisplay = {
    'design': '设计阶段',
    'demolition': '拆改阶段',
    'water': '水电阶段',
    'mud': '泥工阶段',
    'wood': '木工阶段',
    'paint': '油漆阶段',
    'install': '安装阶段',
    'soft': '软装阶段'
  };
  stages.forEach(function(stage) {
    // Count notes for this stage directly from notesData (not DOM, which may be collapsed)
    var count = notesData.filter(function(note) { return note.stage === stage; }).length;
    var tocCount = document.getElementById('toc-count-' + stage);
    if (tocCount) tocCount.textContent = count;
    // Update chapter meta
    var chapterId = 'chapter-' + stage;
    var chapter = document.getElementById(chapterId);
    if (chapter) {
      var meta = chapter.querySelector('.manual-chapter-meta span');
      if (meta) meta.textContent = count + ' 条记录';
    }
  });
}

// Scroll to chapter
function scrollToChapter(chapterId) {
  var chapter = document.getElementById(chapterId);
  if (chapter) {
    chapter.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Select a TOC stage (highlight + expand chapter + scroll)
function selectTocStage(stage) {
  // Highlight active TOC button
  document.querySelectorAll('.manual-toc-btn').forEach(function(b) {
    b.classList.remove('active');
  });
  var btn = document.querySelector('.manual-toc-btn[onclick*="selectTocStage(\'' + stage + '\')"]');
  if (btn) btn.classList.add('active');

  // Open the chapter if not already open
  var chapterId = 'chapter-' + stage;
  var chapter = document.getElementById(chapterId);
  if (chapter && !chapter.classList.contains('open')) {
    var toggle = chapter.querySelector('.manual-chapter-toggle svg');
    chapter.classList.add('open');
    if (toggle) toggle.style.transform = 'rotate(0deg)';
  }

  // Scroll to chapter
  if (chapter) {
    chapter.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Go to progress page
function goToProgress() {
  window.location.href = '/decoration/progress';
}

// Go to compare page
function goToCompare() {
  window.location.href = '/decoration/compare';
}

// Toggle TOC section (collapse/expand the section)
function toggleTocSection(btn) {
  var section = btn.closest('.manual-toc-section');
  if (!section) return;
  section.classList.toggle('open');
  document.querySelectorAll('.manual-toc-btn').forEach(function(b) { b.classList.remove('active'); });
  if (section.classList.contains('open')) btn.classList.add('active');
}

// Toggle chapter (collapse/expand chapter body)
function toggleChapter(header) {
  var chapter = header.closest('.manual-chapter');
  if (!chapter) return;
  var toggle = chapter.querySelector('.manual-chapter-toggle svg');
  if (chapter.classList.contains('open')) {
    chapter.classList.remove('open');
    if (toggle) toggle.style.transform = 'rotate(-90deg)';
  } else {
    chapter.classList.add('open');
    if (toggle) toggle.style.transform = 'rotate(0deg)';
  }
}

// Initialize progress page: load tasks from API
function initProgressPage() {
  if (document.querySelector('.kanban-board')) {
    loadLookupData(function() {
      fillCategorySelects();
      loadTasksFromAPI();
    });
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
  // Load saved project state
  var savedProject = localStorage.getItem('renovamate-project');
  if (savedProject) {
    try {
      var parsed = JSON.parse(savedProject);
      Object.assign(projectState, parsed);
    } catch (e) {}
  }

  // Initialize sidebar state based on screen width
  function initSidebar() {
    if (window.innerWidth < 900) {
      // Mobile: always collapsed
      document.body.classList.add('sidebar-collapsed');
    } else {
      // PC/iPad: check localStorage
      var saved = localStorage.getItem('renovamate-sidebar-collapsed');
      if (saved === '1') {
        document.body.classList.add('sidebar-collapsed');
      } else {
        document.body.classList.remove('sidebar-collapsed');
      }
    }
  }

  initSidebar();

  // Handle resize
  window.addEventListener('resize', function() {
    if (window.innerWidth < 900) {
      document.body.classList.add('sidebar-collapsed');
    } else {
      // Don't auto-expand on resize up, keep user's choice
      var saved = localStorage.getItem('renovamate-sidebar-collapsed');
      if (saved === '1') {
        document.body.classList.add('sidebar-collapsed');
      } else {
        document.body.classList.remove('sidebar-collapsed');
      }
    }
  });

  // Initialize budget display + load real budget data on all pages
  updateBudgetDisplay();
  loadTopbarBudgetFromAPI();

  // Bind data-open-modal buttons
  document.querySelectorAll('[data-open-modal]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var modalId = this.dataset.openModal;
      openModal(modalId);
      // Populate dropdowns before showing modals that need lookup data
      if (modalId === 'taskModal' || modalId === 'editTaskModal') {
        if (!window.renovaLookupData || !window.renovaLookupData.categories || window.renovaLookupData.categories.length === 0) {
          loadLookupData(function() { fillCategorySelects(); });
        } else {
          fillCategorySelects();
        }
      }
      if (modalId === 'noteEntryModal' || modalId === 'editNoteModal') {
        if (!window.renovaLookupData || !window.renovaLookupData.categories || window.renovaLookupData.categories.length === 0) {
          loadLookupData(function() { fillCategorySelects(); fillTaskSelects(); fillCompareItemSelects(); });
        } else {
          fillCategorySelects();
          fillTaskSelects();
          fillCompareItemSelects();
        }
      }
      if (modalId === 'expenseModal') {
        if (!window.renovaLookupData || !window.renovaLookupData.categories || window.renovaLookupData.categories.length === 0) {
          loadLookupData(function() { fillCategorySelects(); fillCompareItemSelects(); });
        } else {
          fillCategorySelects();
          fillCompareItemSelects();
        }
      }
    });
  });

  // Close modal on overlay click
  document.querySelectorAll('.modal-overlay').forEach(function(overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Close modal on ESC key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(function(modal) {
        modal.classList.remove('active');
      });
      document.body.style.overflow = '';
    }
  });

  // Toggle filter chips
  document.querySelectorAll('.filter-chip').forEach(function(chip) {
    chip.addEventListener('click', function() {
      var parent = this.closest('.filter-bar') || this.closest('.sub-category-pills');
      if (parent) {
        parent.querySelectorAll('.filter-chip, .sub-cat-pill').forEach(function(c) {
          c.classList.remove('active');
        });
      }
      this.classList.add('active');
    });
  });

  // Toggle sub-category pills
  document.querySelectorAll('.sub-cat-pill').forEach(function(pill) {
    pill.addEventListener('click', function() {
      var parent = this.closest('.sub-category-pills');
      if (parent) {
        parent.querySelectorAll('.sub-cat-pill').forEach(function(p) {
          p.classList.remove('active');
        });
      }
      this.classList.add('active');
    });
  });

  // Toggle view tabs
  document.querySelectorAll('.view-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      var parent = this.closest('.view-tabs');
      if (parent) {
        parent.querySelectorAll('.view-tab').forEach(function(t) {
          t.classList.remove('active');
        });
      }
      this.classList.add('active');
    });
  });

  // Category card click - navigate with anchor
  document.querySelectorAll('.category-card[data-category]').forEach(function(card) {
    card.addEventListener('click', function() {
      var category = this.dataset.category;
      navigateToCategory(category);
    });
  });

  // Todo item toggle with confirmation
  document.querySelectorAll('.todo-item').forEach(function(item) {
    bindTodoItemEvents(item);
  });

  // Initialize todo count
  updateTodoCount();

  // Close modals on page load (in case they were open)
  document.querySelectorAll('.modal-overlay').forEach(function(modal) {
    modal.classList.remove('active');
  });

  // Mobile sidebar overlay click
  var sidebarOverlay = document.getElementById('sidebarOverlay');
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', toggleMobileSidebar);
  }

  // Settings button in topbar - just open modal (form pre-populated by Flask/Jinja2)
  var settingsBtn = document.querySelector('.topbar-actions .btn-icon');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', function() {
      openModal('settingsModal');
    });
  }

  // Topbar menu button (for sidebar collapse on PC/iPad)
  var topbarMenuBtn = document.querySelector('.topbar-menu-btn');
  if (topbarMenuBtn) {
    topbarMenuBtn.addEventListener('click', toggleSidebar);
  }

  // Bind click-to-edit on all kanban cards
  bindKanbanCardEvents();

  // Initialize compare page if present
  checkAndInitComparePage();

  // Initialize AC detail page if present
  initAcDetailPage();

  // Initialize home page if present
  initHomePage();

  // Initialize budget page if present
  initBudgetPage();

  // Initialize notes page if present
  initNotesPage();

  // Initialize progress page if present
  if (document.querySelector('.kanban-board')) {
    initProgressPage();
  }
});
