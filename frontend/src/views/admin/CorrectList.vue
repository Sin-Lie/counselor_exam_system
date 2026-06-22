<template>
  <div class="correct-page">
    <!-- ==================== 左侧边栏 ==================== -->
    <div class="sidebar">
      <!-- 退出登录按钮 -->
      <div class="logout-wrapper">
        <el-button type="default" @click="handleLogout" class="logout-btn"> 退出登录 </el-button>
      </div>

      <!-- 发布成绩按钮 -->
      <div class="publish-wrapper">
        <el-button
          type="success"
          :loading="publishing"
          :disabled="!currentExamId"
          class="publish-btn"
          @click="handlePublish"
        >
          发布成绩
        </el-button>
      </div>

      <!-- 考试列表 -->
      <div class="exam-list">
        <div class="list-header">
          <h3>考试列表</h3>
          <span class="list-count">{{ examList.length }} 场考试</span>
        </div>
        <div
          v-for="exam in examList"
          :key="exam.exam_id"
          class="exam-item"
          :class="{ active: currentExamId === exam.exam_id }"
          @click="selectExam(exam)"
        >
          <div class="exam-item-name">{{ exam.exam_name }}</div>
          <div class="exam-item-meta">
            <el-tag :type="examStatusType(exam.exam_status)" size="small" effect="plain">
              {{ examStatusText(exam.exam_status) }}
            </el-tag>
            <span class="exam-counts" v-if="exam.total_counselors > 0">
              {{ exam.submitted_count }}/{{ exam.total_counselors }}交
              <template v-if="exam.graded_count > 0"> · {{ exam.graded_count }}批 </template>
            </span>
          </div>
        </div>
        <div v-if="examLoading" class="empty-exam">加载考试列表中...</div>
        <div v-else-if="examList.length === 0" class="empty-exam">暂无考试数据</div>
      </div>
    </div>

    <!-- ==================== 右侧主内容区 ==================== -->
    <div class="main-content">
      <!-- 顶部工具栏 -->
      <div class="toolbar">
        <div class="current-exam">
          <span class="exam-label">当前考试：</span>
          <span class="exam-name">{{ currentExamName }}</span>
          <el-tag
            v-if="currentExamStatus"
            :type="examStatusType(currentExamStatus)"
            size="small"
            class="status-tag"
          >
            {{ examStatusText(currentExamStatus) }}
          </el-tag>
        </div>

        <!-- 批改进度 -->
        <div class="progress-wrapper">
          <div class="progress-info" v-if="correctProgress !== null">
            <span class="progress-text">
              已批改 {{ correctProgress.corrected }} / {{ correctProgress.total }} （{{
                correctProgress.total > 0 ? Math.round(correctProgress.progress * 100) : 0
              }}%）
            </span>
          </div>
          <!-- 各批改员进度 -->
          <div
            class="corrector-progress"
            v-if="
              correctProgress?.corrector_progress &&
              Object.keys(correctProgress.corrector_progress).length > 0
            "
          >
            <el-popover placement="bottom" :width="220" trigger="hover">
              <template #reference>
                <el-tag size="small" type="info" effect="plain" class="detail-tag"
                  >查看各批改员进度</el-tag
                >
              </template>
              <div class="corrector-progress-list">
                <div
                  v-for="(rate, name) in correctProgress.corrector_progress"
                  :key="name"
                  class="corrector-item"
                >
                  <span>{{ name }}</span>
                  <el-progress
                    :percentage="Math.round(rate * 100)"
                    :stroke-width="6"
                    style="width: 100px"
                  />
                </div>
              </div>
            </el-popover>
          </div>
        </div>
      </div>

      <!-- 未批改预览快速入口 -->
      <div class="preview-bar" v-if="correctProgress?.uncorrected_preview?.length > 0">
        <span class="preview-title">待批改预览：</span>
        <el-tag
          v-for="item in correctProgress.uncorrected_preview"
          :key="item.answer_id"
          type="warning"
          effect="plain"
          size="small"
          class="preview-tag"
          @click="handlePreviewJump(item)"
        >
          #{{ item.answer_id }} {{ item.examiner_name }}
        </el-tag>
      </div>

      <!-- 数据表格 - 待批改简答题列表 -->
      <div class="table-container">
        <el-table :data="sortedCorrectList" v-loading="loading" style="width: 100%" border>
          <el-table-column prop="answer_id" label="答题ID" width="80" />
          <el-table-column prop="examiner_name" label="考生姓名" width="120" />
          <el-table-column
            prop="question_title"
            label="题目"
            min-width="200"
            show-overflow-tooltip
          />
          <el-table-column
            prop="user_answer"
            label="学生作答"
            min-width="200"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span class="answer-preview">{{ truncateText(row.user_answer, 50) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="current_total_score" label="当前总分" width="100" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                :type="hasCorrected(row) ? 'warning' : 'primary'"
                @click="handleCorrect(row)"
                class="correct-btn"
              >
                {{ hasCorrected(row) ? '修改分数' : '批改' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 无数据提示 -->
        <div v-if="!loading && sortedCorrectList.length === 0" class="empty-state">
          <el-empty
            :description="currentExamId ? '该考试暂无待批改题目' : '请先在左侧选择一个考试'"
          />
        </div>

        <!-- 分页 -->
        <div v-if="pagination.total > 0" class="pagination">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 批改列表页面
 * 对接后端 GET /api/correct/list/ 获取待批改简答题（含分页）
 * 对接后端 GET /api/correct/progress/ 获取批改进度统计
 * 对接后端 GET /api/system/exam/list/ 获取考试列表
 *
 * 后端返回参数全部使用：
 * - exam 对象：exam_id, exam_name, exam_status, total_counselors, submitted_count, graded_count
 * - correct list：answer_id, question_title, user_answer, standard_answer, examiner_name, current_total_score
 * - progress：total, corrected, progress, corrector_progress, uncorrected_preview
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getCorrectList, getCorrectProgress, publishScores } from '@/api/correct'
import { getExamManageList } from '@/api/system'

const router = useRouter()
const userStore = useUserStore()

// ==================== 状态定义 ====================
const loading = ref(false)
const examLoading = ref(false)
const publishing = ref(false) // 发布成绩加载状态

// 考试列表（从后端加载）
const examList = ref([])
const currentExamId = ref(null)

// 当前考试名称
const currentExamName = computed(() => {
  const exam = examList.value.find((e) => e.exam_id === currentExamId.value)
  return exam ? exam.exam_name : '请选择考试'
})

// 当前考试状态
const currentExamStatus = computed(() => {
  const exam = examList.value.find((e) => e.exam_id === currentExamId.value)
  return exam ? exam.exam_status : ''
})

// 待批改列表
const correctList = ref([])

// 排序后的批改列表：未批改（existing_score 为 null）在前，已批改在后
const sortedCorrectList = computed(() => {
  return [...correctList.value].sort((a, b) => {
    const aScored = a.existing_score !== null && a.existing_score !== undefined
    const bScored = b.existing_score !== null && b.existing_score !== undefined
    // null 排前面，有值排后面
    if (aScored && !bScored) return 1
    if (!aScored && bScored) return -1
    return 0
  })
})

// 批改进度
const correctProgress = ref(null)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

// ==================== 考试状态映射 ====================
const examStatusMap = {
  not_started: { text: '未开始', type: 'info' },
  ongoing: { text: '进行中', type: 'success' },
  ended: { text: '已结束', type: 'warning' },
  closed: { text: '已关闭', type: 'danger' },
}

function examStatusType(status) {
  return examStatusMap[status]?.type || 'info'
}

function examStatusText(status) {
  return examStatusMap[status]?.text || status || '未知'
}

// ==================== 方法定义 ====================
/**
 * 加载考试列表
 */
async function loadExamList() {
  examLoading.value = true
  try {
    const res = await getExamManageList({ page: 1, size: 50 })
    examList.value = res.list || []

    // 优先从 sessionStorage 恢复上次选中的考试
    const savedExamId = sessionStorage.getItem('correctSelectedExam')
    if (savedExamId) {
      const savedId = parseInt(savedExamId, 10)
      const found = examList.value.find((e) => e.exam_id === savedId)
      if (found) {
        currentExamId.value = savedId
        await Promise.all([loadCorrectList(), loadCorrectProgress()])
        return
      }
    }

    // 默认选中第一个考试
    if (examList.value.length > 0 && !currentExamId.value) {
      currentExamId.value = examList.value[0].exam_id
      await Promise.all([loadCorrectList(), loadCorrectProgress()])
    }
  } catch (error) {
    console.error('加载考试列表失败', error)
    ElMessage.error('加载考试列表失败，请检查网络或联系管理员')
  } finally {
    examLoading.value = false
  }
}

/**
 * 选择考试
 */
function selectExam(exam) {
  currentExamId.value = exam.exam_id
  sessionStorage.setItem('correctSelectedExam', String(exam.exam_id))
  pagination.page = 1
  loadCorrectList()
  loadCorrectProgress()
}

/**
 * 加载待批改列表
 */
async function loadCorrectList() {
  if (!currentExamId.value) return

  loading.value = true
  try {
    const params = {
      exam_id: currentExamId.value,
      page: pagination.page,
      size: pagination.pageSize,
    }
    const res = await getCorrectList(params)
    correctList.value = res.list || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载批改列表失败', error)
    ElMessage.error('加载批改列表失败')
    correctList.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

/**
 * 加载批改进度
 */
async function loadCorrectProgress() {
  if (!currentExamId.value) return
  try {
    const res = await getCorrectProgress(currentExamId.value)
    correctProgress.value = res
  } catch (error) {
    console.error('加载批改进度失败', error)
  }
}

/**
 * 截断文本
 */
function truncateText(text, maxLen) {
  if (!text) return ''
  return text.length > maxLen ? text.substring(0, maxLen) + '...' : text
}

/**
 * 从未批改预览快速跳转
 */
function handlePreviewJump(item) {
  // 预览数据只有 answer_id、question_title、examiner_name，没有完整数据
  // 点击后在列表中定位该条
  ElMessage.info(`请在列表中查找答题ID #${item.answer_id}`)
}

/**
 * 判断某条记录是否已批改
 * @param {Object} row - 列表行数据
 * @returns {boolean} 是否已批改
 */
function hasCorrected(row) {
  return row.existing_score !== null && row.existing_score !== undefined
}

/**
 * 进入批改详情
 */
function handleCorrect(row) {
  // 保存当前选中的考试ID
  sessionStorage.setItem('correctSelectedExam', String(currentExamId.value))
  // 将排序后的列表存入 sessionStorage，供批改详情页自动跳转下一题使用
  const nextList = sortedCorrectList.value.map((item) => ({
    answer_id: item.answer_id,
    examiner_name: item.examiner_name || '',
    question_title: item.question_title || '',
    user_answer: item.user_answer || '',
    current_total_score: item.current_total_score || 0,
    standard_answer: item.standard_answer || null,
    existing_score: item.existing_score,
    existing_remark: item.existing_remark || '',
  }))
  sessionStorage.setItem('correctNextList', JSON.stringify(nextList))
  router.push({
    path: '/admin/correct-do',
    query: {
      answerId: row.answer_id,
      examId: currentExamId.value,
      examinerName: row.examiner_name || '',
      questionTitle: row.question_title || '',
      userAnswer: row.user_answer || '',
      currentTotalScore: row.current_total_score || 0,
      standardAnswer: row.standard_answer
        ? encodeURIComponent(JSON.stringify(row.standard_answer))
        : '',
      // 已批改的分数和批注，用于修改时预填
      existingScore: hasCorrected(row) ? row.existing_score : undefined,
      existingRemark: row.existing_remark || undefined,
    },
  })
}

/**
 * 分页大小变化
 */
function handleSizeChange() {
  pagination.page = 1
  loadCorrectList()
}

/**
 * 页码变化
 */
function handlePageChange() {
  loadCorrectList()
}

/**
 * 发布批改成绩
 */
async function handlePublish() {
  if (!currentExamId.value) {
    ElMessage.warning('请先在左侧选择一个考试')
    return
  }
  try {
    await ElMessageBox.confirm(
      '发布后无法再修改分数，确定要发布当前考试的所有批改成绩吗？',
      '发布成绩',
      {
        confirmButtonText: '确定发布',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return // 用户取消
  }

  publishing.value = true
  try {
    await publishScores(currentExamId.value)
    ElMessage.success('成绩发布成功')
    // 刷新批改进度
    await loadCorrectProgress()
  } catch (error) {
    console.error('发布成绩失败', error)
    // 错误消息由响应拦截器统一弹出
  } finally {
    publishing.value = false
  }
}

/**
 * 退出登录
 */
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    sessionStorage.removeItem('correctSelectedExam')
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (e) {
    // 用户取消
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadExamList()
})
</script>

<style scoped>
/**
 * 批改列表页面样式
 */
.correct-page {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #e6f7ff;
}

/* ==================== 左侧边栏样式 ==================== */
.sidebar {
  width: 250px;
  height: 100vh;
  background: #fff;
  border-right: 1px solid #d9d9d9;
  display: flex;
  flex-direction: column;
}

.logout-wrapper {
  padding: 15px;
  border-bottom: 1px solid #e8e8e8;
}

.logout-btn {
  width: 100%;
  background: #f5f5f5;
  color: #333;
  border: 1px solid #d9d9d9;
}

.publish-wrapper {
  padding: 0 15px 15px 15px; /* 上左右内边距 */
  border-bottom: 1px solid #e8e8e8; /* 底部分隔线 */
}

.publish-btn {
  width: 100%; /* 全宽 */
}

.exam-list {
  flex: 1;
  overflow-y: auto;
}

.list-header {
  padding: 12px 15px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.list-count {
  font-size: 11px;
  color: #999;
}

.exam-item {
  padding: 10px 15px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 3px solid transparent;
  border-bottom: 1px solid #f5f5f5;
}

.exam-item:hover {
  background: #f5f5f5;
}

.exam-item.active {
  background: #e6f7ff;
  border-left-color: #1890ff;
}

.exam-item-name {
  font-size: 13px;
  color: #333;
  margin-bottom: 4px;
}

.exam-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.exam-counts {
  font-size: 11px;
  color: #999;
}

.empty-exam {
  padding: 40px 20px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

/* ==================== 右侧主内容区样式 ==================== */
.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 15px 20px;
  background: #fff;
  border-radius: 4px;
}

.current-exam {
  display: flex;
  align-items: center;
  gap: 8px;
}

.exam-label {
  font-size: 14px;
  color: #666;
}

.exam-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.status-tag {
  margin-left: 4px;
}

.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-info {
  font-size: 14px;
  color: #1890ff;
}

.detail-tag {
  cursor: pointer;
}

.corrector-progress-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.corrector-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
}

/* 未批改预览栏 */
.preview-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px 16px;
  background: #fff;
  border-radius: 4px;
  margin-bottom: 16px;
}

.preview-title {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}

.preview-tag {
  cursor: pointer;
}

.table-container {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
}

.answer-preview {
  color: #666;
  font-size: 13px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 统一批改按钮尺寸 */
.correct-btn {
  min-width: 72px; /* 固定最小宽度，确保按钮大小一致 */
  width: 72px; /* 固定宽度 */
  height: 28px; /* 固定高度（Element small 按钮默认高度） */
}
</style>
