<template>
  <div class="practice-container">
    <!-- ==================== 页面标题 ==================== -->
    <div class="page-header">
      <h2 class="page-title">日常练习</h2>
      <div v-if="!sessionId" class="header-actions">
        <el-button type="danger" @click="handleExitPractice">退出练习</el-button>
      </div>
    </div>

    <!-- ==================== 学生信息卡片 ==================== -->
    <div v-if="sessionId" class="student-card">
      <div class="student-info">
        <span class="student-label">当前学生：</span>
        <span class="student-name">{{ studentName }}</span>
        <span class="student-id">（学号：{{ studentXid }}）</span>
      </div>
      <div class="student-progress">
        <span class="progress-label">练习进度：</span>
        <el-progress
          :percentage="Math.round(practiceProgress * 100)"
          :stroke-width="6"
          style="width: 200px"
        />
      </div>
      <el-button type="text" @click="handleSwitchStudent">切换学生</el-button>
    </div>

    <!-- ==================== 收藏夹按钮（右下角） ==================== -->
    <div class="collection-button-wrapper">
      <el-button
        type="primary"
        round
        size="small"
        icon="Collection"
        @click="goToCollection"
        class="collection-btn"
      >
        收藏夹
      </el-button>
    </div>

    <!-- ==================== 练习内容区域 ==================== -->
    <div v-if="currentQuestion" class="practice-content">
      <!-- 进度条 -->
      <div class="progress-bar">
        <el-progress :percentage="progressPercent" :stroke-width="8" />
        <span class="progress-text">第 {{ currentIndex + 1 }} / {{ totalCount }} 题</span>
      </div>

      <!-- 题目卡片 -->
      <PracticeCard
        ref="practiceCardRef"
        :question="currentQuestion"
        :question-number="currentIndex + 1"
        :is-collected="isCurrentCollected"
        :correct-answer="correctAnswer"
        @submit="handleSubmitAnswer"
        @next="handleNextQuestion"
        @collect="handleCollect"
        @uncollect="handleUncollect"
      />

      <!-- 答题结果提示 -->
      <div
        v-if="submitResult !== null"
        class="result-tip"
        :class="submitResult.isCorrect ? 'correct' : 'incorrect'"
      >
        <el-icon v-if="submitResult.isCorrect"><Check /></el-icon>
        <el-icon v-else><Close /></el-icon>
        <span>{{
          submitResult.isCorrect
            ? '回答正确！'
            : `回答错误，正确答案是 ${formatAnswer(submitResult.correctAnswer, currentQuestion?.type)}`
        }}</span>
      </div>
    </div>

    <!-- ==================== 开始练习提示 ==================== -->
    <div v-else class="start-prompt">
      <el-empty description="点击下方按钮开始练习" />
      <el-button type="primary" size="large" @click="handleStartPractice">开始随机练习</el-button>
      <p class="prompt-tip">系统将随机选取一名学生，基于题库模板生成一组题目供您练习</p>
      <p class="prompt-tip">若有未完成的练习，系统将自动恢复</p>
    </div>

    <!-- ==================== 底部操作栏 ==================== -->
    <div v-if="currentQuestion" class="bottom-actions">
      <el-button @click="handleFinishPractice">结束练习</el-button>
      <div class="action-stats">
        <span>正确：{{ correctCount }}</span>
        <span>错误：{{ incorrectCount }}</span>
        <span>正确率：{{ correctRate }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 日常练习页面逻辑
 * 处理开始练习、答题、收藏等功能
 * 接口遵循 V1.5 接口文档规范
 */
import { ref, computed, nextTick } from 'vue' // 引入Vue响应式API
import { useRouter } from 'vue-router' // 引入Vue Router
import { ElMessage } from 'element-plus' // 引入Element Plus消息组件
import { Check, Close } from '@element-plus/icons-vue' // 引入Element Plus图标
import PracticeCard from '@/components/PracticeCard.vue' // 引入练习题目卡片组件
import {
  startPractice,
  submitPracticeAnswer,
  nextQuestionGroup,
  addCollection,
  removeCollection,
} from '@/api/practice' // 引入练习相关API

// 获取路由实例
const router = useRouter()

// ==================== 状态定义 ====================
const sessionId = ref('') // 练习会话ID
const studentXid = ref(null) // 学生学号
const studentName = ref('') // 学生姓名
const practiceProgress = ref(0) // 练习进度
const questions = ref([]) // 题目列表
const currentIndex = ref(0) // 当前题目索引
const currentQuestion = ref(null) // 当前题目
const practiceCardRef = ref(null) // 题目卡片引用
// 已收藏的题目 Map：key 为 questionId，value 为 favorite_id
const collectedIds = ref(new Map())
const submitResult = ref(null) // 答题结果（包含isCorrect和correctAnswer）
const submitResults = ref([]) // 所有答题结果记录
const isLoading = ref(false) // 加载状态
const correctAnswer = ref('') // 当前题目正确答案（从提交答案接口获取）

// ==================== 从 localStorage 恢复收藏状态 ====================
const savedCollected = localStorage.getItem('practice_collected')
if (savedCollected) {
  try {
    const parsed = JSON.parse(savedCollected)
    collectedIds.value = new Map(parsed)
  } catch (e) {
    collectedIds.value = new Map()
  }
}

// ==================== 计算属性 ====================
const totalCount = computed(() => questions.value.length) // 总题目数
const progressPercent = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round(((currentIndex.value + 1) / totalCount.value) * 100)
}) // 答题进度百分比
const correctCount = computed(() => {
  // 统计正确数量
  return submitResults.value.filter((r) => r && r.isCorrect).length
}) // 正确数量
const incorrectCount = computed(() => {
  return submitResults.value.length - correctCount.value
}) // 错误数量
const correctRate = computed(() => {
  if (submitResults.value.length === 0) return 0
  return Math.round((correctCount.value / submitResults.value.length) * 100)
}) // 正确率
const isCurrentCollected = computed(() => {
  return currentQuestion.value ? collectedIds.value.has(currentQuestion.value.question_id) : false
}) // 当前题目是否已收藏

// ==================== 方法定义 ====================
/**
 * 开始练习/恢复练习
 */
async function handleStartPractice() {
  isLoading.value = true
  try {
    const res = await startPractice()
    const data = res.data || res

    // 保存会话信息
    sessionId.value = data.session_id
    studentXid.value = data.student_xid
    studentName.value = data.student_name
    practiceProgress.value = data.progress || 0

    // 转换题目数据格式（适配组件使用）
    questions.value = (data.questions || []).map((q) => {
      console.log('题目原始数据:', q)
      const convertedType =
        q.question_type === 'single'
          ? 'single'
          : q.question_type === 'multi'
            ? 'multiple'
            : q.question_type === 'judge'
              ? 'judge'
              : 'short'

      const convertedQuestion = {
        question_id: q.question_id,
        template_id: q.template_id,
        id: q.question_id,
        type: convertedType,
        content: q.title || '无题目内容',
        options: convertOptions(q.options, q.question_type),
        answer: (() => {
          if (q.question_type === 'multi') {
            return normalizeMultiAnswer(q.correct_answer)
          } else if (q.question_type === 'judge') {
            // 判断题答案转换：true/'true' -> 'A'（正确），false/'false' -> 'B'（错误）
            return q.correct_answer === true || q.correct_answer === 'true' ? 'A' : 'B'
          }
          return q.correct_answer
        })(),
        score: 1,
      }

      console.log('转换后题目:', convertedQuestion)
      return convertedQuestion
    })

    currentIndex.value = 0
    submitResults.value = []
    submitResult.value = null
    correctAnswer.value = ''
    collectedIds.value.clear() // 清空收藏状态（开始新的练习）
    localStorage.removeItem('practice_collected') // 清除本地收藏缓存

    if (questions.value.length > 0) {
      // 使用 nextTick 确保 DOM 完全更新后再切换条件渲染
      await nextTick()
      currentQuestion.value = questions.value[0]
    }
  } catch (error) {
    console.error('获取练习题目失败', error)
    ElMessage.error('获取练习题目失败')
  } finally {
    isLoading.value = false
  }
}

/**
 * 转换选项格式（将对象格式转换为数组格式）
 * @param {Object} options - 接口返回的选项对象
 * @param {string} questionType - 题目类型
 * @returns {Array} 转换后的选项数组
 */
function convertOptions(options, questionType) {
  if (!options) return []

  // 判断题选项特殊处理
  if (questionType === 'judge') {
    // 根据后端返回的选项值来确定正确/错误对应的选项
    const result = []
    if (options.A !== undefined) {
      result.push({ key: 'A', value: String(options.A) })
    } else {
      result.push({ key: 'A', value: '正确' })
    }
    if (options.B !== undefined) {
      result.push({ key: 'B', value: String(options.B) })
    } else {
      result.push({ key: 'B', value: '错误' })
    }
    return result
  }

  // 其他题型转换为数组格式
  return Object.keys(options).map((key) => ({
    key: key,
    value: options[key],
  }))
}

function normalizeMultiAnswer(answer) {
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

function formatAnswer(answer, questionType) {
  if (questionType !== 'multiple') {
    return answer || '暂无答案'
  }
  const answers = normalizeMultiAnswer(answer)
  return answers.length > 0 ? answers.join('、') : '暂无答案'
}

/**
 * 提交答案
 * @param {Object} data - 答题数据
 */
async function handleSubmitAnswer(data) {
  try {
    console.log('=== 提交答案 ===')
    console.log('session_id:', sessionId.value)
    console.log('question_id:', data.questionId, '类型:', typeof data.questionId)
    console.log('user_answer:', data.answer, '类型:', typeof data.answer)

    const res = await submitPracticeAnswer({
      session_id: sessionId.value,
      question_id: Number(data.questionId),
      user_answer: data.answer,
    })

    const resultData = res.data || res
    submitResult.value = {
      isCorrect: resultData.is_correct,
      correctAnswer: resultData.correct_answer,
    }
    // 更新当前题目正确答案，用于组件显示
    correctAnswer.value = resultData.correct_answer
    submitResults.value.push(submitResult.value)
  } catch (error) {
    console.error('提交答案失败', error)
    ElMessage.error('提交答案失败')
  }
}

/**
 * 下一题
 */
function handleNextQuestion() {
  console.log('=== 切换下一题 ===')
  console.log('当前索引:', currentIndex.value, '总题数:', questions.value.length)
  console.log('questions 数组:', questions.value)

  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    currentQuestion.value = questions.value[currentIndex.value]

    console.log('新索引:', currentIndex.value)
    console.log('新题目:', currentQuestion.value)
    console.log('新题目类型:', currentQuestion.value?.type)
    console.log('新题目内容:', currentQuestion.value?.content)
    console.log('currentQuestion 响应式:', currentQuestion.value)

    submitResult.value = null
    correctAnswer.value = '' // 重置正确答案
    practiceCardRef.value?.reset()
  } else {
    ElMessage.success('恭喜您完成了所有题目！')
  }
}

/**
 * 切换学生（下一组题目）
 */
async function handleSwitchStudent() {
  if (!sessionId.value) {
    ElMessage.warning('请先开始练习')
    return
  }

  try {
    isLoading.value = true
    const res = await nextQuestionGroup(sessionId.value)
    const data = res.data || res

    // 更新会话信息
    sessionId.value = data.session_id
    studentXid.value = data.student_xid
    studentName.value = data.student_name
    practiceProgress.value = data.progress || 0

    // 转换题目数据格式
    questions.value = (data.questions || []).map((q) => ({
      question_id: q.question_id,
      template_id: q.template_id,
      id: q.question_id,
      type:
        q.question_type === 'single'
          ? 'single'
          : q.question_type === 'multi'
            ? 'multiple'
            : q.question_type === 'judge'
              ? 'judge'
              : 'short',
      content: q.title || '无题目内容',
      options: convertOptions(q.options, q.question_type),
      answer: (() => {
        if (q.question_type === 'multi') {
          return normalizeMultiAnswer(q.correct_answer)
        } else if (q.question_type === 'judge') {
          return q.correct_answer === true || q.correct_answer === 'true' ? 'A' : 'B'
        }
        return q.correct_answer
      })(),
      score: 1,
    }))

    currentIndex.value = 0
    submitResults.value = []
    submitResult.value = null
    correctAnswer.value = ''
    collectedIds.value.clear() // 清空收藏状态（切换学生开始新的练习）
    localStorage.removeItem('practice_collected') // 清除本地收藏缓存
    practiceCardRef.value?.reset() // 重置答题卡片状态（清空选项判断颜色）

    if (questions.value.length > 0) {
      currentQuestion.value = questions.value[0]
    }

    ElMessage.success(`已切换到学生：${data.student_name}`)
  } catch (error) {
    console.error('切换学生失败', error)
    ElMessage.error('切换学生失败')
  } finally {
    isLoading.value = false
  }
}

/**
 * 收藏题目
 */
async function handleCollect(questionId) {
  try {
    const res = await addCollection({
      session_id: sessionId.value,
      question_id: questionId,
    })
    const favoriteId = res.data?.favorite_id || res.favorite_id
    if (favoriteId) {
      collectedIds.value.set(questionId, favoriteId)
      saveCollectedToStorage()
      ElMessage.success('收藏成功')
    } else {
      ElMessage.error('收藏失败：未获取到收藏ID')
    }
  } catch (error) {
    console.error('收藏失败', error)
    ElMessage.error('收藏失败')
  }
}

/**
 * 取消收藏
 */
async function handleUncollect(questionId) {
  try {
    const favoriteId = collectedIds.value.get(questionId)
    if (!favoriteId) {
      ElMessage.error('取消收藏失败：未找到收藏记录')
      return
    }
    await removeCollection(favoriteId)
    collectedIds.value.delete(questionId)
    saveCollectedToStorage()
    ElMessage.success('已取消收藏')
  } catch (error) {
    console.error('取消收藏失败', error)
    ElMessage.error('取消收藏失败')
  }
}

/**
 * 保存收藏状态到 localStorage
 */
function saveCollectedToStorage() {
  const arr = Array.from(collectedIds.value.entries())
  localStorage.setItem('practice_collected', JSON.stringify(arr))
}

/**
 * 结束练习
 */
function handleFinishPractice() {
  sessionId.value = ''
  studentXid.value = null
  studentName.value = ''
  practiceProgress.value = 0
  currentQuestion.value = null
  questions.value = []
  currentIndex.value = 0
  submitResults.value = []
  submitResult.value = null
  correctAnswer.value = ''
  // 不清空 collectedIds，保留收藏状态
}

/**
 * 退出练习（返回考试列表）
 */
function handleExitPractice() {
  router.push('/exam-status')
}

/**
 * 跳转到收藏夹页面
 */
function goToCollection() {
  router.push('/collection')
}
</script>

<style scoped>
/**
 * 练习页面样式
 */
.practice-container {
  max-width: 800px; /* 最大宽度800px */
  margin: 0 auto; /* 居中对齐 */
  padding: 20px; /* 内边距20px */
}

/* ==================== 页面标题样式 ==================== */
.page-header {
  display: flex; /* 弹性布局 */
  justify-content: space-between; /* 左右分散对齐 */
  align-items: center; /* 垂直居中对齐 */
  margin-bottom: 30px; /* 底部外边距30px */
}

.page-title {
  font-size: 24px; /* 标题字号24px */
  font-weight: 600; /* 粗体 */
  color: #303133; /* 深灰色 */
  margin: 0; /* 清除默认外边距 */
}

/* ==================== 学生信息卡片样式 ==================== */
.student-card {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 20px; /* 间距20px */
  padding: 16px 20px; /* 内边距 */
  background-color: #fff; /* 白色背景 */
  border-radius: 8px; /* 圆角8px */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); /* 阴影效果 */
  margin-bottom: 20px; /* 底部外边距20px */
}

.student-info {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 8px; /* 间距8px */
}

.student-label {
  font-size: 14px; /* 字号14px */
  color: #606266; /* 中灰色 */
}

.student-name {
  font-size: 16px; /* 字号16px */
  font-weight: 600; /* 粗体 */
  color: #303133; /* 深灰色 */
}

.student-id {
  font-size: 14px; /* 字号14px */
  color: #909399; /* 浅灰色 */
}

.student-progress {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 10px; /* 间距10px */
  margin-left: auto; /* 左侧外边距自动 */
}

.progress-label {
  font-size: 14px; /* 字号14px */
  color: #606266; /* 中灰色 */
}

/* ==================== 练习内容样式 ==================== */
.practice-content {
  background-color: #fff; /* 白色背景 */
  border-radius: 12px; /* 圆角12px */
  padding: 30px; /* 内边距30px */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1); /* 阴影效果 */
}

/* ==================== 进度条样式 ==================== */
.progress-bar {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 16px; /* 间距16px */
  margin-bottom: 24px; /* 底部外边距24px */
}

.progress-bar .el-progress {
  flex: 1; /* 占据剩余空间 */
}

.progress-text {
  font-size: 14px; /* 字号14px */
  color: #606266; /* 中灰色 */
  white-space: nowrap; /* 不换行 */
}

/* ==================== 结果提示样式 ==================== */
.result-tip {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 8px; /* 间距8px */
  padding: 12px 16px; /* 内边距 */
  border-radius: 6px; /* 圆角6px */
  margin-top: 16px; /* 顶部外边距16px */
  font-size: 14px; /* 字号14px */
}

.result-tip.correct {
  background-color: #f0f9eb; /* 浅绿背景 */
  color: #67c23a; /* 绿色 */
}

.result-tip.incorrect {
  background-color: #fef0f0; /* 浅红背景 */
  color: #f56c6c; /* 红色 */
}

/* ==================== 开始提示样式 ==================== */
.start-prompt {
  text-align: center; /* 居中对齐 */
  padding: 60px 20px; /* 内边距 */
  background-color: #fff; /* 白色背景 */
  border-radius: 12px; /* 圆角12px */
}

.prompt-tip {
  margin-top: 16px; /* 顶部外边距16px */
  color: #909399; /* 灰色 */
  font-size: 14px; /* 字号14px */
}

/* ==================== 底部操作栏样式 ==================== */
.bottom-actions {
  display: flex; /* 弹性布局 */
  justify-content: space-between; /* 左右分散对齐 */
  align-items: center; /* 垂直居中对齐 */
  margin-top: 20px; /* 顶部外边距20px */
  padding: 16px 20px; /* 内边距 */
  background-color: #fff; /* 白色背景 */
  border-radius: 12px; /* 圆角12px */
}

.action-stats {
  display: flex; /* 弹性布局 */
  gap: 20px; /* 间距20px */
  font-size: 14px; /* 字号14px */
  color: #606266; /* 中灰色 */
}

/* ==================== 收藏夹按钮样式 ==================== */
.collection-button-wrapper {
  position: fixed; /* 固定定位 */
  right: 30px; /* 距离右侧30px */
  bottom: 30px; /* 距离底部30px */
  z-index: 999; /* 确保在最上层 */
}

.collection-btn {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3); /* 阴影效果 */
  padding: 10px 24px; /* 内边距：上下10px，左右24px（约两个汉字宽度） */
  font-size: 14px; /* 字号14px */
}
</style>
