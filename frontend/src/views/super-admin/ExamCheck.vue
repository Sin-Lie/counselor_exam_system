<template>
  <div class="exam-check-page">
    <div class="page-header">
      <div class="header-left">
        <h1>试卷检查</h1>
        <p>查看考生试卷，并在开考前修改需要纠正的题目</p>
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
            <el-button type="primary" @click="loadExamList" :loading="loadingExams" class="refresh-btn">
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
        <el-table v-loading="loadingPapers" :data="paperList" border>
          <el-table-column prop="teacher_name" label="考生姓名" />
          <el-table-column prop="teacher_gh" label="工号" />
          <el-table-column prop="submit_time" label="交卷时间">
            <template #default="scope">
              <span>{{ scope.row.submit_time || '未交卷' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-tag :type="paperStatuses[scope.row.status]?.type || 'info'">
                {{ paperStatuses[scope.row.status]?.text || '未知' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button
                size="small"
                type="primary"
                :loading="openingPaperId === scope.row.paper_id"
                :disabled="openingPaperId !== null"
                @click="viewPaper(scope.row)"
              >
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

    <el-dialog
      v-model="showPaperDialog"
      title="试卷详情"
      width="min(900px, 96vw)"
      :close-on-click-modal="false"
      :close-on-press-escape="!savingQuestion"
      :show-close="!savingQuestion"
      @closed="editDraft = null"
    >
      <div v-if="selectedPaper" class="paper-content">
        <div class="paper-header">
          <h3>{{ selectedExam?.exam_name || '试卷详情' }}</h3>
          <p>考生：{{ selectedPaper.teacher_name }} ({{ selectedPaper.teacher_gh }})</p>
          <p v-if="selectedPaper.submit_time">交卷时间：{{ selectedPaper.submit_time }}</p>
          <p>{{ selectedPaper.can_edit ? '开考前可逐题修改，保存后仅影响该考生。' : '当前试卷仅供查看。' }}</p>
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
              <span class="question-type">{{ question.score }} 分</span>
              <el-button
                v-if="selectedPaper.can_edit"
                class="edit-question-button"
                size="small"
                type="primary"
                plain
                :disabled="editDraft !== null"
                @click="beginQuestionEdit(question)"
              >
                编辑第 {{ index + 1 }} 题
              </el-button>
              <!-- 正确答案标签 -->
              <el-tag
                v-if="question.correct_answer && question.question_type !== 'essay'"
                type="success"
                size="small"
                class="correct-tag"
              >
                正确答案：{{ formatCorrectAnswer(question) }}
              </el-tag>
            </div>
            <el-form
              v-if="editDraft?.questionId === question.question_id"
              label-position="top"
              :disabled="savingQuestion"
              @submit.prevent="saveQuestion(question)"
            >
              <el-form-item label="题干">
                <el-input v-model="editDraft.title" type="textarea" :rows="3" maxlength="2000" />
              </el-form-item>
              <template v-if="editDraft.options">
                <el-form-item v-for="key in Object.keys(editDraft.options)" :key="key" :label="'选项 ' + key">
                  <el-input v-model="editDraft.options[key]" type="textarea" autosize maxlength="2000" />
                </el-form-item>
                <el-form-item label="正确答案">
                  <el-select v-model="editDraft.answer" :multiple="question.question_type === 'multi'">
                    <el-option
                      v-for="key in Object.keys(editDraft.options)"
                      :key="key"
                      :label="key"
                      :value="key"
                      :disabled="!editDraft.options[key].trim()"
                    />
                  </el-select>
                </el-form-item>
              </template>
              <el-form-item>
                <el-button type="primary" native-type="submit" :loading="savingQuestion">
                  保存题目
                </el-button>
                <el-button @click="editDraft = null">取消编辑</el-button>
              </el-form-item>
            </el-form>
            <template v-else>
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
            </template>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button :disabled="savingQuestion" @click="showPaperDialog = false">关闭</el-button>
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
import { getPaperReview, updatePaperQuestion, getExamUserStatus, exportExamStudents } from '@/api/exam'
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
const loadingPapers = ref(false)
let paperListRequest = 0

const paperStatuses = {
  not_started: { text: '未开始', type: 'info' },
  normal: { text: '进行中', type: 'primary' },
  submitted: { text: '已交卷', type: 'warning' },
  graded: { text: '已批改', type: 'success' },
}

const showPaperDialog = ref(false)
const selectedPaper = ref(null)
const openingPaperId = ref(null)
const editDraft = ref(null)
const savingQuestion = ref(false)
const loadingExams = ref(false)

async function loadExamList() {
  loadingExams.value = true
  try {
    const first = await getExamList({ page: 1, size: 50 })
    const exams = [...first.list]
    for (let page = 2; page <= first.pages; page++) {
      const next = await getExamList({ page, size: 50 })
      exams.push(...next.list)
    }
    examList.value = exams
    if (!exams.some((exam) => exam.exam_id === selectedExamId.value)) {
      selectedExamId.value = exams[0]?.exam_id || ''
    }
    await handleExamChange()
  } catch {
    // 请求层已显示错误。
  } finally {
    loadingExams.value = false
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
  } else {
    paperListRequest++
    loadingPapers.value = false
  }
}

async function loadPaperList() {
  const requestId = ++paperListRequest
  loadingPapers.value = true
  try {
    const res = await getExamUserStatus(selectedExamId.value, {
      page: currentPage.value,
      size: pageSize.value,
    })
    if (requestId === paperListRequest) {
      paperList.value = res.list
      total.value = res.total
    }
  } catch {
    // 请求层已显示错误。
  } finally {
    if (requestId === paperListRequest) loadingPapers.value = false
  }
}

async function viewPaper(row) {
  const examId = selectedExamId.value
  openingPaperId.value = row.paper_id
  try {
    const res = await getPaperReview(row.paper_id)
    const questions = res.question_groups?.flatMap((group) => group.questions) || res.questions || []
    const missingImage = questions.some((question) =>
      Object.entries(question.options || {}).some(([key, value]) =>
        isImagePath(value) && !examStore.getCachedImage(question.question_id, key, value),
      ),
    )
    if (missingImage) await examStore.preloadExamImages(row.paper_id, true)
    if (examId === selectedExamId.value) {
      editDraft.value = null
      selectedPaper.value = { ...row, ...res, questions }
      showPaperDialog.value = true
    }
  } catch {
    // 请求层已显示错误。
  } finally {
    openingPaperId.value = null
  }
}

function beginQuestionEdit(question) {
  const isObjective = ['single', 'multi', 'judge'].includes(question.question_type)
  const defaultKeys = question.question_type === 'judge' ? ['A', 'B'] : ['A', 'B', 'C', 'D']
  const options = question.options || Object.fromEntries(defaultKeys.map((key) => [key, '']))
  editDraft.value = {
    questionId: question.question_id,
    title: question.title,
    options: isObjective ? { ...options } : null,
    answer: question.question_type === 'multi'
      ? normalizeAnswerList(question.correct_answer)
      : String(question.correct_answer || '').trim().toUpperCase(),
  }
}

async function saveQuestion(question) {
  if (savingQuestion.value) return
  const draft = editDraft.value
  const title = draft.title.trim()
  if (!title) {
    ElMessage.warning('请填写题干')
    return
  }

  const data = { revision: question.revision }
  if (title !== question.title) data.title = title
  if (draft.options) {
    const optionEntries = Object.entries(draft.options)
    if (optionEntries.some(([key, value]) => value !== (question.options?.[key] ?? ''))) {
      data.options = draft.options
    }
    const answer = Array.isArray(draft.answer) ? [...draft.answer].sort().join(',') : draft.answer
    const originalAnswer = question.question_type === 'multi'
      ? normalizeAnswerList(question.correct_answer).sort().join(',')
      : String(question.correct_answer || '').trim().toUpperCase()
    if (answer !== originalAnswer) data.correct_answer = answer
    if ((data.options || data.correct_answer !== undefined) && !answer) {
      ElMessage.warning('请选择正确答案')
      return
    }
  }
  if (Object.keys(data).length === 1) {
    editDraft.value = null
    return
  }

  savingQuestion.value = true
  try {
    const result = await updatePaperQuestion(selectedPaper.value.paper_id, question.question_id, data)
    Object.assign(question, result)
    editDraft.value = null
    ElMessage.success('题目已保存')
    if (data.options && Object.values(result.options || {}).some(isImagePath)) {
      await examStore.preloadExamImages(selectedPaper.value.paper_id, true)
    }
  } catch {
    // 保留草稿，便于修正后重试。
  } finally {
    savingQuestion.value = false
  }
}

function handleSizeChange(val) {
  pageSize.value = val
  currentPage.value = 1
  loadPaperList()
}

function handleCurrentChange(val) {
  if (val === currentPage.value) return
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
    const cachedUrl = examStore.getCachedImage(questionId, optionKey, path)
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
  const raw = String(answer || '').replace(/，/g, ',').trim().toUpperCase()
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
  return String(answer).trim().toUpperCase() === String(optKey)
}

// ==================== 格式化显示正确答案 ====================
function formatCorrectAnswer(question) {
  const answer = question.correct_answer
  if (!answer) return ''
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
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
}

.edit-question-button {
  margin-left: auto;
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
