/**
 * 全屏控制组件
 * 提供考试全屏模式控制功能，支持进入和退出全屏，以及全屏状态监听
 */
<template>
  <slot :isFullScreen="isFullScreen" :enterFullScreen="enterFullScreen" :exitFullScreen="exitFullScreen" /> <!-- 插槽，传递全屏状态和控制方法给父组件 -->
</template>

<script setup>
/**
 * 全屏控制组件逻辑
 * 提供全屏切换功能和状态管理
 */
import { ref, onMounted, onUnmounted } from 'vue'; // 引入Vue生命周期和响应式API
import { useExamStore } from '@/stores/exam'; // 引入考试状态管理

// ==================== 状态定义 ====================
const examStore = useExamStore(); // 获取考试状态管理实例
const isFullScreen = ref(false); // 全屏状态标记

// ==================== 生命周期钩子 ====================
onMounted(() => {
  // 组件挂载时，添加全屏状态变化事件监听
  document.addEventListener('fullscreenchange', handleFullScreenChange); // 监听全屏变化事件
  document.addEventListener('webkitfullscreenchange', handleFullScreenChange); // 兼容WebKit内核浏览器
  document.addEventListener('msfullscreenchange', handleFullScreenChange); // 兼容IE浏览器
});

onUnmounted(() => {
  // 组件卸载时，移除全屏状态变化事件监听
  document.removeEventListener('fullscreenchange', handleFullScreenChange);
  document.removeEventListener('webkitfullscreenchange', handleFullScreenChange);
  document.removeEventListener('msfullscreenchange', handleFullScreenChange);
});

// ==================== 方法定义 ====================
/**
 * 处理全屏状态变化事件
 * 当用户通过ESC退出全屏或调用API进入/退出全屏时触发
 */
function handleFullScreenChange() {
  // 判断当前是否为全屏状态
  isFullScreen.value = !!document.fullscreenElement;
  // 同步更新考试状态管理器的全屏状态
  examStore.setFullScreen(isFullScreen.value);
}

/**
 * 进入全屏模式方法
 * 尝试调用浏览器全屏API进入全屏
 */
function enterFullScreen() {
  const element = document.documentElement; // 获取HTML根元素作为全屏目标
  if (element.requestFullscreen) {
    // 标准全屏API
    element.requestFullscreen().then(() => {
      isFullScreen.value = true; // 进入成功，更新状态
      examStore.setFullScreen(true); // 同步更新考试状态管理器
    }).catch((err) => {
      console.error('进入全屏失败', err); // 进入失败，输出错误日志
    });
  } else if (element.webkitRequestFullScreen) {
    // WebKit内核浏览器（如Safari）全屏API
    element.webkitRequestFullScreen();
    isFullScreen.value = true;
    examStore.setFullScreen(true);
  } else if (element.msRequestFullscreen) {
    // IE浏览器全屏API
    element.msRequestFullscreen();
    isFullScreen.value = true;
    examStore.setFullScreen(true);
  } else {
    console.warn('当前浏览器不支持全屏模式'); // 浏览器不支持，输出警告
  }
}

/**
 * 退出全屏模式方法
 * 尝试调用浏览器API退出全屏
 */
function exitFullScreen() {
  if (document.exitFullscreen) {
    // 标准退出全屏API
    document.exitFullscreen().then(() => {
      isFullScreen.value = false; // 退出成功，更新状态
      examStore.setFullScreen(false); // 同步更新考试状态管理器
    }).catch((err) => {
      console.error('退出全屏失败', err); // 退出失败，输出错误日志
    });
  } else if (document.webkitCancelFullScreen) {
    // WebKit内核浏览器退出全屏API
    document.webkitCancelFullScreen();
    isFullScreen.value = false;
    examStore.setFullScreen(false);
  } else if (document.msExitFullscreen) {
    // IE浏览器退出全屏API
    document.msExitFullscreen();
    isFullScreen.value = false;
    examStore.setFullScreen(false);
  }
}

/**
 * 切换全屏模式方法
 * 根据当前状态进入或退出全屏
 */
function toggleFullScreen() {
  if (isFullScreen.value) {
    exitFullScreen(); // 当前是全屏，则退出
  } else {
    enterFullScreen(); // 当前不是全屏，则进入
  }
}
</script>
