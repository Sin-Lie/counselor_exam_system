/**
 * 批改面板组件
 * 管理员批改简答题时使用，显示学生答案、标准答案，并提供打分和提交功能
 */
<template>
  <div class="correct-panel">
    <!-- ==================== 学生信息区域 ==================== -->
    <div class="student-info">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="学生姓名">{{ studentInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{ studentInfo.jobNumber }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ studentInfo.submitTime }}</el-descriptions-item>
        <el-descriptions-item label="客观题得分">{{ studentInfo.objectiveScore || 0 }}分</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- ==================== 答题信息区域 ==================== -->
    <div class="answer-section">
      <el-card shadow="never" class="question-card">
        <template #header>
          <div class="card-header">
            <span class="header-title">题目信息</span>
          </div>
        </template>
        <div class="question-content">
          <el-tag type="info" size="small" class="type-tag">简答题</el-tag>
          <p class="question-text">{{ questionData.content }}</p>
        </div>
      </el-card>

      <!-- 标准答案 -->
      <el-card shadow="never" class="answer-card standard">
        <template #header>
          <div class="card-header">
            <span class="header-title">标准答案</span>
          </div>
        </template>
        <div class="answer-content">
          {{ questionData.answer }}
        </div>
      </el-card>

      <!-- 学生答案 -->
      <el-card shadow="never" class="answer-card student">
        <template #header>
          <div class="card-header">
            <span class="header-title">学生答案</span>
          </div>
        </template>
        <div class="answer-content">
          {{ studentAnswer || '学生未作答' }}
        </div>
      </el-card>
    </div>

    <!-- ==================== 批改区域 ==================== -->
    <div class="score-section">
      <el-form :model="scoreForm" :rules="scoreRules" ref="scoreFormRef" label-width="80px">
        <!-- 分数输入 -->
        <el-form-item label="得分" prop="score">
          <el-input-number
            v-model="scoreForm.score"
            :min="0"
            :max="questionData.score || 10"
            :precision="0"
            controls-position="right"
            class="score-input"
          />
          <span class="score-unit">/ {{ questionData.score || 10 }} 分</span>
        </el-form-item>

        <!-- 评语输入 -->
        <el-form-item label="评语" prop="comment">
          <el-input
            v-model="scoreForm.comment"
            type="textarea"
            :rows="3"
            placeholder="请输入评语（可选）..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </div>

    <!-- ==================== 操作按钮区域 ==================== -->
    <div class="action-section">
      <el-button @click="handleReset">重置</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        提交评分
      </el-button>
    </div>
  </div>
</template>

<script setup>
/**
 * 批改面板组件逻辑
 * 处理批改表单提交、分数验证等功能
 */
import { ref, reactive, watch } from 'vue'; // 引入Vue响应式API
import { ElMessage } from 'element-plus'; // 引入Element Plus消息组件

// ==================== Props定义 ====================
const props = defineProps({
  studentInfo: {
    type: Object,
    required: true, // 学生信息必填
    default: () => ({ name: '', jobNumber: '', submitTime: '', objectiveScore: 0 }),
  },
  questionData: {
    type: Object,
    required: true, // 题目信息必填
    default: () => ({ content: '', answer: '', score: 10 }),
  },
  studentAnswer: {
    type: String,
    default: '', // 学生答案
  },
  initialScore: {
    type: Number,
    default: null, // 初始分数（编辑时传入）
  },
  initialComment: {
    type: String,
    default: '', // 初始评语
  },
});

// ==================== 事件定义 ====================
const emit = defineEmits(['submit', 'reset']); // 定义提交和重置事件

// ==================== 状态定义 ====================
const scoreFormRef = ref(null); // 表单引用
const submitting = ref(false); // 提交按钮加载状态
const scoreForm = reactive({
  score: null, // 分数
  comment: '', // 评语
});

// 表单验证规则
const scoreRules = {
  score: [
    { required: true, message: '请输入分数', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value < 0 || value > (props.questionData.score || 10)) {
          callback(new Error(`分数应在0-${props.questionData.score || 10}之间`));
        } else {
          callback();
        }
      },
      trigger: 'change',
    },
  ],
};

// ==================== 监听器 ====================
// 监听初始分数变化
watch(
  () => props.initialScore,
  (newVal) => {
    if (newVal !== null) {
      scoreForm.score = newVal;
    }
  },
  { immediate: true }
);

// 监听初始评语变化
watch(
  () => props.initialComment,
  (newVal) => {
    scoreForm.comment = newVal || '';
  },
  { immediate: true }
);

// ==================== 方法定义 ====================
/**
 * 重置表单
 */
function handleReset() {
  scoreFormRef.value?.resetFields(); // 重置表单字段
  scoreForm.score = null;
  scoreForm.comment = '';
  emit('reset'); // 触发重置事件
}

/**
 * 提交评分
 */
async function handleSubmit() {
  // 表单验证
  try {
    await scoreFormRef.value.validate();
  } catch (error) {
    return; // 验证失败，不提交
  }

  // 检查分数是否有效
  if (scoreForm.score === null) {
    ElMessage.warning('请输入分数');
    return;
  }

  // 触发提交事件
  submitting.value = true;
  try {
    emit('submit', {
      score: scoreForm.score,
      comment: scoreForm.comment,
    });
  } finally {
    submitting.value = false;
  }
}

/**
 * 设置分数（外部调用）
 * @param {number} score - 分数值
 */
function setScore(score) {
  scoreForm.score = score;
}

/**
 * 设置评语（外部调用）
 * @param {string} comment - 评语文本
 */
function setComment(comment) {
  scoreForm.comment = comment;
}
</script>

<style scoped>
/**
 * 批改面板样式
 */
.correct-panel {
  background-color: #fff; /* 白色背景 */
  border-radius: 8px; /* 圆角8px */
  padding: 20px; /* 内边距20px */
}

/* ==================== 学生信息样式 ==================== */
.student-info {
  margin-bottom: 20px; /* 底部外边距20px */
  padding-bottom: 20px; /* 底部内边距20px */
  border-bottom: 1px solid #eee; /* 底部边框 */
}

/* ==================== 答题信息样式 ==================== */
.answer-section {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  gap: 16px; /* 子元素之间16px间距 */
  margin-bottom: 20px; /* 底部外边距20px */
}

.question-card,
.answer-card {
  border: 1px solid #e4e7ed; /* 边框 */
}

.card-header {
  display: flex; /* 弹性布局 */
  justify-content: space-between; /* 左右分散对齐 */
  align-items: center; /* 垂直居中对齐 */
}

.header-title {
  font-weight: 600; /* 粗体 */
  color: #303133; /* 深灰色 */
}

.type-tag {
  margin-bottom: 12px; /* 底部外边距12px */
}

.question-text {
  font-size: 15px; /* 字号15px */
  line-height: 1.6; /* 行高1.6 */
  color: #303133; /* 深灰色 */
  margin: 0; /* 清除默认外边距 */
}

.answer-card.standard .answer-content {
  color: #67c23a; /* 绿色（标准答案） */
  font-size: 14px; /* 字号14px */
  line-height: 1.6; /* 行高1.6 */
  background-color: #f0f9eb; /* 浅绿背景 */
  padding: 12px; /* 内边距12px */
  border-radius: 4px; /* 圆角4px */
}

.answer-card.student .answer-content {
  color: #606266; /* 中灰色（学生答案） */
  font-size: 14px; /* 字号14px */
  line-height: 1.6; /* 行高1.6 */
  background-color: #f5f7fa; /* 浅灰背景 */
  padding: 12px; /* 内边距12px */
  border-radius: 4px; /* 圆角4px */
}

/* ==================== 批改区域样式 ==================== */
.score-section {
  margin-bottom: 20px; /* 底部外边距20px */
  padding: 20px; /* 内边距20px */
  background-color: #f5f7fa; /* 浅灰背景 */
  border-radius: 8px; /* 圆角8px */
}

.score-input {
  width: 120px; /* 宽度120px */
}

.score-unit {
  margin-left: 8px; /* 左侧外边距8px */
  color: #909399; /* 灰色文字 */
}

/* ==================== 操作按钮样式 ==================== */
.action-section {
  display: flex; /* 弹性布局 */
  justify-content: flex-end; /* 右对齐 */
  gap: 12px; /* 子元素之间12px间距 */
  padding-top: 20px; /* 顶部内边距20px */
  border-top: 1px solid #eee; /* 顶部边框 */
}
</style>
