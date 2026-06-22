/**
 * 防切屏监控组件
 * 监控考生在考试过程中是否切换浏览器标签页或离开考试页面
 * 记录切屏次数，达到阈值后强制交卷并上报异常
 */
<template>
  <slot /> <!-- 默认插槽，用于包装考试内容 -->
</template>

<script setup>
/**
 * 防切屏监控组件逻辑
 * 监听页面可见性变化和窗口焦点变化，防止考生切屏作弊
 */
import { onMounted, onUnmounted, ref } from 'vue'; // 引入Vue生命周期和响应式API
import { useExamStore } from '@/stores/exam'; // 引入考试状态管理
import { ElMessage, ElMessageBox } from 'element-plus'; // 引入Element Plus消息和对话框

// ==================== 常量定义 ====================
const MAX_LEAVE_COUNT = 3; // 允许的最大切屏次数

// ==================== 状态定义 ====================
const examStore = useExamStore(); // 获取考试状态管理实例
const leaveCount = ref(0); // 切屏次数计数器
const isFirstLeave = ref(true); // 标记是否首次切屏

// ==================== 事件处理函数 ====================
/**
 * 处理页面可见性变化事件
 * 当用户切换浏览器标签页时触发
 * @param {VisibilityChangeEvent} event - 可见性变化事件对象
 */
function handleVisibilityChange(event) {
  // 只有在考试进行中才监控
  if (!examStore.isExamining) {
    return;
  }

  // 页面变为隐藏（用户切换到其他标签页或最小化了窗口）
  if (document.hidden) {
    handleLeave(); // 处理离开事件
  }
}

/**
 * 处理窗口失去焦点事件
 * 当用户点击窗口外部或切换到其他应用程序时触发
 * @param {FocusEvent} event - 焦点变化事件对象
 */
function handleWindowBlur(event) {
  // 只有在考试进行中才监控
  if (!examStore.isExamining) {
    return;
  }

  // 窗口失去焦点
  handleLeave(); // 处理离开事件
}

/**
 * 处理离开事件（切屏）
 * 记录切屏次数，达到阈值时强制交卷
 */
async function handleLeave() {
  leaveCount.value++; // 增加切屏次数

  // 首次切屏，只记录并警告
  if (isFirstLeave.value) {
    isFirstLeave.value = false; // 标记为非首次切屏
    ElMessage.warning('检测到您离开了考试页面，考试期间请勿切屏！'); // 显示警告消息
    examStore.reportException('leave', '用户首次离开考试页面'); // 上报异常
    return;
  }

  // 达到最大切屏次数，强制交卷
  if (leaveCount.value >= MAX_LEAVE_COUNT) {
    ElMessage.error('切屏次数过多，考试被强制终止！'); // 显示错误消息
    examStore.reportException('leave', `切屏次数达到${MAX_LEAVE_COUNT}次，强制交卷`); // 上报异常
    await examStore.handleAutoSubmit(); // 执行自动交卷
    return;
  }

  // 未达到阈值，警告并记录
  ElMessage.warning(`检测到您离开了考试页面！剩余 ${MAX_LEAVE_COUNT - leaveCount.value + 1} 次机会`); // 显示剩余机会警告
  examStore.reportException('leave', `用户离开考试页面，当前第${leaveCount.value}次`); // 上报异常
}

/**
 * 处理键盘事件
 * 监听可能用于作弊的快捷键
 * @param {KeyboardEvent} event - 键盘事件对象
 */
function handleKeyDown(event) {
  // 只有在考试进行中才监控
  if (!examStore.isExamining) {
    return;
  }

  // 监听Alt+Tab组合键（切换窗口）
  if (event.key === 'Tab' && event.altKey) {
    event.preventDefault(); // 阻止默认行为
    ElMessage.warning('考试期间禁止使用Alt+Tab切换窗口！'); // 显示警告
    return;
  }

  // 监听Windows键或Command键
  if (event.key === 'Meta' || event.key === 'OS') {
    event.preventDefault(); // 阻止默认行为
    ElMessage.warning('考试期间禁止使用系统快捷键！'); // 显示警告
    return;
  }

  // 监听F11（全屏切换）
  if (event.key === 'F11') {
    event.preventDefault(); // 阻止默认行为
    ElMessage.warning('请勿尝试退出全屏模式！'); // 显示警告
    return;
  }

  // 监听Ctrl键组合
  if (event.ctrlKey) {
    // Ctrl+W（关闭标签页）
    if (event.key === 'w' || event.key === 'W') {
      event.preventDefault(); // 阻止默认行为
      ElMessage.warning('考试期间禁止关闭页面！'); // 显示警告
      return;
    }
    // Ctrl+T（新建标签页）
    if (event.key === 't' || event.key === 'T') {
      event.preventDefault(); // 阻止默认行为
      ElMessage.warning('考试期间禁止打开新标签页！'); // 显示警告
      return;
    }
    // Ctrl+N（新建窗口）
    if (event.key === 'n' || event.key === 'N') {
      event.preventDefault(); // 阻止默认行为
      ElMessage.warning('考试期间禁止打开新窗口！'); // 显示警告
      return;
    }
    // Ctrl+R（刷新页面）
    if (event.key === 'r' || event.key === 'R') {
      event.preventDefault(); // 阻止默认行为
      ElMessage.warning('考试期间禁止刷新页面！'); // 显示警告
      return;
    }
  }
}

/**
 * 处理右键菜单事件
 * 禁止右键菜单，防止考生查看源代码或复制
 * @param {MouseEvent} event - 鼠标事件对象
 */
function handleContextMenu(event) {
  // 只有在考试进行中才拦截
  if (!examStore.isExamining) {
    return;
  }
  event.preventDefault(); // 阻止默认右键菜单
  ElMessage.warning('考试期间禁止使用右键菜单！'); // 显示警告
}

/**
 * 处理复制事件
 * 禁止复制考试内容
 * @param {ClipboardEvent} event - 剪贴板事件对象
 */
function handleCopy(event) {
  // 只有在考试进行中才拦截
  if (!examStore.isExamining) {
    return;
  }
  event.preventDefault(); // 阻止默认复制行为
  ElMessage.warning('考试期间禁止复制内容！'); // 显示警告
}

/**
 * 处理粘贴事件
 * 禁止粘贴内容到答案中
 * @param {ClipboardEvent} event - 剪贴板事件对象
 */
function handlePaste(event) {
  // 只有在考试进行中才拦截
  if (!examStore.isExamining) {
    return;
  }
  event.preventDefault(); // 阻止默认粘贴行为
  ElMessage.warning('考试期间禁止粘贴内容！'); // 显示警告
}

/**
 * 处理粘贴事件
 * 禁止粘贴内容到答案中
 * @param {ClipboardEvent} event - 剪贴板事件对象
 */
function handleBeforeUnload(event) {
  // 只有在考试进行中才拦截
  if (!examStore.isExamining) {
    return;
  }
  // 显示确认对话框，提示用户不要关闭页面
  event.preventDefault(); // 现代浏览器需要设置此属性
  event.returnValue = '考试期间请勿关闭页面！'; // 对话框提示文本
  return '考试期间请勿关闭页面！'; // 返回提示文本
}

// ==================== 生命周期钩子 ====================
onMounted(() => {
  // 添加各种事件监听器
  // 页面可见性变化监听（切换标签页）
  document.addEventListener('visibilitychange', handleVisibilityChange);
  // 窗口焦点变化监听（切换应用程序）
  window.addEventListener('blur', handleWindowBlur);
  // 键盘事件监听（快捷键）
  document.addEventListener('keydown', handleKeyDown);
  // 右键菜单事件监听（禁止右键）
  document.addEventListener('contextmenu', handleContextMenu);
  // 复制事件监听（禁止复制）
  document.addEventListener('copy', handleCopy);
  // 粘贴事件监听（禁止粘贴）
  document.addEventListener('paste', handlePaste);
  // 页面关闭/刷新前事件监听（防止意外关闭）
  window.addEventListener('beforeunload', handleBeforeUnload);
});

onUnmounted(() => {
  // 组件卸载时移除所有事件监听器，防止内存泄漏
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  window.removeEventListener('blur', handleWindowBlur);
  document.removeEventListener('keydown', handleKeyDown);
  document.removeEventListener('contextmenu', handleContextMenu);
  document.removeEventListener('copy', handleCopy);
  document.removeEventListener('paste', handlePaste);
  window.removeEventListener('beforeunload', handleBeforeUnload);
});
</script>
