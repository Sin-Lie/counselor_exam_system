/** * 练习题目卡片组件 * 用于显示练习题目，支持单选题、多选题、判断题、简答题四种题型 *
提供答题、收藏、查看答案等功能 */
<template>
  <div class="practice-card">
    <!-- ==================== 题目头部信息 ==================== -->
    <div class="card-header">
      <!-- 题目类型标签 -->
      <el-tag :type="questionTypeTagType" size="small" class="type-tag">
        {{ questionTypeText }}
      </el-tag>
      <!-- 题目分值 -->
      <span class="question-score">{{ question.score || 0 }}分</span>
      <!-- 收藏按钮 -->
      <el-button
        :type="isCollected ? 'warning' : 'default'"
        :icon="isCollected ? 'Star' : 'Star'"
        circle
        size="small"
        class="collect-btn"
        @click="handleToggleCollect"
        :loading="collectLoading"
      />
    </div>

    <!-- ==================== 题目内容区域 ==================== -->
    <div class="card-body">
      <!-- 题目编号和内容 -->
      <div class="question-content">
        <span class="question-number">{{ questionNumber }}.</span>
        <span class="question-text">{{ question.content }}</span>
      </div>

      <!-- ==================== 选项区域 ==================== -->
      <!-- 单选题选项 -->
      <div v-if="question.type === 'single'" class="options-list">
        <div
          v-for="(option, index) in question.options"
          :key="index"
          class="option-item"
          :class="{
            selected: selectedAnswer === option.key,
            correct: showAnswer && option.key === correctAnswer,
            incorrect: showAnswer && selectedAnswer === option.key && option.key !== correctAnswer,
          }"
          @click="handleSelectOption(option.key)"
        >
          <span class="option-key">{{ option.key }}.</span>
          <span class="option-text">{{ option.value }}</span>
          <!-- 正确答案标记 -->
          <el-icon v-if="showAnswer && option.key === correctAnswer" class="correct-icon"
            ><Check
          /></el-icon>
          <!-- 错误答案标记 -->
          <el-icon
            v-if="showAnswer && selectedAnswer === option.key && option.key !== correctAnswer"
            class="incorrect-icon"
            ><Close
          /></el-icon>
        </div>
      </div>

      <!-- 多选题选项 -->
      <div v-else-if="question.type === 'multiple'" class="options-list">
        <div
          v-for="(option, index) in question.options"
          :key="index"
          class="option-item multiple"
          :class="{
            selected: selectedAnswer && selectedAnswer.includes(option.key),
            correct: showAnswer && correctAnswerList.includes(option.key),
            incorrect:
              showAnswer &&
              selectedAnswer &&
              selectedAnswer.includes(option.key) &&
              correctAnswerList.length > 0 &&
              !correctAnswerList.includes(option.key),
          }"
          @click="handleToggleMultiple(option.key)"
        >
          <el-checkbox
            :model-value="selectedAnswer && selectedAnswer.includes(option.key)"
            :disabled="showAnswer"
          />
          <span class="option-key">{{ option.key }}.</span>
          <span class="option-text">{{ option.value }}</span>
          <!-- 正确答案标记 -->
          <el-icon
            v-if="showAnswer && correctAnswerList.includes(option.key)"
            class="correct-icon"
            ><Check
          /></el-icon>
        </div>
      </div>

      <!-- 判断题选项 -->
      <div v-else-if="question.type === 'judge'" class="options-list judge">
        <div
          class="option-item"
          :class="{
            selected: selectedAnswer === 'A',
            correct: showAnswer && correctAnswer === 'A',
            incorrect: showAnswer && selectedAnswer === 'A' && correctAnswer !== 'A',
          }"
          @click="handleSelectOption('A')"
        >
          <el-radio v-model="selectedAnswer" label="A" :disabled="showAnswer">正确</el-radio>
          <el-icon v-if="showAnswer && correctAnswer === 'A'" class="correct-icon"
            ><Check
          /></el-icon>
          <el-icon
            v-if="showAnswer && selectedAnswer === 'A' && correctAnswer !== 'A'"
            class="incorrect-icon"
            ><Close
          /></el-icon>
        </div>
        <div
          class="option-item"
          :class="{
            selected: selectedAnswer === 'B',
            correct: showAnswer && correctAnswer === 'B',
            incorrect: showAnswer && selectedAnswer === 'B' && correctAnswer !== 'B',
          }"
          @click="handleSelectOption('B')"
        >
          <el-radio v-model="selectedAnswer" label="B" :disabled="showAnswer">错误</el-radio>
          <el-icon v-if="showAnswer && correctAnswer === 'B'" class="correct-icon"
            ><Check
          /></el-icon>
          <el-icon
            v-if="showAnswer && selectedAnswer === 'B' && correctAnswer !== 'B'"
            class="incorrect-icon"
            ><Close
          /></el-icon>
        </div>
      </div>

      <!-- 简答题输入框 -->
      <div v-else-if="question.type === 'short'" class="short-answer">
        <el-input
          v-model="shortAnswer"
          type="textarea"
          :rows="4"
          placeholder="请输入您的答案..."
          :disabled="showAnswer"
          @input="handleShortAnswerInput"
        />
        <!-- 正确答案提示 -->
        <div v-if="showAnswer" class="answer-tip">
          <span class="tip-label">标准答案：</span>
          <span class="tip-content">{{ correctAnswer }}</span>
        </div>
      </div>
    </div>

    <!-- ==================== 答案解析区域 ==================== -->
    <div v-if="showAnswer && question.explanation" class="card-footer">
      <div class="explanation">
        <span class="explanation-label">答案解析：</span>
        <span class="explanation-text">{{ question.explanation }}</span>
      </div>
    </div>

    <!-- ==================== 操作按钮区域 ==================== -->
    <div class="card-actions">
      <!-- 提交答案按钮 -->
      <!-- 提交本题按钮 -->
      <el-button
        v-if="!showAnswer"
        type="primary"
        @click="handleSubmitAnswer"
        :disabled="!hasAnswer"
      >
        提交本题
      </el-button>

      <!-- 下一题按钮 -->
      <el-button v-if="showAnswer" type="success" @click="handleNext"> 下一题 </el-button>
    </div>
  </div>
</template>

<script setup>
/**
 * 练习题目卡片组件逻辑
 * 处理题目显示、答题选择、答案提交等功能
 */
import { ref, computed } from 'vue' // 引入Vue响应式API
import { ElMessage } from 'element-plus' // 引入Element Plus消息组件
import { Check, Close } from '@element-plus/icons-vue' // 引入Element Plus图标

// ==================== Props定义 ====================
const props = defineProps({
  question: {
    type: Object,
    required: true, // 题目数据必填
  },
  questionNumber: {
    type: Number,
    default: 1, // 题目编号，默认1
  },
  isCollected: {
    type: Boolean,
    default: false, // 是否已收藏
  },
  correctAnswer: {
    type: [String, Array],
    default: '', // 提交后返回的正确答案
  },
})

// ==================== 事件定义 ====================
const emit = defineEmits(['submit', 'next', 'collect', 'uncollect']) // 定义组件事件

// ==================== 状态定义 ====================
const selectedAnswer = ref(null) // 选中的答案（单选、判断）
const shortAnswer = ref('') // 简答题答案
const showAnswer = ref(false) // 是否显示答案
const collectLoading = ref(false) // 收藏按钮加载状态

// ==================== 计算属性 ====================
const correctAnswerList = computed(() => normalizeAnswerList(props.correctAnswer))

// 题目类型文本
const questionTypeText = computed(() => {
  const typeMap = {
    single: '单选题',
    multiple: '多选题',
    judge: '判断题',
    short: '简答题',
  }
  return typeMap[props.question.type] || '未知类型'
})

// 题目类型标签颜色
const questionTypeTagType = computed(() => {
  const typeMap = {
    single: 'primary',
    multiple: 'success',
    judge: 'warning',
    short: 'info',
  }
  return typeMap[props.question.type] || 'info'
})

// 是否已选择答案
const hasAnswer = computed(() => {
  if (props.question.type === 'multiple') {
    return selectedAnswer.value && selectedAnswer.value.length > 0
  }
  if (props.question.type === 'short') {
    return shortAnswer.value.trim().length > 0
  }
  return selectedAnswer.value !== null
})

// ==================== 方法定义 ====================
function normalizeAnswerList(answer) {
  if (Array.isArray(answer)) {
    return answer.map((item) => String(item).trim()).filter(Boolean)
  }
  const raw = String(answer || '').replace(/，/g, ',').trim()
  if (!raw) return []
  if (raw.includes(',')) {
    return raw
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  }
  return raw.split('').map((item) => item.trim()).filter(Boolean)
}

/**
 * 处理单选题选项点击
 * @param {string} key - 选项键值
 */
function handleSelectOption(key) {
  if (showAnswer.value) return // 已显示答案时不可点击
  selectedAnswer.value = key
}

/**
 * 处理多选题选项切换
 * @param {string} key - 选项键值
 */
function handleToggleMultiple(key) {
  if (showAnswer.value) return // 已显示答案时不可点击
  if (!selectedAnswer.value) {
    selectedAnswer.value = []
  }
  const index = selectedAnswer.value.indexOf(key)
  if (index > -1) {
    selectedAnswer.value.splice(index, 1) // 已选中，取消选择
  } else {
    selectedAnswer.value.push(key) // 未选中，添加选择
  }
}

/**
 * 处理简答题输入
 * @param {string} value - 输入的文本
 */
function handleShortAnswerInput(value) {
  shortAnswer.value = value
}

/**
 * 处理提交答案
 */
function handleSubmitAnswer() {
  if (!hasAnswer.value) {
    ElMessage.warning('请先选择或输入答案') // 提示用户先答题
    return
  }

  // 提交后显示答案状态（正确/错误）
  showAnswer.value = true

  // 触发提交答案事件
  let answer = selectedAnswer.value
  if (props.question.type === 'multiple') {
    // 多选题答案转换为字符串格式，按字母顺序排序后用逗号分隔
    answer = [...selectedAnswer.value].sort().join(',')
  } else if (props.question.type === 'short') {
    answer = shortAnswer.value
  }

  emit('submit', {
    questionId: props.question.id,
    answer: answer,
  })
}

/**
 * 处理下一题
 */
function handleNext() {
  // 重置状态
  selectedAnswer.value = null
  shortAnswer.value = ''
  showAnswer.value = false

  // 触发下一题事件
  emit('next')
}

/**
 * 处理收藏/取消收藏
 */
async function handleToggleCollect() {
  collectLoading.value = true
  try {
    if (props.isCollected) {
      emit('uncollect', props.question.id)
    } else {
      emit('collect', props.question.id)
    }
  } finally {
    collectLoading.value = false
  }
}

/**
 * 重置答题状态（外部调用）
 */
function reset() {
  selectedAnswer.value = null
  shortAnswer.value = ''
  showAnswer.value = false
}

// 暴露方法给父组件
defineExpose({ reset })
</script>

<style scoped>
/**
 * 练习题目卡片样式
 */
.practice-card {
  background-color: #fff; /* 白色背景 */
  border-radius: 8px; /* 圆角8px */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1); /* 阴影效果 */
  padding: 20px; /* 内边距20px */
}

/* ==================== 头部样式 ==================== */
.card-header {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 10px; /* 子元素之间10px间距 */
  margin-bottom: 16px; /* 底部外边距16px */
  padding-bottom: 12px; /* 底部内边距12px */
  border-bottom: 1px solid #eee; /* 底部边框 */
}

.type-tag {
  margin-right: auto; /* 右侧外边距自动，推到左边 */
}

.question-score {
  color: #909399; /* 灰色文字 */
  font-size: 14px; /* 字号14px */
}

.collect-btn {
  margin-left: 8px; /* 左侧外边距8px */
}

/* ==================== 题目内容样式 ==================== */
.card-body {
  margin-bottom: 16px; /* 底部外边距16px */
}

.question-content {
  font-size: 16px; /* 字号16px */
  line-height: 1.6; /* 行高1.6 */
  margin-bottom: 16px; /* 底部外边距16px */
}

.question-number {
  color: #409eff; /* 蓝色编号 */
  font-weight: 600; /* 粗体 */
  margin-right: 8px; /* 右侧外边距8px */
}

.question-text {
  color: #303133; /* 深灰色文字 */
}

/* ==================== 选项样式 ==================== */
.options-list {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  gap: 10px; /* 子元素之间10px间距 */
}

.option-item {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  padding: 12px 16px; /* 内边距：上下12px，左右16px */
  border: 1px solid #dcdfe6; /* 边框 */
  border-radius: 6px; /* 圆角6px */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.2s; /* 过渡效果 */
  gap: 8px; /* 子元素之间8px间距 */
}

.option-item:hover {
  border-color: #409eff; /* 悬停时蓝色边框 */
  background-color: #ecf5ff; /* 悬停时浅蓝背景 */
}

.option-item.selected {
  border-color: #409eff; /* 选中时蓝色边框 */
  background-color: #ecf5ff; /* 选中时浅蓝背景 */
}

.option-item.correct {
  border-color: #67c23a; /* 正确时绿色边框 */
  background-color: #f0f9eb; /* 正确时浅绿背景 */
}

.option-item.selected.correct {
  border-color: #67c23a; /* 同时选中和正确时绿色边框 */
  background-color: #f0f9eb; /* 同时选中和正确时浅绿背景 */
}

.option-item.incorrect {
  border-color: #f56c6c; /* 错误时红色边框 */
  background-color: #fef0f0; /* 错误时浅红背景 */
}

.option-item.selected.incorrect {
  border-color: #f56c6c; /* 同时选中和错误时红色边框 */
  background-color: #fef0f0; /* 同时选中和错误时浅红背景 */
}

.option-key {
  font-weight: 600; /* 粗体 */
  color: #303133; /* 深灰色 */
}

.option-text {
  color: #606266; /* 中灰色文字 */
}

.correct-icon {
  margin-left: auto; /* 左侧外边距自动，推到右边 */
  color: #67c23a; /* 绿色 */
  font-size: 18px; /* 字号18px */
}

.incorrect-icon {
  margin-left: auto; /* 左侧外边距自动 */
  color: #f56c6c; /* 红色 */
  font-size: 18px; /* 字号18px */
}

/* ==================== 判断题样式 ==================== */
.options-list.judge {
  flex-direction: row; /* 水平排列 */
  gap: 20px; /* 子元素之间20px间距 */
}

.options-list.judge .option-item {
  flex: 1; /* 平分宽度 */
  justify-content: center; /* 水平居中 */
}

/* ==================== 简答题样式 ==================== */
.short-answer {
  margin-top: 16px; /* 顶部外边距16px */
}

.answer-tip {
  margin-top: 12px; /* 顶部外边距12px */
  padding: 12px; /* 内边距12px */
  background-color: #f0f9eb; /* 浅绿背景 */
  border-radius: 6px; /* 圆角6px */
  font-size: 14px; /* 字号14px */
}

.tip-label {
  color: #67c23a; /* 绿色标签 */
  font-weight: 600; /* 粗体 */
}

.tip-content {
  color: #606266; /* 中灰色文字 */
}

/* ==================== 答案解析样式 ==================== */
.card-footer {
  padding-top: 12px; /* 顶部内边距12px */
  border-top: 1px solid #eee; /* 顶部边框 */
}

.explanation {
  font-size: 14px; /* 字号14px */
  line-height: 1.6; /* 行高1.6 */
}

.explanation-label {
  color: #e6a23c; /* 橙色标签 */
  font-weight: 600; /* 粗体 */
}

.explanation-text {
  color: #606266; /* 中灰色文字 */
}

/* ==================== 操作按钮样式 ==================== */
.card-actions {
  display: flex; /* 弹性布局 */
  justify-content: flex-end; /* 右对齐 */
  gap: 12px; /* 子元素之间12px间距 */
  padding-top: 16px; /* 顶部内边距16px */
  border-top: 1px solid #eee; /* 顶部边框 */
}
</style>
