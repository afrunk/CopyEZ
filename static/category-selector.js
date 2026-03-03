/**
 * 可搜索下拉选择组件（二级分类）
 */
class CategorySelector {
  constructor(inputId, options = {}) {
    this.input = document.getElementById(inputId);
    if (!this.input) return;
    
    this.options = {
      placeholder: options.placeholder || "选择或输入二级分类",
      apiUrl: options.apiUrl || "/api/categories",
      mainCategoryInputId: options.mainCategoryInputId || "mainCategory",
      ...options
    };
    
    this.categories = [];
    this.filteredCategories = [];
    this.isOpen = false;
    this.selectedIndex = -1;
    
    this.init();
  }
  
  init() {
    // 创建下拉容器
    this.container = document.createElement("div");
    this.container.className = "category-selector-container";
    this.input.parentNode.insertBefore(this.container, this.input.nextSibling);
    
    // 创建下拉列表
    this.dropdown = document.createElement("div");
    this.dropdown.className = "category-selector-dropdown";
    this.dropdown.style.display = "none";
    this.container.appendChild(this.dropdown);
    
    // 绑定事件
    this.input.addEventListener("input", (e) => this.handleInput(e));
    this.input.addEventListener("focus", () => this.handleFocus());
    this.input.addEventListener("blur", () => {
      // 延迟关闭，允许点击选项
      setTimeout(() => this.handleBlur(), 200);
    });
    this.input.addEventListener("keydown", (e) => this.handleKeydown(e));
    
    // 监听一级分类变化
    const mainCategoryInput = document.getElementById(this.options.mainCategoryInputId);
    if (mainCategoryInput) {
      mainCategoryInput.addEventListener("change", () => this.loadCategories());
    }
    
    // 初始加载分类
    this.loadCategories();
  }
  
  async loadCategories() {
    const mainCategory = document.getElementById(this.options.mainCategoryInputId)?.value || "";
    const url = `${this.options.apiUrl}?mainCategory=${encodeURIComponent(mainCategory)}&_t=${Date.now()}`;
    
    try {
      // 强制禁用缓存，确保每次获取最新数据
      const response = await fetch(url, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      const data = await response.json();
      this.categories = data.categories || [];
      this.filter();
    } catch (error) {
      console.error("加载分类失败:", error);
      this.categories = [];
    }
  }
  
  filter() {
    const query = this.input.value.trim().toLowerCase();
    
    if (!query) {
      this.filteredCategories = this.categories;
    } else {
      this.filteredCategories = this.categories.filter(cat => 
        cat.toLowerCase().includes(query)
      );
    }
    
    this.render();
  }
  
  render() {
    const query = this.input.value.trim();
    const hasMatch = this.filteredCategories.some(cat => cat === query);
    
    this.dropdown.innerHTML = "";
    
    // 显示匹配的分类
    this.filteredCategories.forEach((category, index) => {
      const item = document.createElement("div");
      item.className = "category-selector-item";
      if (index === this.selectedIndex) {
        item.classList.add("selected");
      }
      item.textContent = category;
      item.addEventListener("click", () => this.selectCategory(category));
      this.dropdown.appendChild(item);
    });
    
    // 如果没有匹配项且用户输入了新内容，显示"新增"选项
    if (query && !hasMatch && this.filteredCategories.length === 0) {
      const addItem = document.createElement("div");
      addItem.className = "category-selector-item category-selector-add";
      addItem.innerHTML = `<span class="add-icon">+</span> 新增：${query}`;
      addItem.addEventListener("click", () => this.selectCategory(query));
      this.dropdown.appendChild(addItem);
    }
    
    // 显示/隐藏下拉框
    if (this.isOpen && (this.filteredCategories.length > 0 || query)) {
      this.dropdown.style.display = "block";
    } else {
      this.dropdown.style.display = "none";
    }
  }
  
  selectCategory(category) {
    this.input.value = category;
    this.isOpen = false;
    this.dropdown.style.display = "none";
    this.selectedIndex = -1;
    
    // 触发 change 事件
    this.input.dispatchEvent(new Event("change", { bubbles: true }));
  }
  
  handleInput(e) {
    this.filter();
    this.isOpen = true;
    this.selectedIndex = -1;
  }
  
  handleFocus() {
    this.isOpen = true;
    this.filter();
  }
  
  handleBlur() {
    this.isOpen = false;
    this.dropdown.style.display = "none";
    this.selectedIndex = -1;
  }
  
  handleKeydown(e) {
    if (!this.isOpen) {
      if (e.key === "ArrowDown" || e.key === "Enter") {
        e.preventDefault();
        this.isOpen = true;
        this.filter();
        return;
      }
    }
    
    if (e.key === "ArrowDown") {
      e.preventDefault();
      this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredCategories.length - 1);
      this.render();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
      this.render();
    } else if (e.key === "Enter" && this.selectedIndex >= 0) {
      e.preventDefault();
      this.selectCategory(this.filteredCategories[this.selectedIndex]);
    } else if (e.key === "Escape") {
      this.isOpen = false;
      this.dropdown.style.display = "none";
      this.selectedIndex = -1;
    }
  }
}

/**
 * 多选标签组件（三级标签）
 */
class TagSelector {
  constructor(containerId, hiddenInputId, options = {}) {
    this.container = document.getElementById(containerId);
    this.hiddenInput = document.getElementById(hiddenInputId);
    if (!this.container || !this.hiddenInput) return;
    
    this.options = {
      placeholder: options.placeholder || "选择或输入标签",
      apiUrl: options.apiUrl || "/api/tags",
      ...options
    };
    
    this.tags = [];
    this.selectedTags = [];
    this.isOpen = false;
    
    this.init();
  }
  
  init() {
    // 解析已选标签
    try {
      const value = this.hiddenInput.value;
      if (value) {
        this.selectedTags = JSON.parse(value);
      }
    } catch (e) {
      // 兼容旧格式：逗号分隔
      const value = this.hiddenInput.value;
      if (value) {
        this.selectedTags = value.split(",").map(t => t.trim()).filter(t => t);
      }
    }
    
    // 创建标签容器
    this.tagsContainer = document.createElement("div");
    this.tagsContainer.className = "tag-selector-tags";
    this.container.appendChild(this.tagsContainer);
    
    // 创建输入框容器
    this.inputContainer = document.createElement("div");
    this.inputContainer.className = "tag-selector-input-container";
    this.container.appendChild(this.inputContainer);
    
    // 创建输入框
    this.input = document.createElement("input");
    this.input.type = "text";
    this.input.className = "tag-selector-input";
    this.input.placeholder = this.options.placeholder;
    this.inputContainer.appendChild(this.input);
    
    // 创建下拉列表
    this.dropdown = document.createElement("div");
    this.dropdown.className = "tag-selector-dropdown";
    this.dropdown.style.display = "none";
    this.inputContainer.appendChild(this.dropdown);
    
    // 绑定事件
    this.input.addEventListener("input", () => this.handleInput());
    this.input.addEventListener("focus", () => this.handleFocus());
    this.input.addEventListener("blur", () => {
      setTimeout(() => this.handleBlur(), 200);
    });
    this.input.addEventListener("keydown", (e) => this.handleKeydown(e));
    
    // 加载预置标签
    this.loadTags();
    
    // 渲染已选标签
    this.renderTags();
  }
  
  async loadTags() {
    try {
      // 强制禁用缓存，确保每次获取最新数据
      // 添加时间戳参数防止浏览器缓存
      const url = `${this.options.apiUrl}?_t=${Date.now()}`;
      const response = await fetch(url, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      const data = await response.json();
      this.tags = data.tags || [];
      this.filter();
    } catch (error) {
      console.error("加载标签失败:", error);
      this.tags = [];
    }
  }
  
  filter() {
    const query = this.input.value.trim().toLowerCase();
    const availableTags = this.tags.filter(tag => 
      !this.selectedTags.includes(tag) && 
      (!query || tag.toLowerCase().includes(query))
    );
    
    this.renderDropdown(availableTags, query);
  }
  
  renderDropdown(availableTags, query) {
    this.dropdown.innerHTML = "";
    
    if (availableTags.length > 0) {
      availableTags.forEach(tag => {
        const item = document.createElement("div");
        item.className = "tag-selector-item";
        item.textContent = tag;
        item.addEventListener("click", () => this.addTag(tag));
        this.dropdown.appendChild(item);
      });
    }
    
    // 如果输入了新标签且不在列表中，显示"新增"选项
    if (query && !this.tags.includes(query) && !this.selectedTags.includes(query)) {
      const addItem = document.createElement("div");
      addItem.className = "tag-selector-item tag-selector-add";
      addItem.innerHTML = `<span class="add-icon">+</span> 新增：${query}`;
      addItem.addEventListener("click", () => this.addTag(query));
      this.dropdown.appendChild(addItem);
    }
    
    // 显示/隐藏下拉框
    if (this.isOpen && (availableTags.length > 0 || query)) {
      this.dropdown.style.display = "block";
    } else {
      this.dropdown.style.display = "none";
    }
  }
  
  renderTags() {
    this.tagsContainer.innerHTML = "";
    
    this.selectedTags.forEach(tag => {
      const tagEl = document.createElement("span");
      tagEl.className = "tag-selector-tag";
      tagEl.innerHTML = `
        <span class="tag-text">${tag}</span>
        <span class="tag-remove" data-tag="${tag}">×</span>
      `;
      
      const removeBtn = tagEl.querySelector(".tag-remove");
      removeBtn.addEventListener("click", () => this.removeTag(tag));
      
      this.tagsContainer.appendChild(tagEl);
    });
    
    // 更新隐藏输入框
    this.hiddenInput.value = JSON.stringify(this.selectedTags);
  }
  
  addTag(tag) {
    if (tag && !this.selectedTags.includes(tag)) {
      this.selectedTags.push(tag);
      this.renderTags();
      this.input.value = "";
      this.filter();
    }
  }
  
  removeTag(tag) {
    this.selectedTags = this.selectedTags.filter(t => t !== tag);
    this.renderTags();
    this.filter();
  }
  
  handleInput() {
    this.filter();
    this.isOpen = true;
  }
  
  handleFocus() {
    this.isOpen = true;
    this.filter();
  }
  
  handleBlur() {
    this.isOpen = false;
    this.dropdown.style.display = "none";
  }
  
  handleKeydown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const value = this.input.value.trim();
      if (value) {
        this.addTag(value);
      }
    } else if (e.key === "Escape") {
      this.isOpen = false;
      this.dropdown.style.display = "none";
    }
  }
}

// 导出
if (typeof module !== "undefined" && module.exports) {
  module.exports = { CategorySelector, TagSelector };
}