<template>
  <div class="exam-check-page">
    <div class="page-header">
      <div class="header-left">
        <h1>试卷检查</h1>
        <p>试卷生成后、考试开考前，检查任意考生的试卷是否生成正确</p>
      </div>
      <div class="header-right">
        <el-button @click="handleBack" class="back-button">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
    </div>

    <div class="exam-select-section">
      <el-card class="select-card">
        <div class="select-header">
          <span class="select-label">选择考试：</span>
          <el-select
            v-model="selectedExamId"
            placeholder="请选择考试"
            class="exam-select"
            @change="handleExamChange"
          >
            <el-option
              v-for="exam in examList"
              :key="exam.exam_id"
              :label="exam.exam_name"
              :value="exam.exam_id"
            />
          </el-select>
          <div class="header-actions">
            <el-button type="success" @click="handleExportStudents" :disabled="!selectedExamId" class="export-btn">
              <el-icon :size="16"><Download /></el-icon>
              导出学生信息
            </el-button>
            <el-button type="primary" @click="loadExamList" class="refresh-btn">
              <el-icon :size="16"><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>

        <div v-if="selectedExam" class="exam-info">
          <div class="info-item">
            <span class="info-label">考试状态：</span>
            <el-tag :type="getExamStatusType(selectedExam.exam_status)">
              {{ getExamStatusText(selectedExam.exam_status) }}
            </el-tag>
          </div>
          <div class="info-item">
            <span class="info-label">考试时间：</span>
            <span>{{ selectedExam.start_time }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">考试时长：</span>
            <span>{{ selectedExam.duration }}分钟</span>
          </div>
          <div class="info-item">
            <span class="info-label">考生总数：</span>
            <span>{{ selectedExam.total_counselors }}人</span>
          </div>
          <div class="info-item">
            <span class="info-label">已交卷：</span>
            <span>{{ selectedExam.submitted_count }}人</span>
          </div>
          <div class="info-item">
            <span class="info-label">已批改：</span>
            <span>{{ selectedExam.graded_count }}人</span>
          </div>
        </div>
      </el-card>
    </div>

    <div v-if="selectedExamId" class="paper-list-section">
      <div class="section-header">
        <span>试卷列表</span>
        <span class="count">共 {{ paperList.length }} 份试卷</span>
      </div>

      <el-card class="paper-list-card">
        <el-table :data="paperList" border>
          <el-table-column prop="teacher_name" label="考生姓名" />
          <el-table-column prop="teacher_gh" label="工号" />
          <el-table-column prop="submit_time" label="交卷时间">
            <template #default="scope">
              <span>{{ scope.row.submit_time || '未交卷' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-tag :type="getEffectiveStatus(scope.row) === 'graded' ? 'success' : 'warning'">
                {{ getEffectiveStatus(scope.row) === 'graded' ? '已批改' : '未批改' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button size="small" type="primary" @click="viewPaper(scope.row)">
                查看试卷
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50]"
          :page-size="pageSize"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </el-card>
    </div>

    <div v-else class="empty-state">
      <el-icon :size="64" color="#ccc"><Document /></el-icon>
      <p>请先选择考试</p>
    </div>

    <el-dialog v-model="showPaperDialog" title="试卷详情" width="900px">
      <div v-if="selectedPaper" class="paper-content">
        <div class="paper-header">
          <h3>{{ selectedExam?.exam_name || '试卷详情' }}</h3>
          <p>考生：{{ selectedPaper.teacher_name }} ({{ selectedPaper.teacher_gh }})</p>
          <p v-if="selectedPaper.submit_time">交卷时间：{{ selectedPaper.submit_time }}</p>
        </div>

        <el-divider />

        <div class="question-list">
          <div
            v-for="(question, index) in selectedPaper.questions"
            :key="question.question_id"
            class="question-item"
          >
            <div class="question-title">
              <span class="question-num">题{{ index + 1 }}</span>
              <span class="question-type">({{ getQuestionTypeText(question.question_type) }})</span>
              <!-- 正确答案标签 -->
              <el-tag
                v-if="question.correct_answer"
                type="success"
                size="small"
                class="correct-tag"
              >
                正确答案：{{ formatCorrectAnswer(question) }}
              </el-tag>
            </div>
            <div class="question-content">{{ question.title }}</div>

            <!-- 选择题/判断题选项区：正确答案标绿 -->
            <div class="options-section" v-if="question.options">
              <div
                class="option-item"
                v-for="(opt, optKey) in question.options"
                :key="optKey"
                :class="{
                  'correct-option': isCorrectOption(question, optKey),
                  'option-item-image': isImagePath(opt),
                }"
              >
                <span class="option-key">{{ optKey }}:</span>
                <!-- 图片选项：显示实际图片 -->
                <img
                  v-if="isImagePath(opt)"
                  :src="getImageUrl(opt, question.question_id, optKey)"
                  class="option-image"
                  :alt="'选项' + optKey + '图片'"
                />
                <!-- 文本选项：直接显示文字 -->
                <span v-else class="option-value">{{ opt }}</span>
                <el-icon v-if="isCorrectOption(question, optKey)" class="correct-icon" :size="18">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                  </svg>
                </el-icon>
              </div>
            </div>

            <!-- 问答题正确答案区域 -->
            <div
              v-if="question.question_type === 'essay' && question.correct_answer"
              class="correct-answer-section"
            >
              <div class="correct-answer-title">正确答案：</div>
              <div class="correct-answer-content">
                <template v-if="typeof question.correct_answer === 'object'">
                  <div v-for="(val, key) in question.correct_answer" :key="key" class="answer-row">
                    <span class="answer-label">{{ key }}：</span>
                    <span class="answer-value">{{ val || '无' }}</span>
                  </div>
                </template>
                <template v-else>
                  {{ question.correct_answer }}
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPaperDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Refresh, Document, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getExamList } from '@/api/system'
import { getPaperReview, getExamUserStatus, exportExamStudents } from '@/api/exam'
import { useExamStore } from '@/stores/exam'

const router = useRouter()
const examStore = useExamStore()

const examList = ref([])
const selectedExamId = ref('')
const selectedExam = computed(() => examList.value.find((e) => e.exam_id === selectedExamId.value))

const paperList = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showPaperDialog = ref(false)
const selectedPaper = ref(null)

async function loadExamList() {
  try {
    const res = await getExamList({ page: 1, size: 50 })
    console.log('考试列表接口返回:', res)

    if (res && res.list) {
      examList.value = res.list
      if (examList.value.length > 0 && !selectedExamId.value) {
        selectedExamId.value = examList.value[0].exam_id
      }
    } else {
      ElMessage.warning('暂无考试数据')
    }
  } catch (error) {
    console.error('获取考试列表失败详情:', error)
    ElMessage.error('获取考试列表失败：' + (error.message || '请检查后端服务或登录状态'))
  }
}

async function handleExportStudents() {
  if (!selectedExamId.value) {
    ElMessage.warning('请先选择考试')
    return
  }
  try {
    const blob = await exportExamStudents(selectedExamId.value)
    // blob 下载
    const link = document.createElement('a')
    const url = window.URL.createObjectURL(blob)
    link.href = url
    const examName = selectedExam.value?.exam_name || selectedExamId.value
    link.download = `${examName}_学生信息.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出学生信息失败:', error)
    // Blob 错误处理：如果后端返回了 JSON 错误而非 Excel
    if (error.response?.data instanceof Blob) {
      const reader = new FileReader()
      reader.onload = () => {
        try {
          const errData = JSON.parse(reader.result)
          ElMessage.error(errData.msg || '导出失败')
        } catch {
          ElMessage.error('导出失败，请重试')
        }
      }
      reader.readAsText(error.response.data)
    } else {
      ElMessage.error(error.message || '导出失败，请重试')
    }
  }
}

async function handleExamChange() {
  paperList.value = []
  currentPage.value = 1
  total.value = 0
  if (selectedExamId.value) {
    await loadPaperList()
  }
}

async function loadPaperList() {
  try {
    const res = await getExamUserStatus(selectedExamId.value, {
      page: currentPage.value,
      size: pageSize.value,
    })
    console.log('试卷列表接口返回:', res)

    if (res && res.list) {
      paperList.value = res.list
      total.value = res.total || 0
    } else {
      paperList.value = []
      total.value = 0
      ElMessage.warning('暂无试卷数据')
    }
  } catch (error) {
    console.error('获取试卷列表失败:', error)
    ElMessage.error('获取试卷列表失败')
  }
}

async function viewPaper(row) {
  try {
    // 调用试卷检查接口，请求拦截器已扁平化返回数据（res.data 展开到顶层）
    const res = await getPaperReview(row.paper_id)
    console.log('试卷详情接口返回:', res)
    if (res.code === 200) {
      // 兼容 by_student 模式：question_groups 扁平化为 questions 数组
      let flatQuestions = []
      if (res.question_groups && res.question_groups.length > 0) {
        flatQuestions = res.question_groups.flatMap(function (group) {
          return group.questions || []
        })
      } else {
        flatQuestions = res.questions || []
      }
      // 请求拦截器已将 { code, msg, data: {...} } 展开为 { code, msg, paper_id, teacher_name, questions, ... }
      // 直接展开 res 即可获取 questions 和 correct_answer
      selectedPaper.value = {
        ...row,
        ...res,
        questions: flatQuestions,
      }

      // 预加载试卷中的图片，将 base64 解码后缓存为 Blob URL
      // 复用考生考试相同的预加载机制，确保学生照片能正常显示
      const paperId = res.paper_id || row.paper_id
      if (paperId) {
        await examStore.preloadExamImages(paperId)
      }
    } else {
      ElMessage.error(res.msg || '获取试卷详情失败')
      selectedPaper.value = row
    }
  } catch (error) {
    console.error('获取试卷详情失败:', error)
    ElMessage.error('获取试卷详情失败')
    selectedPaper.value = row
  }
  showPaperDialog.value = true
}

function handleSizeChange(val) {
  pageSize.value = val
  loadPaperList()
}

function handleCurrentChange(val) {
  currentPage.value = val
  loadPaperList()
}

function getExamStatusType(status) {
  const typeMap = {
    not_started: 'warning',
    normal: 'success',
    ended: 'info',
    closed: 'danger',
  }
  return typeMap[status] || 'info'
}

function getExamStatusText(status) {
  const textMap = {
    not_started: '未发布',
    normal: '进行中',
    ended: '已结束',
    closed: '已关闭',
  }
  return textMap[status] || status
}

/**
 * 获取考生的有效状态
 * 如果 score 字段有值（数字），说明已批改，即使 status 不是 'graded' 也按已批改处理
 */
function getEffectiveStatus(row) {
  if (row.score !== null && row.score !== undefined && row.score !== '') {
    return 'graded'
  }
  return row.status
}

function getQuestionTypeText(type) {
  const typeMap = {
    single: '单选题',
    multi: '多选题',
    multiple: '多选题',
    judge: '判断题',
    blank: '填空题',
    essay: '问答题',
  }
  return typeMap[type] || type
}

// ==================== 图片路径判断与URL解析 ====================

/**
 * 判断选项文本是否为图片路径
 * 根据文件扩展名判断是否为图片文件
 * @param {string} text - 选项文本
 * @returns {boolean} 是否为图片路径
 */
function isImagePath(text) {
  if (!text || typeof text !== 'string') return false // 空值或非字符串，不是图片路径
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'] // 常见图片扩展名
  const lowerText = text.toLowerCase() // 转为小写比较
  return imageExtensions.some((ext) => lowerText.endsWith(ext)) // 匹配任意图片扩展名
}

/**
 * 获取图片的URL
 * 优先使用预加载缓存的 Blob URL，未缓存时拼接后端 URL 兜底
 * @param {string} path - 图片路径（可能携带 media/ 前缀）
 * @param {string|number} questionId - 题目ID，用于查找缓存
 * @param {string} optionKey - 选项键（A/B/C/D），用于查找缓存
 * @returns {string} 完整的图片URL
 */
function getImageUrl(path, questionId, optionKey) {
  if (!path) return '' // 空路径
  // 优先使用预加载缓存的 Blob URL
  if (questionId && optionKey) {
    const cachedUrl = examStore.getCachedImage(questionId, optionKey)
    if (cachedUrl) {
      return cachedUrl
    }
  }
  // 未缓存时拼接后端媒体文件 URL 兜底
  let cleanPath = path.replace(/^\/?media\//, '') // 去除开头的 media/ 或 /media/
  return `/media/${cleanPath}` // 拼接为 /media/ 路径，由 Vite 代理转发到后端
}

// ==================== 判断选项是否为正确答案 ====================
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

function isCorrectOption(question, optKey) {
  if (!question.correct_answer) return false // 无正确答案数据
  const answer = question.correct_answer
  if (question.question_type === 'multi' || question.question_type === 'multiple') {
    return normalizeAnswerList(answer).includes(String(optKey))
  }
  // 单选/判断题：直接匹配
  return String(answer) === String(optKey)
}

// ==================== 格式化显示正确答案 ====================
function formatCorrectAnswer(question) {
  const answer = question.correct_answer
  if (!answer) return ''
  if (question.question_type === 'essay') {
    // 问答题：显示"见下方详情"
    return '见下方详情'
  }
  if (Array.isArray(answer)) {
    // 数组格式拼接
    return answer.join('、')
  }
  if (question.question_type === 'multi' || question.question_type === 'multiple') {
    return normalizeAnswerList(answer).join('、')
  }
  return String(answer)
}

function handleBack() {
  router.push('/super-admin/home')
}

loadExamList()
</script>

<style scoped>
.exam-check-page {
  padding: 20px;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #333;
}

.header-left p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 4px;
}

.exam-select-section {
  margin-bottom: 20px;
}

.select-card {
  background: #fff;
}

.select-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.select-label {
  font-weight: 600;
  color: #333;
}

.exam-select {
  width: 300px;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.exam-info {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.info-label {
  color: #999;
}

.paper-list-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.section-header .count {
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.paper-list-card {
  margin-top: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #999;
}

.empty-state p {
  margin-top: 16px;
  font-size: 16px;
}

.paper-content {
  max-height: 600px;
  overflow-y: auto;
}

.paper-header {
  margin-bottom: 16px;
}

.paper-header h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #333;
}

.paper-header p {
  margin: 4px 0;
  color: #666;
  font-size: 14px;
}

.question-list {
  margin-top: 16px;
}

.question-item {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9ff;
  border-radius: 8px;
  border: 1px solid #e8e8ff;
}

.question-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
}

.question-num {
  color: #667eea;
  font-size: 16px;
}

.question-type {
  color: #999;
  font-size: 14px;
  font-weight: normal;
}

.question-content {
  color: #333;
  line-height: 1.6;
  margin-bottom: 16px;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
}

.options-section {
  padding: 12px;
  background: #fff;
  border-radius: 6px;
}

.option-item {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  line-height: 1.6;
}

.option-item-image {
  flex-wrap: wrap; /* 图片选项允许换行 */
}

.option-item:last-child {
  margin-bottom: 0;
}

.option-key {
  color: #667eea;
  font-weight: 600;
  min-width: 20px;
}

.option-value {
  color: #333;
}

/* ==================== 选项图片样式 ==================== */
.option-image {
  max-width: 300px; /* 限制图片最大宽度 */
  max-height: 200px; /* 限制图片最大高度 */
  object-fit: contain; /* 保持图片比例 */
  border-radius: 4px; /* 圆角 */
  border: 1px solid #e0e0e0; /* 边框 */
  cursor: pointer; /* 鼠标悬停变手型 */
  transition: transform 0.2s; /* 悬停过渡动画 */
}

.option-image:hover {
  transform: scale(1.05); /* 悬停时轻微放大 */
}

/* ==================== 正确答案标绿样式 ==================== */
.correct-option {
  background: #f0f9eb; /* 浅绿色背景 */
  border: 2px solid #67c23a; /* 绿色边框 */
  border-radius: 4px; /* 圆角 */
  padding: 4px 8px; /* 内边距 */
  margin-bottom: 6px; /* 底部间距 */
}

.correct-option .option-key {
  color: #67c23a; /* 绿色选项字母 */
}

.correct-option .option-value {
  color: #529b2e; /* 深绿色文字 */
}

.correct-icon {
  color: #67c23a; /* 绿色勾号 */
  margin-left: auto; /* 靠右对齐 */
  flex-shrink: 0; /* 不收缩 */
}

.correct-tag {
  margin-left: 8px; /* 与题目类型间距 */
}

/* ==================== 问答题正确答案区域 ==================== */
.correct-answer-section {
  margin-top: 12px; /* 顶部间距 */
  padding: 12px; /* 内边距 */
  background: #f0f9eb; /* 浅绿色背景 */
  border: 1px solid #b3e19d; /* 淡绿色边框 */
  border-radius: 6px; /* 圆角 */
}

.correct-answer-title {
  font-weight: 600; /* 加粗 */
  color: #67c23a; /* 绿色标题 */
  margin-bottom: 8px; /* 底部间距 */
  font-size: 14px; /* 字号 */
}

.correct-answer-content {
  color: #333; /* 文字颜色 */
  line-height: 1.8; /* 行高 */
}

.answer-row {
  display: flex; /* flex 布局 */
  gap: 4px; /* 间距 */
  padding: 2px 0; /* 上下内边距 */
}

.answer-label {
  color: #67c23a; /* 绿色标签 */
  font-weight: 500; /* 中等粗细 */
  min-width: 80px; /* 最小宽度 */
  flex-shrink: 0; /* 不收缩 */
}

.answer-value {
  color: #303133; /* 深色值文字 */
}

:deep(.el-table) {
  margin-top: 16px;
}
</style>
