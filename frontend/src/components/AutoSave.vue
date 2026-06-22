/**
 * 自动保存组件
 * 在考试过程中自动保存考生的答题进度，防止意外丢失答案
 * 支持定时保存和答案变化时保存
 */
<template>
  <slot /> <!-- 默认插槽，用于包装考试答题内容 -->
</template>

<script setup>
/**
 * 自动保存组件逻辑
 * 监听答案变化并在适当时机自动保存到服务器
 */
import { ref, watch, onMounted, onUnmounted } from 'vue'; // 引入Vue生命周期和响应式API
import { useExamStore } from '@/stores/exam'; // 引入考试状态管理
import { ElMessage } from 'element-plus'; // 引入Element Plus消息组件

// ==================== Props定义 ====================
const props = defineProps({
  autoSaveInterval: {
    type: Number,
    default: 30000, // 自动保存间隔时间，默认30秒
  },
  debounceDelay: {
    type: Number,
    default: 1000, // 防抖延迟时间，默认1秒
  },
});

// ==================== 状态定义 ====================
const examStore = useExamStore(); // 获取考试状态管理实例
let autoSaveTimer = null; // 自动保存定时器ID
let debounceTimer = null; // 防抖定时器ID
const lastSaveAnswer = ref(null); // 上次保存的答案记录
const isAutoSaving = ref(false); // 自动保存中状态标记

// ==================== 方法定义 ====================
/**
 * 执行自动保存方法
 * 将所有已答题目批量保存到服务器
 */
async function performAutoSave() {
  // 如果已交卷或正在保存，直接返回
  if (examStore.isSubmitted || isAutoSaving.value) {
    return;
  }

  // 获取所有已答题目
  const answeredList = Array.from(examStore.answers.entries());

  // 如果没有已答题目，直接返回
  if (answeredList.length === 0) {
    return;
  }

  // 检查答案是否有变化
  const currentAnswerStr = JSON.stringify(answeredList);
  if (currentAnswerStr === lastSaveAnswer.value) {
    return; // 答案没有变化，不需要保存
  }

  // 设置保存状态
  isAutoSaving.value = true;

  try {
    // 将答案转换为批量保存格式
    const answersData = answeredList.map(([questionId, answer]) => ({
      question_id: questionId,
      user_answer: answer,
    }));

    // 调用批量保存方法
    await examStore.autoSaveAnswers(answersData);

    // 更新最后保存的答案记录
    lastSaveAnswer.value = currentAnswerStr;

    // 更新最后保存时间
    examStore.lastSaveTime = new Date();

  } catch (error) {
    // 保存失败，输出错误日志（不弹窗避免打扰考试）
    console.error('批量自动保存失败', error);
  } finally {
    // 关闭保存状态
    isAutoSaving.value = false;
  }
}

/**
 * 防抖保存方法
 * 在一定时间内的多次调用只执行一次保存
 */
function debouncedSave() {
  // 清除之前的防抖定时器
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  // 设置新的防抖定时器
  debounceTimer = setTimeout(() => {
    performAutoSave(); // 防抖时间到了后执行保存
  }, props.debounceDelay);
}

/**
 * 启动自动保存定时器
 * 按照设定的间隔定期保存答案
 */
function startAutoSaveTimer() {
  // 如果定时器已存在，先清除
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer);
  }

  // 设置定时器，定期执行保存
  autoSaveTimer = setInterval(() => {
    // 只有在考试进行中才执行保存
    if (examStore.isExamining && !examStore.isSubmitted) {
      performAutoSave();
    }
  }, props.autoSaveInterval);
}

/**
 * 停止自动保存定时器
 */
function stopAutoSaveTimer() {
  if (autoSaveTimer) {
    clearInterval(autoSaveTimer);
    autoSaveTimer = null;
  }
}

// ==================== 监听器 ====================
// 监听答题记录变化，自动保存
watch(
  () => examStore.answers,
  () => {
    // 只有在考试进行中才监听
    if (examStore.isExamining && !examStore.isSubmitted) {
      debouncedSave(); // 使用防抖方式保存
    }
  },
  { deep: true } // 深度监听，检测嵌套属性的变化
);

// 监听考试状态变化
watch(
  () => examStore.isExamining,
  (isExamining) => {
    if (isExamining) {
      // 开始考试，启动自动保存
      startAutoSaveTimer();
    } else {
      // 考试结束，停止自动保存
      stopAutoSaveTimer();
    }
  }
);

// ==================== 生命周期钩子 ====================
onMounted(() => {
  // 组件挂载时，如果正在考试，启动自动保存
  if (examStore.isExamining) {
    startAutoSaveTimer();
  }
});

onUnmounted(() => {
  // 组件卸载时，执行一次最终保存
  performAutoSave();
  // 清除所有定时器
  stopAutoSaveTimer();
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
});
</script>
