<template>
  <div class="correct-do-page">
    <!-- 左侧导航区 -->
    <div class="left-section">
      <!-- 顶部考试信息 -->
      <div class="teacher-info">
        <h3>{{ isModify ? '修改分数' : '批改详情' }}</h3>
        <div class="info-item">
          <span class="label">答题ID：</span>
          <span class="value">{{ answerId }}</span>
        </div>
        <div class="info-item">
          <span class="label">考生姓名：</span>
          <span class="value">{{ examinerName }}</span>
        </div>
        <div class="info-item">
          <span class="label">当前总分：</span>
          <span class="value highlight">{{ currentTotalScore }}</span>
        </div>
      </div>
    </div>

    <!-- 右侧主批改区 -->
    <div class="right-section">
      <div class="main-content">
        <!-- 题目信息 -->
        <div class="content-block">
          <h4 class="block-title">题目信息</h4>
          <div class="question-content">
            <p>{{ questionTitle }}</p>
          </div>
        </div>

        <!-- 学生作答 -->
        <div class="content-block">
          <h4 class="block-title">学生作答</h4>
          <div class="student-answer">
            <p>{{ userAnswer || '（暂无作答内容）' }}</p>
          </div>
        </div>

        <!-- 学生信息表格（标准答案参考） -->
        <div class="content-block" v-if="standardAnswer">
          <h4 class="block-title">学生信息（标准答案参考）</h4>
          <div class="student-info-table">
            <table>
              <tr v-for="(row, rowIdx) in standardAnswerRows" :key="rowIdx">
                <td
                  v-for="(cell, cellIdx) in row"
                  :key="cellIdx"
                  :class="cellIdx % 2 === 0 ? 'label-cell' : 'value-cell'"
                >
                  {{ cell }}
                </td>
              </tr>
            </table>
          </div>
        </div>

        <!-- 分数与操作 -->
        <div class="content-block score-block">
          <!-- 打分输入区域 -->
          <div class="score-operation">
            <div class="score-input-group">
              <span class="label">给出分数：</span>
              <el-input-number
                v-model="score"
                :min="0"
                :max="maxScore"
                :step="1"
                size="small"
                class="score-input"
              />
              <span class="unit">分（满分{{ maxScore }}）</span>
            </div>
            <div class="remark-group">
              <span class="label">批注：</span>
              <el-input
                v-model="remark"
                type="textarea"
                :rows="2"
                placeholder="可选，输入批改评语"
                class="remark-input"
              />
            </div>
            <div class="action-buttons">
              <el-button type="primary" :loading="submitting" @click="handleSubmit">
                {{ submitting ? '提交中...' : isModify ? '修改分数' : '提交分数' }}
              </el-button>
              <el-button type="danger" @click="handleExit" :disabled="submitting">
                退出批改
              </el-button>
            </div>
          </div>

          <div v-if="submitMessage" class="save-message" :class="{ success: submitSuccess }">
            {{ submitMessage }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 批改详情页面
 * 对接后端 PUT /api/correct/score/{answer_id}/ 提交批改分数
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { submitScore } from '@/api/correct'

const router = useRouter()
const route = useRoute()

// ==================== 状态定义 ====================
const submitting = ref(false)
const submitMessage = ref('')
const submitSuccess = ref(false)
const isModify = ref(false) // 是否为修改已有分数模式

// 从路由参数获取基本信息
const answerId = ref('')
const examinerName = ref('')
const questionTitle = ref('')
const userAnswer = ref('')
const currentTotalScore = ref(0)
const examId = ref('')

// 学生信息（标准答案）
const standardAnswer = ref(null)

// 打分
const score = ref(0)
const remark = ref('')
const maxScore = ref(6) // 简答题默认6分满分

// 将 standardAnswer 对象转换为表格行
const standardAnswerRows = computed(() => {
  if (!standardAnswer.value) return []
  const entries = Object.entries(standardAnswer.value)
  const rows = []
  for (let i = 0; i < entries.length; i += 2) {
    const row = []
    row.push(entries[i][0]) // 字段名
    row.push(entries[i][1] || '') // 字段值
    if (i + 1 < entries.length) {
      row.push(entries[i + 1][0])
      row.push(entries[i + 1][1] || '')
    }
    rows.push(row)
  }
  return rows
})

// ==================== 方法定义 ====================
/**
 * 退出批改，返回列表并清除 sessionStorage 中的导航列表
 */
function handleExit() {
  sessionStorage.removeItem('correctNextList') // 清除导航列表，防止下次进入时自动跳转
  router.push('/admin/correct-list')
}

/**
 * 自动跳转到下一题（从 sessionStorage 中查找当前题目之后的第一个未批改题目）
 * @param {boolean} isModifyMode - 是否为修改分数模式，修改模式不跳转下一题
 */
function navigateToNext(isModifyMode) {
  // 修改分数模式：不跳转下一题，返回列表
  if (isModifyMode) {
    router.push('/admin/correct-list')
    return
  }
  try {
    const listStr = sessionStorage.getItem('correctNextList') // 从 sessionStorage 读取批改列表
    if (!listStr) {
      router.push('/admin/correct-list')
      return
    }
    const list = JSON.parse(listStr) // 解析列表JSON
    // 查找当前题目在列表中的位置
    const currentIndex = list.findIndex((item) => String(item.answer_id) === String(answerId.value))
    // 从当前题目之后查找下一个未批改的题目
    const nextItem = list
      .slice(currentIndex + 1)
      .find((item) => item.existing_score === null || item.existing_score === undefined)
    if (nextItem) {
      // 找到下一题，跳转到该题的批改详情页
      // 先清空批注和重置分数（因为 Vue Router 同一个组件复用不会触发 onMounted）
      score.value = 0
      remark.value = ''
      isModify.value = false
      router.push({
        path: '/admin/correct-do',
        query: {
          answerId: nextItem.answer_id,
          examId: examId.value,
          examinerName: nextItem.examiner_name || '',
          questionTitle: nextItem.question_title || '',
          userAnswer: nextItem.user_answer || '',
          currentTotalScore: nextItem.current_total_score || 0,
          standardAnswer: nextItem.standard_answer
            ? encodeURIComponent(JSON.stringify(nextItem.standard_answer))
            : '',
          existingScore: undefined,
          existingRemark: undefined,
        },
      })
    } else {
      // 没有更多待批改题目，返回列表
      ElMessage.success('该页所有题目已批改完成')
      router.push('/admin/correct-list')
    }
  } catch (e) {
    console.error('跳转下一题失败', e)
    router.push('/admin/correct-list')
  }
}

/**
 * 提交分数
 */
async function handleSubmit() {
  if (!answerId.value) {
    ElMessage.error('缺少答题ID')
    return
  }

  submitting.value = true
  submitMessage.value = ''
  try {
    await submitScore(answerId.value, {
      score: score.value,
      remark: remark.value,
    })

    submitSuccess.value = true
    submitMessage.value = '批改成功！'
    ElMessage.success('批改成功')

    // 延迟后自动跳转到下一题（修改模式返回列表，批改模式跳到下一个未批改题目）
    setTimeout(() => {
      navigateToNext(isModify.value)
    }, 800)
  } catch (error) {
    console.error('提交分数失败', error)
    submitSuccess.value = false
    submitMessage.value = '提交失败，请重试'
  } finally {
    submitting.value = false
  }
}

// ==================== 从路由参数加载数据 ====================
/**
 * 从路由 query 参数中读取并填充页面数据
 * 抽取为独立函数，供 onMounted 和 watch 复用
 */
function loadQueryParams() {
  // 从路由参数获取数据
  answerId.value = route.query.answerId || ''
  examId.value = route.query.examId || ''
  examinerName.value = route.query.examinerName || ''
  questionTitle.value = route.query.questionTitle || ''
  userAnswer.value = route.query.userAnswer || ''
  currentTotalScore.value = parseFloat(route.query.currentTotalScore) || 0

  // 解析标准答案JSON
  try {
    const saStr = route.query.standardAnswer
    if (saStr) {
      standardAnswer.value = JSON.parse(decodeURIComponent(saStr))
    } else {
      standardAnswer.value = null
    }
  } catch (e) {
    console.error('解析标准答案失败', e)
    standardAnswer.value = null
  }

  // 如果是修改已有分数，预填分数和批注
  const existingScore = route.query.existingScore
  if (existingScore !== undefined && existingScore !== '') {
    score.value = Number(existingScore) || 0
    remark.value = route.query.existingRemark || ''
    isModify.value = true
  } else {
    score.value = 0
    remark.value = ''
    isModify.value = false
  }
  // 清除提交状态消息
  submitMessage.value = ''
  submitSuccess.value = false
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadQueryParams()
})

// 监听 query 参数变化（同一组件复用时跳转下一题不会触发 onMounted）
watch(
  () => route.query.answerId,
  () => {
    loadQueryParams()
  },
)
</script>

<style scoped>
/**
 * 批改详情页面样式
 */
.correct-do-page {
  display: flex;
  min-height: 100vh;
  background: #e6f7ff;
}

/* ==================== 左侧导航区 ==================== */
.left-section {
  width: 280px;
  background: #fff;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.teacher-info {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 6px;
}

.teacher-info h3 {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
  border-bottom: 1px solid #e8e8e8;
  padding-bottom: 10px;
}

.info-item {
  margin-bottom: 8px;
  font-size: 13px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .label {
  color: #666;
}

.info-item .value {
  color: #333;
  font-weight: 500;
}

.info-item .value.highlight {
  color: #1890ff;
  font-size: 16px;
  font-weight: 600;
}

/* ==================== 右侧主批改区 ==================== */
.right-section {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.main-content {
  background: #fff;
  padding: 25px;
  border-radius: 8px;
}

.content-block {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.content-block:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.block-title {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.question-content p {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: #333;
}

.student-answer {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
  max-height: 400px; /* 设置最大高度 */
  overflow-y: auto; /* 垂直滚动 */
  overflow-x: hidden; /* 隐藏水平滚动 */
  word-wrap: break-word; /* 自动换行 */
  word-break: break-all; /* 强制换行 */
}

.student-answer p {
  margin: 0;
  font-size: 14px;
  line-height: 1.8; /* 增大行高便于阅读 */
  color: #333;
  white-space: pre-wrap; /* 保留换行符并自动换行 */
}

/* 学生信息表格 */
.student-info-table {
  background: #f5f7fa;
  border-radius: 6px;
  overflow: hidden;
  padding: 12px; /* 统一内边距 */
}

.student-info-table table {
  width: 100%;
  border-collapse: collapse;
}

.student-info-table tr {
  border-bottom: 1px dashed #e8e8e8; /* 虚线分隔更紧凑 */
}

.student-info-table tr:last-child {
  border-bottom: none;
}

.student-info-table td {
  padding: 6px 10px; /* 减少内边距 */
  font-size: 12px; /* 缩小字体 */
  line-height: 1.4; /* 缩小行高 */
  vertical-align: top;
}

.label-cell {
  background: transparent; /* 移除背景色更紧凑 */
  color: #888;
  width: 80px; /* 缩小标签宽度 */
  white-space: nowrap; /* 标签不换行 */
}

.value-cell {
  color: #333;
  width: 140px; /* 设置固定宽度，便于一行多列 */
}

/* 分数与操作 */
.score-block {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.score-operation {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.score-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-input-group .label {
  color: #666;
  font-size: 14px;
}

.score-input {
  width: 120px;
}

.unit {
  color: #999;
  font-size: 13px;
}

.remark-group {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.remark-group .label {
  color: #666;
  font-size: 14px;
  padding-top: 5px;
}

.remark-input {
  flex: 1;
  max-width: 400px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.save-message {
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 13px;
  background: #fffbe6;
  color: #faad14;
  border: 1px solid #ffe58f;
}

.save-message.success {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}
</style>
