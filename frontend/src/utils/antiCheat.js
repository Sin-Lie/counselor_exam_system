/**
 * 防作弊引擎
 * 集中管理考试过程中的环境控制和行为监控
 * 替代 AbortMonitor.vue + AntiCheatDetector 的分散模式
 */

/**
 * 防作弊引擎类
 * 提供切屏检测、强制全屏、DevTools检测、窗口缩放检测、快捷键拦截等功能
 */
export class AntiCheatEngine {
  /**
   * @param {Object} options
   * @param {number} options.maxLeaveCount - 最大切屏次数，默认3
   * @param {Object} options.examStore - Pinia exam store 实例
   * @param {Function} options.onLeave - 切屏回调(info)
   * @param {Function} options.onForceSubmit - 强制交卷回调(info)
   * @param {Function} options.onDevtoolsOpen - 检测到DevTools回调()
   * @param {Function} options.onWindowResize - 窗口异常缩放回调(info)
   * @param {Function} options.onReFocus - 切屏后重新获得焦点回调()
   */
  constructor(options = {}) {
    this.options = {
      maxLeaveCount: options.maxLeaveCount || 3, // 最大切屏次数
      examStore: options.examStore || null, // Pinia exam store 实例
      paperId: options.paperId || null, // 当前试卷ID（用于异常上报）
      onLeave: options.onLeave || null, // 切屏回调
      onForceSubmit: options.onForceSubmit || null, // 强制交卷回调
      onDevtoolsOpen: options.onDevtoolsOpen || null, // 检测到DevTools回调
      onWindowResize: options.onWindowResize || null, // 窗口异常缩放回调
      onReFocus: options.onReFocus || null, // 切屏后重新获得焦点回调
      onFullscreenExit: options.onFullscreenExit || null, // 用户尝试退出全屏回调
    }

    // 状态
    this.leaveCount = 0 // 切屏计数
    this.isMonitoring = false // 是否正在监控
    this.isFirstLeave = true // 是否首次离开
    this.focusedAfterBlur = false // 失焦后是否已重新获得焦点
    this.initialWindowWidth = 0 // 初始窗口宽度
    this.lastLeaveTime = 0 // 上次离开时间戳
    this.devtoolsTimer = null // DevTools检测定时器
    this.resizeTimer = null // 窗口缩放检测定时器
    this._fullscreenReentryTimer = null // 全屏重入延迟定时器

    // 绑定 this 引用
    this.handleVisibilityChange = this.handleVisibilityChange.bind(this) // 页面可见性变化处理
    this.handleWindowBlur = this.handleWindowBlur.bind(this) // 窗口失焦处理
    this.handleWindowFocus = this.handleWindowFocus.bind(this) // 窗口聚焦处理
    this.handleKeyDown = this.handleKeyDown.bind(this) // 键盘按下处理（常规阶段）
    this.handleKeyDownCapture = this.handleKeyDownCapture.bind(this) // 键盘按下处理（捕获阶段，在浏览器之前拦截）
    this.handleKeyUp = this.handleKeyUp.bind(this) // 键盘弹起处理
    this.handleContextMenu = this.handleContextMenu.bind(this) // 右键菜单拦截
    this.handleCopy = this.handleCopy.bind(this) // 复制拦截
    this.handlePaste = this.handlePaste.bind(this) // 粘贴拦截
    this.handleCut = this.handleCut.bind(this) // 剪切拦截
    this.handleDragStart = this.handleDragStart.bind(this) // 拖拽拦截
    this.handleBeforeUnload = this.handleBeforeUnload.bind(this) // 页面关闭/刷新拦截
    this.handleFullScreenChange = this.handleFullScreenChange.bind(this) // 全屏状态变化处理
    this.handleResize = this.handleResize.bind(this) // 窗口尺寸变化处理
    this.handleWheel = this.handleWheel.bind(this) // 滚轮拦截
    this.detectDevTools = this.detectDevTools.bind(this) // 开发者工具检测
  }

  /**
   * 启动所有监控
   */
  start() {
    if (this.isMonitoring) return
    this.isMonitoring = true

    // 记录初始窗口宽度
    this.initialWindowWidth = window.innerWidth

    // 强制进入全屏
    this.requestFullscreen()

    // 添加事件监听
    document.addEventListener('visibilitychange', this.handleVisibilityChange) // 页面可见性变化
    window.addEventListener('blur', this.handleWindowBlur) // 窗口失焦
    window.addEventListener('focus', this.handleWindowFocus) // 窗口聚焦
    // 捕获阶段监听键盘（在浏览器处理之前拦截，用于阻止ESC退出全屏等系统级快捷键）
    document.addEventListener('keydown', this.handleKeyDownCapture, true) // 第三个参数 true 表示捕获阶段
    document.addEventListener('keydown', this.handleKeyDown) // 常规阶段补充拦截
    document.addEventListener('keyup', this.handleKeyUp) // 键盘弹起拦截
    document.addEventListener('contextmenu', this.handleContextMenu) // 右键菜单
    document.addEventListener('copy', this.handleCopy) // 复制
    document.addEventListener('paste', this.handlePaste) // 粘贴
    document.addEventListener('cut', this.handleCut) // 剪切
    document.addEventListener('dragstart', this.handleDragStart) // 拖拽
    window.addEventListener('beforeunload', this.handleBeforeUnload) // 页面关闭/刷新
    document.addEventListener('fullscreenchange', this.handleFullScreenChange) // 全屏变化
    window.addEventListener('resize', this.handleResize) // 窗口尺寸变化
    document.addEventListener('wheel', this.handleWheel, { passive: false }) // 滚轮（非被动模式以支持preventDefault）

    // 启动 DevTools 检测（立即执行一次，之后每3秒）
    this.detectDevTools()
    this.devtoolsTimer = setInterval(this.detectDevTools, 3000)
  }

  /**
   * 停止所有监控，清理监听器
   */
  stop() {
    if (!this.isMonitoring) return
    this.isMonitoring = false

    document.removeEventListener('visibilitychange', this.handleVisibilityChange) // 页面可见性变化
    window.removeEventListener('blur', this.handleWindowBlur) // 窗口失焦
    window.removeEventListener('focus', this.handleWindowFocus) // 窗口聚焦
    document.removeEventListener('keydown', this.handleKeyDownCapture, true) // 捕获阶段键盘
    document.removeEventListener('keydown', this.handleKeyDown) // 常规阶段键盘
    document.removeEventListener('keyup', this.handleKeyUp) // 键盘弹起
    document.removeEventListener('contextmenu', this.handleContextMenu) // 右键菜单
    document.removeEventListener('copy', this.handleCopy) // 复制
    document.removeEventListener('paste', this.handlePaste) // 粘贴
    document.removeEventListener('cut', this.handleCut) // 剪切
    document.removeEventListener('dragstart', this.handleDragStart) // 拖拽
    window.removeEventListener('beforeunload', this.handleBeforeUnload) // 页面关闭/刷新
    document.removeEventListener('fullscreenchange', this.handleFullScreenChange) // 全屏变化
    window.removeEventListener('resize', this.handleResize) // 窗口尺寸变化
    document.removeEventListener('wheel', this.handleWheel) // 滚轮

    if (this.devtoolsTimer) {
      clearInterval(this.devtoolsTimer)
      this.devtoolsTimer = null
    }
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer)
      this.resizeTimer = null
    }
    if (this._fullscreenReentryTimer) {
      clearTimeout(this._fullscreenReentryTimer) // 清除全屏重入定时器
      this._fullscreenReentryTimer = null
    }
  }

  /**
   * 重置切屏计数等状态
   */
  reset() {
    this.leaveCount = 0
    this.isFirstLeave = true
    this.focusedAfterBlur = false
    this.lastLeaveTime = 0
  }

  // ============ 全屏控制 ============

  requestFullscreen() {
    const el = document.documentElement // 获取文档根元素作为全屏目标
    if (el.requestFullscreen) {
      el.requestFullscreen().catch(() => {}) // 标准全屏API
    } else if (el.webkitRequestFullScreen) {
      el.webkitRequestFullScreen() // WebKit内核全屏API
    } else if (el.msRequestFullscreen) {
      el.msRequestFullscreen() // IE全屏API
    }
  }

  /**
   * 退出全屏模式（公开方法，供考试结束时调用）
   */
  exitFullscreen() {
    if (document.exitFullscreen) {
      document.exitFullscreen().catch(() => {}) // 标准退出全屏API
    } else if (document.webkitCancelFullScreen) {
      document.webkitCancelFullScreen() // WebKit内核退出全屏API
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen() // IE退出全屏API
    }
  }

  // ============ 切屏检测 ============

  handleVisibilityChange() {
    if (!this.isMonitoring) return
    if (document.hidden) {
      this.recordLeave('visibility')
    }
  }

  handleWindowBlur() {
    if (!this.isMonitoring) return
    this.focusedAfterBlur = false
    this.recordLeave('blur')
  }

  handleWindowFocus() {
    if (!this.isMonitoring) return
    if (!this.focusedAfterBlur) {
      this.focusedAfterBlur = true
      if (this.options.onReFocus) {
        this.options.onReFocus()
      }
    }
  }

  /**
   * 记录离开事件（防重复计数：同一时间窗口内 blur 和 visibility 只计一次）
   */
  recordLeave(type) {
    if (!this.isMonitoring) return

    const now = Date.now()
    if (now - this.lastLeaveTime < 500) return
    this.lastLeaveTime = now

    this.leaveCount++

    const info = {
      count: this.leaveCount,
      maxCount: this.options.maxLeaveCount,
      type: type,
      remaining: Math.max(0, this.options.maxLeaveCount - this.leaveCount),
    }

    if (this.isFirstLeave) {
      this.isFirstLeave = false
      this.leaveCount--
      if (this.options.onLeave) {
        this.options.onLeave({ ...info, count: this.leaveCount, isFirst: true })
      }
      return
    }

    if (this.options.onLeave) {
      this.options.onLeave(info)
    }

    if (this.leaveCount >= this.options.maxLeaveCount) {
      this.handleForceSubmit()
    }
  }

  handleForceSubmit() {
    if (this.options.onForceSubmit) {
      this.options.onForceSubmit({ leaveCount: this.leaveCount })
    }
    this.stop()
  }

  /**
   * 通过 store 上报异常
   */
  reportToStore(type, detail) {
    // 检查 paperId 有效性，避免传 null 到后端
    const paperId = this.options.paperId // 获取试卷ID
    if (!paperId) {
      console.warn(`[防作弊] 异常上报跳过（paperId为空）：type=${type}, detail=${detail}`)
      return
    }
    if (this.options.examStore && this.options.examStore.reportException) {
      this.options.examStore.reportException(type, detail) // 调用store上报
    }
  }

  // ============ DevTools 检测 ============

  detectDevTools() {
    if (!this.isMonitoring) return
    const start = performance.now()
    debugger
    const end = performance.now()
    if (end - start > 100) {
      if (this.options.onDevtoolsOpen) {
        this.options.onDevtoolsOpen()
      }
    }
  }

  // ============ 窗口缩放检测 ============

  handleResize() {
    if (!this.isMonitoring) return
    if (this.resizeTimer) clearTimeout(this.resizeTimer)
    this.resizeTimer = setTimeout(() => {
      const currentWidth = window.innerWidth
      if (this.initialWindowWidth > 0 && currentWidth < this.initialWindowWidth * 0.6) {
        if (this.options.onWindowResize) {
          this.options.onWindowResize({
            initialWidth: this.initialWindowWidth,
            currentWidth: currentWidth,
            ratio: currentWidth / this.initialWindowWidth,
          })
        }
      }
    }, 500)
  }

  // ============ 全屏变化 ============

  handleFullScreenChange() {
    if (!this.isMonitoring) return // 未监控时放行
    const isFs = !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.msFullscreenElement
    )
    if (!isFs) {
      // 调用用户尝试退出全屏的回调
      if (this.options.onFullscreenExit) {
        this.options.onFullscreenExit()
      }
      // 上报异常（需检查 paperId 有效性，避免传 null 到后端）
      const paperId = this.options.paperId // 获取试卷ID
      if (paperId) {
        this.reportToStore('fullscreen_exit', '用户按下ESC键退出全屏模式')
      } else {
        console.warn('[防作弊] 全屏退出，但 paperId 为空，跳过异常上报')
      }
      // 延迟重新进入全屏（等浏览器完成退出全屏的状态切换后再请求进入）
      // 使用 requestAnimationFrame 确保在下一帧执行，避免浏览器状态冲突
      if (this._fullscreenReentryTimer) {
        clearTimeout(this._fullscreenReentryTimer) // 清除之前的定时器，防止重复
      }
      this._fullscreenReentryTimer = setTimeout(() => {
        this._fullscreenReentryTimer = null
        if (this.isMonitoring) {
          this.requestFullscreen() // 重新进入全屏
        }
      }, 150) // 延迟150ms，确保浏览器退出全屏后再进入
    }
  }

  // ============ 键盘快捷键拦截（捕获阶段，在浏览器处理之前拦截） ============

  /**
   * 捕获阶段键盘监听
   * 在浏览器处理键盘事件之前拦截，用于阻止ESC退出全屏等系统级行为
   * @param {KeyboardEvent} event - 键盘事件对象
   */
  handleKeyDownCapture(event) {
    if (!this.isMonitoring) return // 未监控时放行

    // ESC键：浏览器全屏退出由浏览器内核处理，JS无法100%阻止
    // 通过捕获阶段尽最大努力拦截，同时依赖 fullscreenchange 事件兜底
    if (event.key === 'Escape' || event.keyCode === 27) {
      event.preventDefault() // 阻止默认行为
      event.stopPropagation() // 阻止事件冒泡
      event.stopImmediatePropagation() // 阻止同一元素上的其他监听器
      return
    }

    // F11全屏切换键
    if (event.key === 'F11' || event.keyCode === 122) {
      event.preventDefault() // 阻止默认行为
      event.stopPropagation() // 阻止冒泡
      event.stopImmediatePropagation() // 阻止其他监听器
      return
    }
  }

  // ============ 键盘快捷键拦截（常规阶段） ============

  /**
   * 键盘按下处理
   * 拦截所有考试期间不允许使用的快捷键
   * @param {KeyboardEvent} event - 键盘事件对象
   */
  handleKeyDown(event) {
    if (!this.isMonitoring) return // 未监控时放行

    // --- ESC键：退出全屏（浏览器级行为无法完全阻止，此处做二次拦截） ---
    if (event.key === 'Escape' || event.keyCode === 27) {
      event.preventDefault() // 阻止默认行为
      event.stopPropagation() // 阻止事件冒泡
      event.stopImmediatePropagation() // 阻止同一元素上的其他监听器
      return
    }

    // --- Alt键组合快捷键 ---
    if (event.altKey) {
      // Alt+Tab（切换窗口，OS级别无法完全阻止）
      if (event.key === 'Tab' || event.keyCode === 9) {
        event.preventDefault() // 阻止默认行为
      }
      // Alt+F4（关闭窗口）
      if (event.key === 'F4' || event.keyCode === 115) {
        event.preventDefault() // 阻止默认行为
      }
      // Alt+左方向键（浏览器后退）
      if (event.key === 'ArrowLeft' || event.keyCode === 37) {
        event.preventDefault() // 阻止默认行为
      }
      // Alt+右方向键（浏览器前进）
      if (event.key === 'ArrowRight' || event.keyCode === 39) {
        event.preventDefault() // 阻止默认行为
      }
      // Alt+Home（打开主页）
      if (event.key === 'Home' || event.keyCode === 36) {
        event.preventDefault() // 阻止默认行为
      }
      // 其他Alt组合键一律阻止
      event.preventDefault() // 阻止所有Alt组合键
      return
    }

    // --- Windows/Meta键（Win键/Command键） ---
    if (event.key === 'Meta' || event.key === 'OS' || event.keyCode === 91 || event.keyCode === 92) {
      event.preventDefault() // 阻止Win键
      return
    }

    // --- F功能键 ---
    // F1（帮助）
    if (event.key === 'F1' || event.keyCode === 112) {
      event.preventDefault() // 阻止F1帮助
      return
    }
    // F2~F10
    if (['F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10'].includes(event.key)) {
      event.preventDefault() // 阻止F2-F10功能键
      return
    }
    // F11（全屏切换）
    if (event.key === 'F11' || event.keyCode === 122) {
      event.preventDefault() // 阻止F11全屏切换
      return
    }
    // F12（开发者工具）
    if (event.key === 'F12' || event.keyCode === 123) {
      event.preventDefault() // 阻止F12开发者工具
      return
    }

    // --- PrintScreen截图键 ---
    if (event.key === 'PrintScreen' || event.keyCode === 44) {
      event.preventDefault() // 阻止截图键
      return
    }

    // --- Ctrl键组合快捷键 ---
    if (event.ctrlKey) {
      // 阻止所有Ctrl+字母组合快捷键
      const blockedCtrlKeys = [
        'a', 'A', // 全选
        'c', 'C', // 复制
        'v', 'V', // 粘贴
        'x', 'X', // 剪切
        's', 'S', // 保存
        'p', 'P', // 打印
        'f', 'F', // 查找
        'h', 'H', // 历史记录/替换
        'u', 'U', // 查看源代码
        'd', 'D', // 添加书签
        'n', 'N', // 新建窗口
        't', 'T', // 新建标签页
        'w', 'W', // 关闭标签页
        'r', 'R', // 刷新
        'j', 'J', // 下载
        'o', 'O', // 打开文件
        'g', 'G', // 查找下一个
        'l', 'L', // 地址栏
        'e', 'E', // 搜索
        'm', 'M', // 静音标签页
        'q', 'Q', // 退出
      ]
      if (blockedCtrlKeys.includes(event.key)) {
        event.preventDefault() // 阻止Ctrl+字母组合
        return
      }

      // Ctrl+Shift组合键
      if (event.shiftKey) {
        const blockedCtrlShiftKeys = [
          'i', 'I', // 开发者工具
          'j', 'J', // 开发者工具（部分浏览器）
          'c', 'C', // 开发者工具（部分浏览器）
          'n', 'N', // 隐私窗口
          't', 'T', // 恢复关闭标签页
          'p', 'P', // 隐私窗口（部分浏览器）
          'Delete', // 清除浏览数据
        ]
        if (blockedCtrlShiftKeys.includes(event.key)) {
          event.preventDefault() // 阻止Ctrl+Shift组合
          return
        }
      }

      // Ctrl+数字键（切换标签页1-9）
      if (['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].includes(event.key)) {
        event.preventDefault() // 阻止Ctrl+数字切换标签页
        return
      }

      // Ctrl+Tab（切换标签页）
      if (event.key === 'Tab' || event.keyCode === 9) {
        event.preventDefault() // 阻止Ctrl+Tab切换标签页
        return
      }

      // Ctrl+加减号（缩放页面）
      if (event.key === '+' || event.key === '-' || event.key === '=' || event.key === '_') {
        event.preventDefault() // 阻止Ctrl+加减号缩放页面
        return
      }

      // Ctrl+0（重置缩放）
      if (event.key === '0') {
        event.preventDefault() // 阻止Ctrl+0重置缩放
        return
      }

      // 阻止所有其他Ctrl组合键
      event.preventDefault() // 阻止其余所有Ctrl组合键
      return
    }

    // --- Shift组合键 ---
    if (event.shiftKey) {
      // Shift+F10（右键菜单）
      if (event.key === 'F10' || event.keyCode === 121) {
        event.preventDefault() // 阻止Shift+F10右键菜单
        return
      }
    }
  }

  /**
   * 键盘弹起拦截
   * 补充拦截部分在keyup阶段触发的快捷键行为
   * @param {KeyboardEvent} event - 键盘事件对象
   */
  handleKeyUp(event) {
    if (!this.isMonitoring) return // 未监控时放行

    // ESC键弹起
    if (event.key === 'Escape' || event.keyCode === 27) {
      event.preventDefault() // 阻止默认行为
      event.stopPropagation() // 阻止冒泡
      return
    }

    // F功能键弹起
    if (event.key && event.key.startsWith('F') && event.key.length >= 2) {
      const fnNum = parseInt(event.key.substring(1)) // 提取F键编号
      if (fnNum >= 1 && fnNum <= 12) {
        event.preventDefault() // 阻止所有F功能键弹起
        return
      }
    }
  }

  // ============ 滚轮/滑动拦截 ============

  /**
   * 拦截鼠标滚轮事件，防止考试期间通过滚轮进行页面滚动或缩放等操作
   */
  handleWheel(event) {
    if (!this.isMonitoring) return

    // 仅拦截 Ctrl+滚轮缩放，放行正常的页面滚动
    if (event.ctrlKey) {
      event.preventDefault()
    }
  }

  // ============ 右键/复制/粘贴/剪切/拖拽拦截 ============

  /**
   * 拦截右键菜单
   * @param {Event} event - 右键事件
   */
  handleContextMenu(event) {
    if (this.isMonitoring) {
      event.preventDefault() // 阻止右键菜单
    }
  }

  /**
   * 拦截复制操作
   * @param {Event} event - 复制事件
   */
  handleCopy(event) {
    if (this.isMonitoring) {
      event.preventDefault() // 阻止复制
    }
  }

  /**
   * 拦截粘贴操作
   * @param {Event} event - 粘贴事件
   */
  handlePaste(event) {
    if (this.isMonitoring) {
      event.preventDefault() // 阻止粘贴
    }
  }

  /**
   * 拦截剪切操作
   * @param {Event} event - 剪切事件
   */
  handleCut(event) {
    if (this.isMonitoring) {
      event.preventDefault() // 阻止剪切
    }
  }

  /**
   * 拦截拖拽操作
   * @param {Event} event - 拖拽事件
   */
  handleDragStart(event) {
    if (this.isMonitoring) {
      event.preventDefault() // 阻止拖拽
    }
  }

  // ============ 页面关闭/刷新阻止 ============

  /**
   * 阻止页面关闭或刷新
   * 考试期间防止学生通过关闭页面或刷新来中断考试
   * @param {Event} event - beforeunload事件
   */
  handleBeforeUnload(event) {
    if (this.isMonitoring) {
      event.preventDefault() // 阻止默认关闭行为
      event.returnValue = '' // Chrome需要设置returnValue来触发确认弹窗
    }
  }
}

/**
 * 全屏控制工具
 * 保留以兼容现有引用
 */
export const fullscreenUtils = {
  isSupported() {
    return !!(
      document.fullscreenEnabled ||
      document.webkitRequestFullScreen ||
      document.mozRequestFullScreen ||
      document.msRequestFullscreen
    )
  },

  isFullScreen() {
    return !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.mozFullScreenElement ||
      document.msFullscreenElement
    )
  },

  request(element = document.documentElement) {
    return new Promise((resolve, reject) => {
      if (element.requestFullscreen) {
        element.requestFullscreen().then(resolve).catch(reject)
      } else if (element.webkitRequestFullScreen) {
        element.webkitRequestFullScreen().then(resolve).catch(reject)
      } else if (element.mozRequestFullScreen) {
        element.mozRequestFullScreen().then(resolve).catch(reject)
      } else if (element.msRequestFullscreen) {
        element.msRequestFullscreen().then(resolve).catch(reject)
      } else {
        reject(new Error('当前浏览器不支持全屏'))
      }
    })
  },

  exit() {
    return new Promise((resolve, reject) => {
      if (document.exitFullscreen) {
        document.exitFullscreen().then(resolve).catch(reject)
      } else if (document.webkitCancelFullScreen) {
        document.webkitCancelFullScreen().then(resolve).catch(reject)
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen().then(resolve).catch(reject)
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen().then(resolve).catch(reject)
      } else {
        reject(new Error('当前浏览器不支持退出全屏'))
      }
    })
  },

  async toggle(element = document.documentElement) {
    if (this.isFullScreen()) {
      await this.exit()
    } else {
      await this.request(element)
    }
  },
}

/**
 * 剪切板工具
 * 保留以兼容现有引用
 */
export const clipboardUtils = {
  async copyText(text) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (error) {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      try {
        document.execCommand('copy')
        document.body.removeChild(textarea)
        return true
      } catch (e) {
        document.body.removeChild(textarea)
        return false
      }
    }
  },

  async readText() {
    try {
      return await navigator.clipboard.readText()
    } catch (error) {
      return ''
    }
  },
}
