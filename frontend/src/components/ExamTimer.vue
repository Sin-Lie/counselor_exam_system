/**
 * 考试倒计时组件
 * 显示考试剩余时间，当剩余时间不足时显示警告，支持自动交卷
 */
<template>
  <div class="exam-timer" :class="{ warning: isWarning, danger: isDanger }">
    <!-- 倒计时显示区域 -->
    <div class="timer-icon">
      <el-icon><Clock /></el-icon> <!-- 闹钟图标 -->
    </div>
    <div class="timer-content">
      <!-- 剩余时间文本显示 -->
      <span class="timer-label">剩余时间</span> <!-- 标签文本 -->
      <span class="timer-value">{{ formattedTime }}</span> <!-- 格式化的时间值 -->
    </div>
    <!-- 交卷按钮 -->
    <el-button
      v-if="showSubmitBtn"
      type="danger"
      size="small"
      @click="handleSubmit"
      :loading="isSubmitting"
    >
      交卷
    </el-button>
  </div>
</template>

<script setup>
/**
 * 考试倒计时组件逻辑
 * 监听考试状态，显示倒计时，并在时间耗尽时自动交卷
 */
import { computed, ref, watch, onUnmounted } from 'vue'; // 引入Vue组合式API
import { useExamStore } from '@/stores/exam'; // 引入考试状态管理
import { ElMessageBox, ElMessage } from 'element-plus'; // 引入Element Plus对话框和消息

// ==================== Props定义 ====================
const props = defineProps({
  showSubmitBtn: {
    type: Boolean,
    default: true, // 默认显示交卷按钮
  },
});

// ==================== 事件定义 ====================
const emit = defineEmits(['submit']); // 定义提交事件

// ==================== 状态管理 ====================
const examStore = useExamStore(); // 获取考试状态管理实例
const isSubmitting = ref(false); // 交卷按钮加载状态

// ==================== 计算属性 ====================
// 格式化剩余时间显示
const formattedTime = computed(() => {
  const remaining = examStore.remainingTime; // 获取剩余秒数
  const hours = Math.floor(remaining / 3600); // 计算小时数
  const minutes = Math.floor((remaining % 3600) / 60); // 计算分钟数
  const seconds = remaining % 60; // 计算秒数
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
});

// 是否处于警告状态（剩余时间少于10分钟）
const isWarning = computed(() => {
  return examStore.remainingTime <= 600 && examStore.remainingTime > 300; // 10分钟到5分钟之间为警告
});

// 是否处于危险状态（剩余时间少于5分钟）
const isDanger = computed(() => {
  return examStore.remainingTime <= 300; // 少于5分钟为危险
});

// ==================== 方法定义 ====================
/**
 * 处理交卷按钮点击事件
 * 弹出确认框，用户确认后执行交卷操作
 */
async function handleSubmit() {
  // 计算未答题目数量
  const unanswered = examStore.unansweredCount;

  // 构建确认消息
  let message = '确定要交卷吗？';
  if (unanswered > 0) {
    message += `您还有 ${unanswered} 道题未答。`;
  }

  try {
    // 弹出确认对话框
    await ElMessageBox.confirm(message, '交卷确认', {
      confirmButtonText: '确定交卷', // 确认按钮文字
      cancelButtonText: '继续答题', // 取消按钮文字
      type: 'warning', // 警告类型
    });

    // 用户确认交卷
    isSubmitting.value = true; // 显示加载状态
    const result = await examStore.submitExamPaper(); // 调用交卷方法
    emit('submit', result); // 触发提交事件
    ElMessage.success('交卷成功'); // 显示成功提示
  } catch (e) {
    // 用户取消交卷，不做任何处理
  } finally {
    isSubmitting.value = false; // 关闭加载状态
  }
}

// ==================== 监听器 ====================
// 监听剩余时间，当时间耗尽时自动交卷
watch(() => examStore.remainingTime, (newVal) => {
  if (newVal === 0 && examStore.isExamining) {
    // 时间耗尽且正在考试，执行自动交卷
    ElMessage.warning('考试时间已到，自动交卷'); // 显示警告消息
    examStore.handleAutoSubmit(); // 调用自动交卷方法
  }
});

// ==================== 生命周期钩子 ====================
onUnmounted(() => {
  // 组件卸载时的清理工作（如果需要）
});
</script>

<style scoped>
/**
 * 倒计时组件样式
 */
.exam-timer {
  display: flex; /* 使用弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 12px; /* 子元素之间12px间距 */
  padding: 8px 16px; /* 内边距：上下8px，左右16px */
  background-color: #fff; /* 白色背景 */
  border-radius: 8px; /* 圆角8px */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 阴影效果 */
  transition: all 0.3s ease; /* 所有属性过渡动画0.3秒 */
}

/* 警告状态样式（剩余时间5-10分钟） */
.exam-timer.warning {
  background-color: #e6a23c; /* 橙色背景 */
  color: #fff; /* 白色文字 */
}

/* 危险状态样式（剩余时间少于5分钟） */
.exam-timer.danger {
  background-color: #f56c6c; /* 红色背景 */
  color: #fff; /* 白色文字 */
  animation: pulse 1s infinite; /* 脉动动画效果 */
}

/* 闹钟图标样式 */
.timer-icon {
  font-size: 24px; /* 图标尺寸 */
}

/* 计时器内容区域样式 */
.timer-content {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  align-items: flex-start; /* 左对齐 */
}

/* 标签文本样式 */
.timer-label {
  font-size: 12px; /* 字号12px */
  opacity: 0.8; /* 半透明效果 */
}

/* 时间值样式 */
.timer-value {
  font-size: 20px; /* 字号20px */
  font-weight: 600; /* 粗体字重 */
  font-family: 'Courier New', monospace; /* 等宽字体 */
}

/* 脉动动画关键帧 */
@keyframes pulse {
  0% {
    transform: scale(1); /* 初始状态 */
  }
  50% {
    transform: scale(1.02); /* 放大状态 */
  }
  100% {
    transform: scale(1); /* 恢复初始状态 */
  }
}
</style>
