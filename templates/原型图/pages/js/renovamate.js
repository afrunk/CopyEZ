// ============================================================
// RenovaMate - Shared JavaScript
// ============================================================

// Project state (simulated database)
var projectState = {
  totalBudget: 200000,
  actualSpent: 89500,
  estimatedCost: 158000,
  projectName: '新房装修',
  area: '120',
  style: '现代简约',
  currentStage: '水电阶段'
};

// Format number with thousand separators
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Parse formatted number
function parseFormattedNumber(str) {
  return parseInt(str.replace(/,/g, '')) || 0;
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

// Update budget display
function updateBudgetDisplay() {
  // Topbar chips
  var topbarTotal = document.querySelector('.topbar-budget-chip .value');
  var topbarRemaining = document.querySelector('.topbar-budget-chip:last-child .value');

  if (topbarTotal) {
    topbarTotal.textContent = formatNumber(projectState.totalBudget) + ' 元';
  }

  // Calculate remaining
  var remaining = projectState.totalBudget - projectState.actualSpent;
  if (remaining < 0) {
    remaining = 0;
  }

  if (topbarRemaining) {
    topbarRemaining.textContent = formatNumber(remaining) + ' 元';
    topbarRemaining.className = 'value ' + (remaining > 0 ? 'saved' : 'over');
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

// Save project settings
function saveProjectSettings() {
  var projectName = document.getElementById('settingsProjectName');
  var area = document.getElementById('settingsArea');
  var style = document.getElementById('settingsStyle');
  var totalBudget = document.getElementById('settingsTotalBudget');
  var currentStage = document.getElementById('settingsCurrentStage');

  if (projectName) projectState.projectName = projectName.value.trim();
  if (area) projectState.area = area.value.trim();
  if (style) projectState.style = style.value;
  if (totalBudget) projectState.totalBudget = parseInt(totalBudget.value) || 0;
  if (currentStage) projectState.currentStage = currentStage.value;

  // Save to localStorage
  localStorage.setItem('renovamate-project', JSON.stringify(projectState));

  // Update display
  updateBudgetDisplay();

  // Update sidebar project card
  var sidebarName = document.querySelector('.sidebar-project-name');
  var sidebarMeta = document.querySelector('.sidebar-project-meta');
  if (sidebarName) sidebarName.textContent = projectState.projectName;
  if (sidebarMeta) sidebarMeta.textContent = projectState.area + '㎡ · ' + projectState.style + ' · ' + projectState.currentStage;

  closeModal('settingsModal');
  showToast('项目设置已保存');
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
    window.location.href = '5-notes.html?title=' + noteTitle + '&category=' + noteCategory;

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
    window.location.href = '2-compare.html#' + anchor;
  } else {
    window.location.href = '2-compare.html';
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
  window.location.href = '4-progress.html';
}

// Go to notes page
function goToNotes() {
  window.location.href = '5-notes.html';
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
    if (tags) {
      var tagList = tags.split(/[，,]/).filter(function(t) { return t.trim(); });
      tagsHtml = '<div class="manual-entry-tags">' + 
        tagList.map(function(t) { 
          return '<span class="note-tag">' + t.trim() + '</span>'; 
        }).join('') + 
        '</div>';
    }
    
    var sourceHtml = source ? '<div style="font-size:.75rem;color:var(--text-muted);margin-top:6px;">来源: ' + source + '</div>' : '';
    
    entry.innerHTML = 
      '<div class="manual-entry-header">' +
        '<span class="manual-entry-date">' + today + '</span>' +
      '</div>' +
      '<div class="manual-entry-title">' + title + '</div>' +
      '<div class="manual-entry-content">' + (content || '暂无内容') + '</div>' +
      sourceHtml +
      tagsHtml;
    
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

// Save progress task (装修进度)
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
  owner = owner ? owner.value.trim() : '未填写';
  note = note ? note.value.trim() : '';

  if (!title) {
    showToast('请填写任务名称');
    return;
  }

  var taskId = generateTaskId();
  var stageName = stageNameMap[stage] || stage;
  var config = statusConfig[status] || statusConfig['pending'];

  // Find target container by data-stage + data-status
  var targetContainer = document.querySelector('[data-stage="' + stage + '"][data-status="' + status + '"]');

  if (targetContainer) {
    var card = document.createElement('div');
    card.className = 'kanban-card';
    card.dataset.taskId = taskId;
    card.dataset.title = title;
    card.dataset.stage = stage;
    card.dataset.status = status;
    card.dataset.budget = budget;
    card.dataset.actual = actual;
    card.dataset.owner = owner;
    card.dataset.note = note;

    card.innerHTML =
      '<div class="kanban-card-title">' + title + '</div>' +
      '<div class="kanban-card-meta">' +
        '<span class="kanban-chip">' + stageName + '</span>' +
        (budget ? '<span class="kanban-chip">¥' + formatNumber(parseInt(budget) || 0) + '</span>' : '') +
      '</div>' +
      '<div class="kanban-card-status-label" style="font-size:.6875rem;color:' + config.color + ';margin-bottom:6px;">' + config.label + '</div>' +
      (status === 'ongoing' ? '<div style="margin-bottom:8px;"><div class="progress-bar-track" style="height:3px;"><div class="progress-bar-fill" style="width:50%;"></div></div></div>' : '') +
      '<div class="kanban-card-footer">' +
        '<span>' + owner + (status === 'ongoing' ? ' · 50%' : '') + '</span>' +
        '<span class="kanban-card-link" onclick="goToNotes()">📖 手册</span>' +
      '</div>';

    // Bind click-to-edit
    card.addEventListener('click', function(e) {
      if (e.target.closest('button') || e.target.closest('a')) return;
      openEditTaskModal(card);
    });

    // Stop propagation on buttons/links
    card.querySelectorAll('button, a').forEach(function(el) {
      el.addEventListener('click', function(e) { e.stopPropagation(); });
    });

    targetContainer.insertBefore(card, targetContainer.firstChild);

    // Update counts
    updateKanbanColumnCounts();
    updateKanbanGroupCounts();
  } else {
    showToast('未找到对应的任务列');
    return;
  }

  closeModal('taskModal');
  showToast('已添加装修任务');

  // Reset form
  var inputs = document.querySelectorAll('#taskModal input, #taskModal textarea, #taskModal select');
  inputs.forEach(function(input) {
    if (input.tagName === 'SELECT') {
      input.selectedIndex = 0;
    } else {
      input.value = '';
    }
  });
}

// ═══════════════════════════════════════════
// 分类比较页面 (2-compare.html)
// ═══════════════════════════════════════════

// ── Category Group Data ──
var categoryGroups = [
  { id: 'g-equipment', name: '设备系统', icon: '🏠', desc: '中央空调、新风、地暖等设备类', order: 1, enabled: true },
  { id: 'g-appliance', name: '家电家具', icon: '❄️', desc: '冰箱、洗衣机等大型家电', order: 2, enabled: true },
  { id: 'g-material', name: '主材选择', icon: '🧱', desc: '瓷砖、地板、门窗等主材', order: 3, enabled: true },
  { id: 'g-project', name: '施工项目', icon: '🔧', desc: '水电、木工等施工项目', order: 4, enabled: true },
  { id: 'g-soft', name: '软装搭配', icon: '🛋️', desc: '灯具、窗帘等软装', order: 5, enabled: true }
];

// ── Sub-category Data ──
var subCategories = [
  { id: 'c-ac', name: '中央空调', group: 'g-equipment', status: 'selected', budget: 28000, plans: 2, viewMode: 'card', note: '大金 VRV-P 一拖五' },
  { id: 'c-vent', name: '新风系统', group: 'g-equipment', status: 'comparing', budget: 8000, plans: 1, viewMode: 'card', note: '霍尼韦尔 / 松下待选' },
  { id: 'c-floorheat', name: '地暖', group: 'g-equipment', status: 'not-started', budget: 15000, plans: 0, viewMode: 'card', note: '' },
  { id: 'c-waterheater', name: '热水器', group: 'g-equipment', status: 'comparing', budget: 4000, plans: 1, viewMode: 'card', note: '燃气 vs 电热待选' },
  { id: 'c-smart', name: '智能家居', group: 'g-equipment', status: 'comparing', budget: 12000, plans: 1, viewMode: 'card', note: '米家 / 绿米方案' },
  { id: 'c-doorwin', name: '门窗', group: 'g-material', status: 'comparing', budget: 25000, plans: 3, viewMode: 'table', note: '3 家报价待对比' },
  { id: 'c-tiles', name: '瓷砖', group: 'g-material', status: 'selected', budget: 18000, plans: 1, viewMode: 'card', note: '马可波罗方案' },
  { id: 'c-floor', name: '地板', group: 'g-material', status: 'not-started', budget: 15000, plans: 0, viewMode: 'card', note: '' },
  { id: 'c-plumb', name: '水电', group: 'g-project', status: 'ongoing', budget: 20000, plans: 1, viewMode: 'card', note: '预计还需 5 天' },
  { id: 'c-wood', name: '木工', group: 'g-project', status: 'not-started', budget: 18000, plans: 0, viewMode: 'card', note: '' },
  { id: 'c-fridge', name: '冰箱', group: 'g-appliance', status: 'not-started', budget: 9000, plans: 0, viewMode: 'card', note: '' },
  { id: 'c-washer', name: '洗衣机', group: 'g-appliance', status: 'not-started', budget: 7000, plans: 0, viewMode: 'card', note: '' },
  { id: 'c-light', name: '灯具', group: 'g-soft', status: 'not-started', budget: 8000, plans: 0, viewMode: 'list', note: '' },
  { id: 'c-curtain', name: '窗帘', group: 'g-soft', status: 'not-started', budget: 5000, plans: 0, viewMode: 'list', note: '' }
];

// ── State ──
var currentGroupFilter = 'all';  // 'all' or group id
var currentView = 'card';         // 'card' or 'table'

// ── Group Helpers ──
function getGroupById(id) {
  return categoryGroups.find(function(g) { return g.id === id; });
}
function getGroupName(id) {
  var g = getGroupById(id);
  return g ? g.name : id;
}
function getSubcatCountByGroup(groupId) {
  return subCategories.filter(function(c) { return c.group === groupId; }).length;
}

// ── Status Helpers ──
var subcatStatusConfig = {
  'not-started': { label: '未开始', cssClass: 'status-not-started', shortLabel: '未开始' },
  'comparing':    { label: '比价中',   cssClass: 'status-comparing',    shortLabel: '比价中' },
  'selected':     { label: '已选方案', cssClass: 'status-selected',     shortLabel: '已选' },
  'ongoing':      { label: '进行中',   cssClass: 'status-ongoing',      shortLabel: '进行中' },
  'pending':      { label: '待确认',   cssClass: 'status-pending',      shortLabel: '待确认' }
};
function getStatusLabel(status) {
  var s = subcatStatusConfig[status] || subcatStatusConfig['not-started'];
  return s.label;
}

// ── Render: Category Groups ──
function renderCategoryGroups() {
  var grid = document.getElementById('categoryGroupGrid');
  if (!grid) return;

  grid.innerHTML = '';
  categoryGroups.forEach(function(g) {
    if (!g.enabled) return;
    var count = getSubcatCountByGroup(g.id);
    var isActive = currentGroupFilter === g.id;
    var card = document.createElement('div');
    card.className = 'category-group-card animate-in' + (isActive ? ' active' : '');
    card.dataset.groupId = g.id;
    card.innerHTML =
      '<div class="category-group-icon" style="background:rgba(234,88,12,.1);color:var(--accent-orange);font-size:1.25rem;">' + g.icon + '</div>' +
      '<div class="category-group-name">' + g.name + '</div>' +
      '<div class="category-group-count">' + count + ' 个子分类</div>';
    card.addEventListener('click', function() {
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
    if (!g.enabled) return;
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
  return subCategories.filter(function(c) { return c.group === currentGroupFilter; });
}

// ── Render: Sub-category Cards ──
function renderSubcatCards(items) {
  var grid = document.getElementById('subcatCardGrid');
  if (!grid) return;
  grid.innerHTML = '';

  items.forEach(function(c) {
    var statusCfg = subcatStatusConfig[c.status] || subcatStatusConfig['not-started'];
    var group = getGroupById(c.group);
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
        '<div class="category-desc">' + (c.note || '待开始') + '</div>' +
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
  if (!tbody) return;
  tbody.innerHTML = '';

  items.forEach(function(c) {
    var statusCfg = subcatStatusConfig[c.status] || subcatStatusConfig['not-started'];
    var budgetStr = c.budget ? '¥' + formatNumber(c.budget) : '—';

    var row = document.createElement('tr');
    row.innerHTML =
      '<td><strong>' + c.name + '</strong></td>' +
      '<td><span class="kanban-chip">' + getGroupName(c.group) + '</span></td>' +
      '<td><span class="status-tag ' + statusCfg.cssClass + '">' + statusCfg.label + '</span></td>' +
      '<td style="font-weight:600;">' + budgetStr + '</td>' +
      '<td style="text-align:center;">' + c.plans + '</td>' +
      '<td>' + (c.viewMode === 'card' ? '卡片' : c.viewMode === 'table' ? '表格' : '清单') + '</td>' +
      '<td style="text-align:center;">' +
        '<button class="btn btn-sm btn-ghost" onclick="navigateToCategoryDetail(\'' + c.id + '\',\'' + c.name + '\')">进入</button>' +
        '<button class="btn btn-sm btn-secondary" style="margin-left:4px;" onclick="openSubcatModal(\'' + c.id + '\')">编辑</button>' +
        '<button class="btn btn-sm btn-ghost" style="margin-left:4px;color:var(--accent-red);" onclick="deleteSubcat(\'' + c.id + '\')">删除</button>' +
      '</td>';

    // Add row click handler for central air conditioner
    if (c.id === 'c-ac') {
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
  if (catId === 'c-ac') {
    window.location.href = '2-air-conditioner.html';
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
    var g = getGroupById(id);
    if (g) {
      if (title) title.textContent = '编辑大类';
      if (nameInput) nameInput.value = g.name;
      if (iconInput) iconInput.value = g.icon;
      if (descInput) descInput.value = g.desc || '';
      if (orderInput) orderInput.value = g.order;
      if (enabledSelect) enabledSelect.value = g.enabled ? '1' : '0';
      // Highlight selected icon
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

  if (idInput && idInput.value) {
    // Edit
    var g = getGroupById(idInput.value);
    if (g) {
      g.name = name;
      g.icon = icon;
      g.desc = desc;
      g.order = order;
      g.enabled = enabled;
      showToast('大类已更新');
    }
  } else {
    // Add
    var newId = 'g-' + Date.now();
    categoryGroups.push({
      id: newId,
      name: name,
      icon: icon,
      desc: desc,
      order: order,
      enabled: enabled
    });
    showToast('大类「' + name + '」已添加');
  }

  closeModal('groupModal');
  renderCategoryGroups();
  renderFilterPills();
  fillGroupSelect();
}

function deleteGroup(groupId) {
  var g = getGroupById(groupId);
  if (!g) return;
  if (!confirm('确定要删除大类「' + g.name + '」吗？删除后该大类下的子分类将移至"全部"。')) return;

  // Remove group
  categoryGroups = categoryGroups.filter(function(x) { return x.id !== groupId; });
  // Clear filter if currently viewing this group
  if (currentGroupFilter === groupId) {
    setGroupFilter('all');
  }
  renderCategoryGroups();
  renderFilterPills();
  showToast('大类已删除');
}

// ── Sub-category Modal ──
function fillGroupSelect() {
  var sel = document.getElementById('subcatModalGroup');
  if (!sel) return;
  sel.innerHTML = '';
  categoryGroups.forEach(function(g) {
    if (!g.enabled) return;
    var opt = document.createElement('option');
    opt.value = g.id;
    opt.textContent = g.name;
    sel.appendChild(opt);
  });
}

function openSubcatModal(id) {
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
    var c = subCategories.find(function(x) { return x.id === id; });
    if (c) {
      if (title) title.textContent = '编辑子分类';
      if (nameInput) nameInput.value = c.name;
      if (groupSelect) groupSelect.value = c.group;
      if (statusSelect) statusSelect.value = c.status;
      if (budgetInput) budgetInput.value = c.budget || '';
      if (viewSelect) viewSelect.value = c.viewMode || 'card';
      if (noteInput) noteInput.value = c.note || '';
    }
  } else {
    if (title) title.textContent = '新增子分类';
    if (nameInput) nameInput.value = '';
    if (groupSelect) {
      if (currentGroupFilter !== 'all') {
        groupSelect.value = currentGroupFilter;
      } else {
        groupSelect.selectedIndex = 0;
      }
    }
    if (statusSelect) statusSelect.value = 'not-started';
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

  var group = groupSelect ? groupSelect.value : '';
  var status = statusSelect ? statusSelect.value : 'not-started';
  var budget = parseInt((budgetInput ? budgetInput.value : '0')) || 0;
  var viewMode = viewSelect ? viewSelect.value : 'card';
  var note = noteInput ? noteInput.value.trim() : '';

  if (idInput && idInput.value) {
    // Edit
    var c = subCategories.find(function(x) { return x.id === idInput.value; });
    if (c) {
      c.name = name;
      c.group = group;
      c.status = status;
      c.budget = budget;
      c.viewMode = viewMode;
      c.note = note;
      showToast('分类已更新');
    }
  } else {
    // Add
    var newId = 'c-' + Date.now();
    subCategories.push({
      id: newId,
      name: name,
      group: group,
      status: status,
      budget: budget,
      plans: 0,
      viewMode: viewMode,
      note: note
    });
    showToast('分类「' + name + '」已添加');
  }

  closeModal('subcatModal');
  var filtered = getFilteredSubcats();
  renderSubcatCards(filtered);
  renderSubcatTable(filtered);
  renderCategoryGroups();
  renderFilterPills();
}

function deleteSubcat(catId) {
  var c = subCategories.find(function(x) { return x.id === catId; });
  if (!c) return;
  if (!confirm('确定要删除分类「' + c.name + '」吗？此操作不可恢复。')) return;

  subCategories = subCategories.filter(function(x) { return x.id !== catId; });
  var filtered = getFilteredSubcats();
  renderSubcatCards(filtered);
  renderSubcatTable(filtered);
  renderCategoryGroups();
  renderFilterPills();
  showToast('分类「' + c.name + '」已删除');
}

// ── Settings (stub) ──
function openCompareSettings() {
  showToast('项目设置后续接入');
}

// ── Initialize Compare Page ──
function initComparePage() {
  renderCategoryGroups();
  renderFilterPills();
  setGroupFilter('all');
  setView('card');
  fillGroupSelect();

  // Group header buttons
  var btnAddGroup = document.getElementById('btnAddGroup');
  if (btnAddGroup) {
    btnAddGroup.addEventListener('click', function() { openGroupModal(null); });
  }
  var btnManageGroup = document.getElementById('btnManageGroup');
  if (btnManageGroup) {
    btnManageGroup.addEventListener('click', function() { showToast('管理大类：点击大卡片可直接编辑'); openGroupModal(null); });
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
// 中央空调详情页 (2-air-conditioner.html)
// ═══════════════════════════════════════════

// AC Plan data
var acPlans = [
  {
    id: 'plan-1',
    brand: '大金',
    model: 'VRV-P',
    power: '6匹',
    units: '一拖五',
    price: 28000,
    outdoor: 1,
    indoor: 5,
    efficiency: '一级',
    warranty: '3年',
    rating: 4.5,
    note: '价格略高，但品牌稳定，安装服务较成熟',
    selected: true,
    productImg: null,
    quoteImg: null
  },
  {
    id: 'plan-2',
    brand: '约克',
    model: 'YES-smart',
    power: '6匹',
    units: '一拖五',
    price: 24500,
    outdoor: 1,
    indoor: 5,
    efficiency: '一级',
    warranty: '3年',
    rating: 4.0,
    note: '性价比较高，需要确认安装辅材费用',
    selected: false,
    productImg: null,
    quoteImg: null
  },
  {
    id: 'plan-3',
    brand: '三菱',
    model: 'Power Multi',
    power: '6匹',
    units: '一拖五',
    price: 31000,
    outdoor: 1,
    indoor: 5,
    efficiency: '一级',
    warranty: '3年',
    rating: 4.6,
    note: '品牌强，但价格偏高',
    selected: false,
    productImg: null,
    quoteImg: null
  }
];

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
  if (countEl) {
    var visibleCount = getFilteredPlans().length;
    var totalCount = acPlans.length;
    countEl.textContent = visibleCount + ' / ' + totalCount + ' 个方案';
  }
}

// Render table rows (Notion-style)
function renderAcPlanTable() {
  var tbody = document.getElementById('acPlanTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  var plans = getFilteredPlans();

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
  if (!container) return;
  container.innerHTML = '';

  var plans = getFilteredPlans();

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

// Select a plan as the final choice
function selectAirconPlan(planId) {
  var plan = acPlans.find(function(p) { return p.id === planId; });
  if (!plan) return;

  // Deselect all
  acPlans.forEach(function(p) {
    p.selected = false;
  });
  plan.selected = true;

  // Update overview card
  updateAirconOverview(plan);

  // Re-render
  renderAcPlanTable();
  renderAcPlanCards();

  showToast('已选择 ' + plan.brand + ' ' + plan.model + ' 作为最终方案');
}

// Update overview card with selected plan info
function updateAirconOverview(plan) {
  var planNameEl = document.querySelector('.ac-overview-value.plan-name');
  var costEl = document.querySelector('.ac-overview-value.cost');
  if (planNameEl) planNameEl.textContent = plan.brand + ' ' + plan.model;
  if (costEl) costEl.textContent = '¥' + formatNumber(plan.price);
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

// Edit plan (stub)
function editAirconPlan(planId) {
  showToast('编辑方案后续接入');
}

// Delete plan
function deleteAirconPlan(planId) {
  var plan = acPlans.find(function(p) { return p.id === planId; });
  if (!plan) return;

  if (!confirm('确定要删除「' + plan.brand + ' ' + plan.model + '」方案吗？')) return;

  acPlans = acPlans.filter(function(p) { return p.id !== planId; });

  // If deleted plan was selected, select first remaining plan
  if (plan.selected && acPlans.length > 0) {
    acPlans[0].selected = true;
    updateAirconOverview(acPlans[0]);
  }

  renderAcPlanTable();
  renderAcPlanCards();
  updatePlanCount();
  showToast('方案已删除');
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

// Save new plan
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
  if (!price) {
    showToast('请填写总价');
    return;
  }

  var newPlan = {
    id: 'plan-' + Date.now(),
    brand: brand,
    model: model,
    power: power || '—',
    units: units || '—',
    price: price,
    outdoor: outdoor,
    indoor: indoor,
    efficiency: efficiency || '—',
    warranty: warranty || '—',
    rating: rating,
    note: note || '暂无备注',
    selected: false,
    productImg: null,
    quoteImg: null
  };

  acPlans.push(newPlan);
  renderAcPlanTable();
  renderAcPlanCards();
  updateOverviewCard();
  closeModal('addPlanModal');
  showToast('已新增中央空调方案');
}

// Open param settings modal
function openParamSettingsModal() {
  openModal('paramSettingsModal');
}

// Go back to compare page
function goBackToCompare() {
  window.location.href = '2-compare.html';
}

// Initialize AC detail page
function initAcDetailPage() {
  if (document.getElementById('acPlanTableBody')) {
    renderAcPlanTable();
    updatePlanCount();
    // Initialize overview with current selected plan
    var selectedPlan = acPlans.find(function(p) { return p.selected; });
    if (selectedPlan) {
      updateAirconOverview(selectedPlan);
    }
  }
}

// ═══════════════════════════════════════════
// 预算控制页 (3-budget.html)
// ═══════════════════════════════════════════

// Budget data
var budgetCategories = [
  { id: 'ac', name: '中央空调', plan: '大金 VRV-P 一拖五', budget: 28000, spent: 30000, status: 'over', hasPlan: true },
  { id: 'fridge', name: '冰箱', plan: '卡萨帝 500L', budget: 9000, spent: 8500, status: 'saved', hasPlan: true },
  { id: 'washer', name: '洗衣机', plan: '小天鹅洗烘套装', budget: 7000, spent: 7000, status: 'equal', hasPlan: true },
  { id: 'windows', name: '门窗', plan: '断桥铝方案 A', budget: 26000, spent: 24000, status: 'saved', hasPlan: true },
  { id: 'tiles', name: '瓷砖', plan: '马可波罗方案', budget: 18000, spent: 19500, status: 'over', hasPlan: true },
  { id: 'door', name: '木门', plan: '梦天木门', budget: 8000, spent: 8000, status: 'saved', hasPlan: true },
  { id: 'floor', name: '地板', plan: null, budget: 15000, spent: 0, status: 'pending', hasPlan: false },
  { id: 'water', name: '水电', plan: '水电改造方案 A', budget: 20000, spent: 15600, status: 'saved', hasPlan: true },
  { id: 'wood', name: '木工', plan: null, budget: 18000, spent: 0, status: 'pending', hasPlan: false },
  { id: 'cabinet', name: '全屋定制', plan: '待确认', budget: 35000, spent: 0, status: 'pending', hasPlan: false }
];

// Expense records
var expenseRecords = [
  { id: 'e1', date: '2024-05-15', category: '中央空调', name: '大金定金（已选方案）', amount: 3000, method: '银行卡', payee: '大金专卖店', receipt: true, note: '已付定金30%' },
  { id: 'e2', date: '2024-05-10', category: '水电', name: '水电一期付款', amount: 8000, method: '微信', payee: '水电师傅', receipt: true, note: '' },
  { id: 'e3', date: '2024-05-12', category: '瓷砖', name: '瓷砖订金（马可波罗）', amount: 5000, method: '支付宝', payee: '马可波罗门店', receipt: true, note: '含送货' },
  { id: 'e4', date: '2024-04-28', category: '冰箱', name: '卡萨帝 500L 货款', amount: 8500, method: '银行卡', payee: '京东电器', receipt: true, note: '已收货' },
  { id: 'e5', date: '2024-04-25', category: '门窗', name: '断桥铝门窗一期款', amount: 12000, method: '转账', payee: '门窗厂', receipt: true, note: '制作中' },
  { id: 'e6', date: '2024-04-20', category: '洗衣机', name: '小天鹅洗烘套装', amount: 7000, method: '微信', payee: '京东电器', receipt: true, note: '已到货' },
  { id: 'e7', date: '2024-04-15', category: '木门', name: '梦天木门定金', amount: 2000, method: '支付宝', payee: '梦天木门', receipt: true, note: '待生产' },
  { id: 'e8', date: '2024-04-10', category: '瓷砖', name: '瓷砖量尺费', amount: 500, method: '微信', payee: '马可波罗门店', receipt: false, note: '已完成' },
  { id: 'e9', date: '2024-03-28', category: '水电', name: '水电材料采购', amount: 7600, method: '转账', payee: '建材市场', receipt: false, note: '已完成' }
];

var currentBudgetFilter = 'all';

// Format number
function formatBudgetNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Calculate totals
function calculateTotals() {
  var totalBudget = 200000;
  var totalEstimated = 0;
  var totalSpent = 0;
  var overCount = 0;
  var savedAmount = 0;

  budgetCategories.forEach(function(cat) {
    totalEstimated += cat.budget;
    totalSpent += cat.spent;
    if (cat.status === 'over') {
      overCount++;
      savedAmount -= (cat.spent - cat.budget);
    } else if (cat.status === 'saved' && cat.hasPlan) {
      savedAmount += (cat.budget - cat.spent);
    }
  });

  return {
    totalBudget: totalBudget,
    totalEstimated: totalEstimated,
    totalSpent: totalSpent,
    remaining: totalBudget - totalSpent,
    estimatedLeft: totalBudget - totalEstimated,
    usagePercent: (totalSpent / totalBudget * 100).toFixed(1),
    estimatedPercent: (totalEstimated / totalBudget * 100).toFixed(1),
    overCount: overCount,
    savedAmount: savedAmount
  };
}

// Update cockpit display
function updateCockpit() {
  var totals = calculateTotals();

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
    spentEl.className = 'cockpit-secondary-value ' + (totals.totalSpent > totals.totalBudget ? 'over' : 'saved');
  }
  if (remainingEl) {
    remainingEl.textContent = '¥' + formatBudgetNumber(totals.remaining);
    remainingEl.className = 'cockpit-secondary-value ' + (totals.remaining < 0 ? 'over' : 'saved');
  }
  if (estimatedLeftEl) {
    estimatedLeftEl.textContent = '¥' + formatBudgetNumber(totals.estimatedLeft);
    estimatedLeftEl.className = 'cockpit-secondary-value ' + (totals.estimatedLeft < 0 ? 'over' : '');
  }
  if (usagePercentEl) usagePercentEl.textContent = totals.usagePercent + '%';
  if (usageBarEl) usageBarEl.style.width = totals.usagePercent + '%';

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
  }
  if (statCards[3]) {
    statCards[3].querySelector('.budget-stat-value').textContent = '¥' + formatBudgetNumber(totals.savedAmount);
  }
}

// Render budget table
function renderBudgetTable() {
  var tbody = document.getElementById('budgetTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  var filtered = budgetCategories.filter(function(cat) {
    if (currentBudgetFilter === 'all') return true;
    if (currentBudgetFilter === 'over') return cat.status === 'over';
    if (currentBudgetFilter === 'saved') return cat.status === 'saved';
    if (currentBudgetFilter === 'equal') return cat.status === 'equal';
    if (currentBudgetFilter === 'pending') return !cat.hasPlan;
    return true;
  });

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
    row.className = cat.status === 'over' ? 'budget-row-over' : cat.status === 'saved' ? 'budget-row-saved' : !cat.hasPlan ? 'budget-row-pending' : '';
    row.innerHTML =
      '<td><strong>' + cat.name + '</strong></td>' +
      '<td style="color:' + (cat.plan ? 'var(--text-secondary)' : 'var(--text-muted)') + ';">' + (cat.plan || '待选方案') + '</td>' +
      '<td style="font-weight:600;">¥' + formatBudgetNumber(cat.budget) + '</td>' +
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
        '<button class="btn btn-ghost btn-sm" onclick="showToast(\'跳转至「' + cat.name + '」分类\')">查看</button>' +
        '<button class="btn btn-ghost btn-sm" style="margin-left:4px;" onclick="openExpenseModalForCategory(\'' + cat.name + '\')">记一笔</button>' +
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
  container.innerHTML = '';

  var groups = groupExpensesByMonth();
  var monthKeys = Object.keys(groups).sort().reverse();

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
      itemEl.onclick = function() {
        showToast(exp.date + ' ' + exp.name + ' ¥' + formatBudgetNumber(exp.amount) + ' ' + exp.payee);
      };

      var day = exp.date.substring(8, 10);
      var monthShort = exp.date.substring(5, 7) + '月';

      itemEl.innerHTML =
        '<div class="expense-flow-date">' +
          '<div class="expense-flow-day">' + day + '</div>' +
          '<div class="expense-flow-month">' + monthShort + '</div>' +
        '</div>' +
        '<div class="expense-flow-content">' +
          '<span class="expense-flow-category">' + exp.category + '</span>' +
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

// Render category analysis bars
function renderCategoryBars() {
  var container = document.getElementById('categoryBars');
  if (!container) return;
  container.innerHTML = '';

  var maxBudget = Math.max.apply(null, budgetCategories.map(function(c) { return c.budget; }));

  budgetCategories.forEach(function(cat) {
    var barEl = document.createElement('div');
    barEl.className = 'category-bar-item';

    var percent = (cat.budget / maxBudget * 100).toFixed(1);
    var barClass = cat.status === 'over' ? 'over' : cat.status === 'saved' ? 'saved' : !cat.hasPlan ? 'pending' : 'normal';
    var valueClass = cat.status === 'over' ? 'over' : cat.status === 'saved' ? 'saved' : '';

    barEl.innerHTML =
      '<span class="category-bar-label">' + cat.name + '</span>' +
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

  if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
  if (categorySelect) categorySelect.selectedIndex = 0;
  if (nameInput) nameInput.value = '';
  if (amountInput) amountInput.value = '';
  if (methodSelect) methodSelect.selectedIndex = 0;
  if (payeeInput) payeeInput.value = '';
  if (noteInput) noteInput.value = '';

  openModal('expenseModal');
}

// Open expense modal with pre-filled category
function openExpenseModalForCategory(categoryName) {
  openExpenseModal();
  var categorySelect = document.getElementById('expenseCategory');
  if (categorySelect) {
    for (var i = 0; i < categorySelect.options.length; i++) {
      if (categorySelect.options[i].value === categoryName) {
        categorySelect.selectedIndex = i;
        break;
      }
    }
  }
}

// Save expense
function saveExpense() {
  var dateInput = document.getElementById('expenseDate');
  var categorySelect = document.getElementById('expenseCategory');
  var nameInput = document.getElementById('expenseName');
  var amountInput = document.getElementById('expenseAmount');
  var methodSelect = document.getElementById('expenseMethod');
  var payeeInput = document.getElementById('expensePayee');
  var noteInput = document.getElementById('expenseNote');

  var date = dateInput ? dateInput.value : '';
  var category = categorySelect ? categorySelect.value : '';
  var name = nameInput ? nameInput.value.trim() : '';
  var amount = amountInput ? parseInt(amountInput.value) || 0 : 0;
  var method = methodSelect ? methodSelect.value : '';
  var payee = payeeInput ? payeeInput.value.trim() : '';
  var note = noteInput ? noteInput.value.trim() : '';

  if (!date) { showToast('请选择支出日期'); return; }
  if (!category) { showToast('请选择支出分类'); return; }
  if (!name) { showToast('请填写支出名称'); return; }
  if (!amount) { showToast('请填写金额'); return; }

  var newExpense = {
    id: 'e-' + Date.now(),
    date: date,
    category: category,
    name: name,
    amount: amount,
    method: method || '银行卡',
    payee: payee,
    receipt: false,
    note: note
  };

  expenseRecords.unshift(newExpense);

  // Update budget category spent if category matches
  budgetCategories.forEach(function(cat) {
    if (cat.name === category) {
      cat.spent += amount;
      if (cat.status !== 'pending') {
        cat.status = cat.spent > cat.budget ? 'over' : cat.spent === cat.budget ? 'equal' : 'saved';
      }
    }
  });

  closeModal('expenseModal');
  renderExpenseRecords();
  renderBudgetTable();
  renderCategoryBars();
  updateCockpit();
  showToast('已新增花费记录');
}

// Initialize budget page
function initBudgetPage() {
  if (document.getElementById('budgetTable')) {
    renderBudgetTable();
    renderExpenseRecords();
    renderCategoryBars();
    updateCockpit();
  }
}

// ═══════════════════════════════════════════
// 装修手册页 (5-notes.html)
// ═══════════════════════════════════════════

var currentNoteStage = 'design';

// Stage name mapping
var stageNames = {
  'design': '设计阶段',
  'demo': '拆改阶段',
  'electrical': '水电阶段',
  'tiles': '泥工阶段',
  'wood': '木工阶段',
  'paint': '油漆阶段',
  'install': '安装阶段',
  'soft': '软装阶段'
};

// Open new note modal for a specific stage
function openNoteModalForStage(stage) {
  currentNoteStage = stage;
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
  document.getElementById('noteTitle').value = '';
  document.getElementById('noteSource').value = '';
  document.getElementById('noteTags').value = '';
  document.getElementById('noteContent').value = '';
  document.getElementById('noteRelatedTask').selectedIndex = 0;
  document.getElementById('noteRelatedCategory').selectedIndex = 0;
  openModal('noteEntryModal');
}

// Save new note entry
function saveNoteEntry() {
  var title = document.getElementById('noteTitle').value.trim();
  var stage = document.getElementById('noteStage').value;
  var source = document.getElementById('noteSource').value.trim();
  var tags = document.getElementById('noteTags').value.trim();
  var content = document.getElementById('noteContent').value.trim();
  var relatedTask = document.getElementById('noteRelatedTask').value;
  var relatedCategory = document.getElementById('noteRelatedCategory').value;

  if (!title) { showToast('请填写记录标题'); return; }
  if (!content) { showToast('请填写记录内容'); return; }

  var noteId = 'note-' + Date.now();
  var today = new Date().toISOString().split('T')[0];

  // Create new entry HTML
  var entryHtml = '<div class="manual-entry" data-note-id="' + noteId + '" data-stage="' + stage + '" data-title="' + title + '" data-date="' + today + '" data-source="' + source + '" data-tags="' + tags + '" data-content="' + content + '" data-related-task="' + relatedTask + '" data-related-category="' + relatedCategory + '">' +
    '<div class="manual-entry-actions">' +
      '<button class="note-action-btn" onclick="openEditNoteModal(\'' + noteId + '\')" title="编辑"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/></svg></button>' +
      '<button class="note-action-btn danger" onclick="deleteNote(\'' + noteId + '\')" title="删除"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg></button>' +
    '</div>' +
    '<div class="manual-entry-header">' +
      '<span class="manual-entry-date">' + today + '</span>' +
      (relatedTask ? '<span class="entry-related-task" onclick="goToProgress()">关联任务：' + relatedTask + '</span>' : '') +
      (relatedCategory ? '<span class="entry-related-cat" onclick="goToCompare()">分类：' + relatedCategory + '</span>' : '') +
    '</div>' +
    '<div class="manual-entry-title">' + title + '</div>' +
    '<div class="manual-entry-content">' + content + '</div>' +
    (tags ? '<div class="manual-entry-tags">' + tags.split(/[,，]/).filter(function(t) { return t.trim(); }).map(function(t) { return '<span class="note-tag">' + t.trim() + '</span>'; }).join('') + '</div>' : '') +
  '</div>';

  // Find the chapter for this stage and add entry before the add button
  var chapters = document.querySelectorAll('.manual-chapter');
  chapters.forEach(function(chapter) {
    var entries = chapter.querySelectorAll('.manual-entry[data-stage]');
    if (entries.length > 0 && entries[0].dataset.stage === stage) {
      var addBtn = chapter.querySelector('.manual-add-btn');
      if (addBtn) {
        var tempDiv = document.createElement('div');
        tempDiv.innerHTML = entryHtml;
        chapter.insertBefore(tempDiv.firstElementChild, addBtn);
      }
    }
  });

  closeModal('noteEntryModal');
  updateNoteStageCounts();
  showToast('手册记录已新增');
}

// Open edit note modal
function openEditNoteModal(noteId) {
  var entry = document.querySelector('[data-note-id="' + noteId + '"]');
  if (!entry) return;

  document.getElementById('editNoteId').value = noteId;
  document.getElementById('editNoteTitle').value = entry.dataset.title || '';
  document.getElementById('editNoteSource').value = entry.dataset.source || '';
  document.getElementById('editNoteTags').value = entry.dataset.tags || '';
  document.getElementById('editNoteContent').value = entry.dataset.content || '';

  // Set stage
  var stageSelect = document.getElementById('editNoteStage');
  var stage = entry.dataset.stage || 'design';
  for (var i = 0; i < stageSelect.options.length; i++) {
    if (stageSelect.options[i].value === stage) {
      stageSelect.selectedIndex = i;
      break;
    }
  }

  // Set related task
  var taskSelect = document.getElementById('editNoteRelatedTask');
  var task = entry.dataset.relatedTask || '';
  for (var j = 0; j < taskSelect.options.length; j++) {
    if (taskSelect.options[j].value === task) {
      taskSelect.selectedIndex = j;
      break;
    }
  }

  // Set related category
  var catSelect = document.getElementById('editNoteRelatedCategory');
  var cat = entry.dataset.relatedCategory || '';
  for (var k = 0; k < catSelect.options.length; k++) {
    if (catSelect.options[k].value === cat) {
      catSelect.selectedIndex = k;
      break;
    }
  }

  openModal('editNoteModal');
}

// Save edited note
function saveEditedNote() {
  var noteId = document.getElementById('editNoteId').value;
  var entry = document.querySelector('[data-note-id="' + noteId + '"]');
  if (!entry) return;

  var title = document.getElementById('editNoteTitle').value.trim();
  var stage = document.getElementById('editNoteStage').value;
  var source = document.getElementById('editNoteSource').value.trim();
  var tags = document.getElementById('editNoteTags').value.trim();
  var content = document.getElementById('editNoteContent').value.trim();
  var relatedTask = document.getElementById('editNoteRelatedTask').value;
  var relatedCategory = document.getElementById('editNoteRelatedCategory').value;

  if (!title) { showToast('请填写记录标题'); return; }
  if (!content) { showToast('请填写记录内容'); return; }

  // Update data attributes
  entry.dataset.title = title;
  entry.dataset.stage = stage;
  entry.dataset.source = source;
  entry.dataset.tags = tags;
  entry.dataset.content = content;
  entry.dataset.relatedTask = relatedTask;
  entry.dataset.relatedCategory = relatedCategory;

  // Update visual elements
  entry.querySelector('.manual-entry-title').textContent = title;
  entry.querySelector('.manual-entry-content').textContent = content;

  // Update header
  var headerEl = entry.querySelector('.manual-entry-header');
  headerEl.innerHTML = '<span class="manual-entry-date">' + (entry.dataset.date || new Date().toISOString().split('T')[0]) + '</span>';
  if (relatedTask) {
    headerEl.innerHTML += '<span class="entry-related-task" onclick="goToProgress()">关联任务：' + relatedTask + '</span>';
  }
  if (relatedCategory) {
    headerEl.innerHTML += '<span class="entry-related-cat" onclick="goToCompare()">分类：' + relatedCategory + '</span>';
  }

  // Update tags
  var tagsEl = entry.querySelector('.manual-entry-tags');
  if (tags) {
    var tagList = tags.split(/[,，]/).filter(function(t) { return t.trim(); });
    if (tagsEl) {
      tagsEl.innerHTML = tagList.map(function(t) { return '<span class="note-tag">' + t.trim() + '</span>'; }).join('');
    } else {
      var tagsHtml = '<div class="manual-entry-tags">' + tagList.map(function(t) { return '<span class="note-tag">' + t.trim() + '</span>'; }).join('') + '</div>';
      entry.insertAdjacentHTML('beforeend', tagsHtml);
    }
  } else if (tagsEl) {
    tagsEl.remove();
  }

  closeModal('editNoteModal');
  showToast('手册记录已更新');
}

// Delete note
function deleteNote(noteId) {
  if (!confirm('确认删除这条装修手册记录吗？')) return;

  var entry = document.querySelector('[data-note-id="' + noteId + '"]');
  if (entry) {
    entry.remove();
    updateNoteStageCounts();
    showToast('记录已删除');
  }
}

// Update note counts in TOC and chapters
function updateNoteStageCounts() {
  var stages = ['design', 'demo', 'electrical', 'tiles', 'wood', 'paint', 'install', 'soft'];
  var stageNamesDisplay = {
    'design': '设计阶段',
    'demo': '拆改阶段',
    'electrical': '水电阶段',
    'tiles': '泥工阶段',
    'wood': '木工阶段',
    'paint': '油漆阶段',
    'install': '安装阶段',
    'soft': '软装阶段'
  };

  stages.forEach(function(stage) {
    var entries = document.querySelectorAll('.manual-entry[data-stage="' + stage + '"]');
    var count = entries.length;

    // Update TOC count
    var tocCount = document.getElementById('toc-count-' + stage);
    if (tocCount) tocCount.textContent = count;

    // Update sidebar badge
    if (stage === 'design') {
      var sidebarBadge = document.querySelector('.nav-item-badge.green');
      if (sidebarBadge) {
        var totalCount = document.querySelectorAll('.manual-entry[data-stage]').length;
        sidebarBadge.textContent = totalCount;
      }
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

// Go to progress page
function goToProgress() {
  showToast('已关联到装修进度任务');
}

// Go to compare page
function goToCompare() {
  showToast('已关联到分类比较');
}

// Toggle TOC section
function toggleTocSection(btn) {
  var section = btn.closest('.manual-toc-section');
  if (!section) return;

  // Toggle current
  section.classList.toggle('open');

  // Update active state
  document.querySelectorAll('.manual-toc-btn').forEach(function(b) {
    b.classList.remove('active');
  });
  if (section.classList.contains('open')) {
    btn.classList.add('active');
  }
}

// Toggle chapter
function toggleChapter(header) {
  var chapter = header.closest('.manual-chapter');
  if (!chapter) return;

  var body = chapter.querySelector('.manual-chapter-body');
  var toggle = chapter.querySelector('.manual-chapter-toggle svg');

  if (chapter.classList.contains('open')) {
    chapter.classList.remove('open');
    if (toggle) toggle.style.transform = 'rotate(-90deg)';
  } else {
    chapter.classList.add('open');
    if (toggle) toggle.style.transform = 'rotate(0deg)';
  }
}

// Initialize notes page
function initNotesPage() {
  if (document.querySelector('.manual-layout')) {
    // Set initial toggle rotations
    document.querySelectorAll('.manual-chapter.open .manual-chapter-toggle svg').forEach(function(svg) {
      svg.style.transform = 'rotate(0deg)';
    });
    document.querySelectorAll('.manual-chapter:not(.open) .manual-chapter-toggle svg').forEach(function(svg) {
      svg.style.transform = 'rotate(-90deg)';
    });

    // Update note counts
    updateNoteStageCounts();
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

  // Initialize budget display
  updateBudgetDisplay();

  // Bind data-open-modal buttons
  document.querySelectorAll('[data-open-modal]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      openModal(this.dataset.openModal);
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

  // Settings button in topbar
  var settingsBtn = document.querySelector('.topbar-actions .btn-icon');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', function() {
      // Populate settings form with current values
      var projectNameEl = document.getElementById('settingsProjectName');
      var areaEl = document.getElementById('settingsArea');
      var styleEl = document.getElementById('settingsStyle');
      var totalBudgetEl = document.getElementById('settingsTotalBudget');
      var currentStageEl = document.getElementById('settingsCurrentStage');
      var actualSpentEl = document.getElementById('settingsActualSpent');

      if (projectNameEl) projectNameEl.value = projectState.projectName;
      if (areaEl) areaEl.value = projectState.area;
      if (styleEl) styleEl.value = projectState.style;
      if (totalBudgetEl) totalBudgetEl.value = projectState.totalBudget;
      if (currentStageEl) currentStageEl.value = projectState.currentStage;
      if (actualSpentEl) actualSpentEl.textContent = formatNumber(projectState.actualSpent) + ' 元';

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

  // Initialize budget page if present
  initBudgetPage();

  // Initialize notes page if present
  initNotesPage();
});
