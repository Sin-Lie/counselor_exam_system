<template>
  <div class="score-detail-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft" class="back-btn">返回</el-button>
        <h2 class="page-title">{{ props.examTitle || '成绩详情' }}</h2>
      </div>
      <div class="header-right">
        <span class="total-info">
          共 <strong>{{ questionList.length }}</strong> 题， 总分
          <strong class="score-highlight">{{ totalUserScore }}</strong> / {{ totalFullScore }} 分
        </span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <p>加载试卷详情中...</p>
    </div>

    <!-- 题目列表 -->
    <div v-else class="question-list">
      <el-card
        v-for="(item, index) in questionList"
        :key="item.question_id"
        shadow="never"
        class="question-card"
      >
        <template #header>
          <div class="question-header">
            <div class="question-header-left">
              <span class="question-num">第 {{ index + 1 }} 题</span>
              <el-tag :type="getTypeTag(item.question_type)" size="small">
                {{ getTypeText(item.question_type) }}
              </el-tag>
            </div>
            <div class="question-header-right">
              <span
                class="question-score"
                :class="item.user_score === item.score ? 'score-correct' : 'score-wrong'"
              >
                {{ item.user_score }} / {{ item.score }} 分
              </span>
            </div>
          </div>
        </template>

        <!-- 题目内容 -->
        <div class="question-body">
          <p class="question-title">{{ item.title }}</p>
        </div>

        <!-- 答案对比区域 -->
        <div class="answer-compare">
          <div class="answer-row">
            <span class="answer-label">我的答案：</span>
            <span
              class="answer-value"
              :class="item.user_score === item.score ? 'answer-right' : 'answer-wrong'"
            >
              {{ formatAnswer(item.user_answer, item.question_type) }}
            </span>
          </div>
          <div class="answer-row">
            <span class="answer-label">正确答案：</span>
            <span class="answer-value answer-correct">
              {{ formatAnswer(item.correct_answer, item.question_type) }}
            </span>
          </div>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="questionList.length === 0" description="暂无题目详情" />
    </div>
  </div>
</template>

<script setup>
/**
 * 成绩详情页面逻辑
 * 通过 props 接收考试ID和名称，调用API获取试卷详情
 */
import { ref, computed, watch } from 'vue' // 引入Vue响应式API
import { ElMessage } from 'element-plus' // 引入Element Plus消息组件
import { ArrowLeft, Loading } from '@element-plus/icons-vue' // 引入图标
import { getMyPaperDetail } from '@/api/exam' // 引入试卷详情API

// ==================== Props 定义 ====================
const props = defineProps({
  examId: { // 试卷ID（paper_id），用于调用试卷详情API
    type: [String, Number], // 支持字符串和数字类型
    required: true, // 必填
  },
  examTitle: { // 考试名称
    type: String, // 字符串类型
    default: '成绩详情', // 默认值
  },
})

// ==================== Emits 定义 ====================
const emit = defineEmits(['back']) // 定义返回事件

// ==================== 状态定义 ====================
const loading = ref(false) // 加载状态
const questionList = ref([]) // 题目列表

// ==================== 计算属性 ====================
// 用户总得分
const totalUserScore = computed(() => {
  return questionList.value.reduce((sum, q) => sum + (q.user_score || 0), 0) // 累加每题得分
})

// 试卷满分
const totalFullScore = computed(() => {
  return questionList.value.reduce((sum, q) => sum + (q.score || 0), 0) // 累加每题满分
})

// ==================== 监听 examId 变化 ====================
watch(
  () => props.examId, // 监听考试ID变化
  (newId) => {
    if (newId) {
      loadPaperDetail() // 重新加载试卷详情
    }
  },
  { immediate: true }, // 立即执行一次
)

// ==================== 方法定义 ====================
/**
 * 加载试卷详情
 * 调用 GET /api/score/my-paper/{paper_id}/ 接口
 */
async function loadPaperDetail() {
  loading.value = true // 开始加载
  try {
    const res = await getMyPaperDetail(props.examId) // 调用API获取试卷详情
    questionList.value = res.questions || [] // 设置题目列表
  } catch (error) {
    console.error('加载试卷详情失败', error) // 打印错误日志
    ElMessage.error('加载试卷详情失败') // 提示用户
  } finally {
    loading.value = false // 结束加载
  }
}

/**
 * 返回上一页
 * 触发 back 事件，由父组件处理返回逻辑
 */
function goBack() {
  emit('back') // 触发返回事件
}

/**
 * 获取题型文本
 */
function getTypeText(type) {
  const typeMap = {
    single: '单选题',
    multi: '多选题',
    multiple: '多选题',
    judge: '判断题',
    short: '简答题',
  }
  return typeMap[type] || type || '未知'
}

/**
 * 获取题型标签颜色
 */
function getTypeTag(type) {
  const tagMap = {
    single: 'primary',
    multi: 'success',
    multiple: 'success',
    judge: 'warning',
    short: 'danger',
  }
  return tagMap[type] || 'info'
}

/**
 * 格式化答案显示
 */
function formatAnswer(answer, type) {
  if (!answer && answer !== 0) return '-'
  if (Array.isArray(answer)) {
    return answer.join('、')
  }
  if (type === 'multi' || type === 'multiple') {
    const answers = normalizeAnswerList(answer)
    return answers.length > 0 ? answers.join('、') : '-'
  }
  if (type === 'judge') {
    const str = String(answer).toLowerCase()
    if (str === 'true' || str === '1') return '正确'
    if (str === 'false' || str === '0') return '错误'
  }
  return String(answer)
}

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
</script>

<style scoped>
/* ==================== 容器样式 ==================== */
.score-detail-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

/* ==================== 页面头部 ==================== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  flex-shrink: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-right {
  flex-shrink: 0;
}

.total-info {
  font-size: 14px;
  color: #606266;
}

.total-info strong {
  color: #303133;
}

.score-highlight {
  font-size: 18px;
  color: #409eff;
}

/* ==================== 加载状态 ==================== */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.loading-icon {
  font-size: 36px;
  animation: rotate 2s linear infinite;
  margin-bottom: 12px;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* ==================== 题目列表 ==================== */
.question-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-card {
  border-radius: 8px;
}

/* ==================== 题目头部 ==================== */
.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.question-num {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.question-header-right {
  flex-shrink: 0;
}

.question-score {
  font-weight: 600;
  font-size: 14px;
}

.score-correct {
  color: #67c23a;
}

.score-wrong {
  color: #f56c6c;
}

/* ==================== 题目内容 ==================== */
.question-body {
  margin-bottom: 16px;
}

.question-title {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  margin: 0;
}

/* ==================== 答案对比区域 ==================== */
.answer-compare {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 12px;
}

.answer-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.answer-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  flex-shrink: 0;
}

.answer-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.answer-right {
  color: #67c23a;
}

.answer-wrong {
  color: #f56c6c;
}

.answer-correct {
  color: #67c23a;
}

</style>
