<template>
  <div class="setexam-page">
    <div class="page-header">
      <div class="header-left">
        <h1>考试配置</h1>
        <p>创建和配置考试参数</p>
      </div>
      <div class="header-right">
        <el-button @click="handleBack" class="back-button">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
    </div>

    <div class="form-section">
      <el-card class="form-card">
        <div class="mode-switch">
          <el-radio-group v-model="generateMode" @change="handleModeChange">
            <el-radio-button value="by_student">传统出题</el-radio-button>
            <el-radio-button value="by_type">新型出题</el-radio-button>
          </el-radio-group>
        </div>

        <el-form :model="examForm" :rules="examRules" ref="examFormRef" label-width="120px">
          <div class="form-row">
            <el-form-item label="考试名称" prop="examName">
              <el-input v-model="examForm.examName" placeholder="请输入考试名称" />
            </el-form-item>
          </div>

          <div class="form-row">
            <el-form-item label="考试日期" prop="startDate">
              <el-date-picker
                v-model="examForm.startDate"
                type="date"
                placeholder="选择考试日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item label="开始时间" prop="startTime">
              <el-time-picker
                v-model="examForm.startTime"
                placeholder="选择开始时间"
                format="HH:mm"
                value-format="HH:mm"
              />
            </el-form-item>
          </div>

          <div class="form-row">
            <el-form-item label="考试时长(分钟)" prop="duration">
              <el-input v-model.number="examForm.duration" placeholder="请输入考试时长" />
            </el-form-item>
          </div>

          <div class="form-row" v-if="generateMode === 'by_student'">
            <el-form-item label="抽选学生数" prop="studentCount">
              <el-input-number
                v-model="examForm.studentCount"
                :min="0"
                :max="50"
                size="default"
                style="width: 100%"
              />
              <div class="field-hint">0 表示每个辅导员名下全部学生，最大 50 人</div>
            </el-form-item>
          </div>

          <el-divider content-position="left">题目配置</el-divider>

          <div class="question-config">
            <div class="question-header">
              <span>总题数：{{ totalQuestionCount }} 道</span>
              <template v-if="generateMode === 'by_student'">
                <span style="margin-left: 20px">个人总分：{{ totalScore }} 分</span>
                <span style="margin-left: 20px">题目总分：{{ questionTotalScore }} 分</span>
              </template>
              <template v-else>
                <span style="margin-left: 20px">总分：{{ totalScore }} 分</span>
              </template>
            </div>

            <el-form :model="questionConfig" label-width="100px" class="question-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="单选题">
                    <div class="question-type-row">
                      <span>数量：</span>
                      <el-input-number
                        v-model="questionConfig.single.count"
                        :min="0"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                      <span style="margin-left: 16px">每道分值：</span>
                      <el-input-number
                        v-model="questionConfig.single.score"
                        :min="1"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="多选题">
                    <div class="question-type-row">
                      <span>数量：</span>
                      <el-input-number
                        v-model="questionConfig.multiple.count"
                        :min="0"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                      <span style="margin-left: 16px">每道分值：</span>
                      <el-input-number
                        v-model="questionConfig.multiple.score"
                        :min="1"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="判断题">
                    <div class="question-type-row">
                      <span>数量：</span>
                      <el-input-number
                        v-model="questionConfig.judge.count"
                        :min="0"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                      <span style="margin-left: 16px">每道分值：</span>
                      <el-input-number
                        v-model="questionConfig.judge.score"
                        :min="1"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="简答题">
                    <div class="question-type-row">
                      <span>数量：</span>
                      <el-input-number
                        v-model="questionConfig.essay.count"
                        :min="0"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                      <span style="margin-left: 16px">每道分值：</span>
                      <el-input-number
                        v-model="questionConfig.essay.score"
                        :min="1"
                        :max="100"
                        size="default"
                        @change="updateTotalScore"
                      />
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>

            <div class="question-summary">
              <el-card shadow="hover">
                <template #header>
                  <span>题型分布</span>
                </template>
                <div class="summary-content">
                  <div class="summary-item">
                    <el-tag type="primary">单选题</el-tag>
                    <span
                      >{{ questionConfig.single.count }} 道 × {{ questionConfig.single.score }} 分 =
                      {{ questionConfig.single.count * questionConfig.single.score }} 分</span
                    >
                  </div>
                  <div class="summary-item">
                    <el-tag type="success">多选题</el-tag>
                    <span
                      >{{ questionConfig.multiple.count }} 道 ×
                      {{ questionConfig.multiple.score }} 分 =
                      {{ questionConfig.multiple.count * questionConfig.multiple.score }} 分</span
                    >
                  </div>
                  <div class="summary-item">
                    <el-tag type="warning">判断题</el-tag>
                    <span
                      >{{ questionConfig.judge.count }} 道 × {{ questionConfig.judge.score }} 分 =
                      {{ questionConfig.judge.count * questionConfig.judge.score }} 分</span
                    >
                  </div>
                  <div class="summary-item">
                    <el-tag>简答题</el-tag>
                    <span
                      >{{ questionConfig.essay.count }} 道 × {{ questionConfig.essay.score }} 分 =
                      {{ questionConfig.essay.count * questionConfig.essay.score }} 分</span
                    >
                  </div>
                </div>
              </el-card>
            </div>
          </div>

          <div class="form-actions">
            <el-button @click="handleReset">重置</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitLoading"
              >保存设置</el-button
            >
          </div>
        </el-form>
      </el-card>
    </div>

    <div class="preview-section">
      <el-card class="preview-card">
        <template #header>
          <div class="card-header-with-refresh">
            <h3>考试列表</h3>
            <el-button type="primary" plain @click="loadExamList" :loading="listLoading">
              <el-icon><Refresh /></el-icon>
              刷新列表
            </el-button>
          </div>
        </template>
        <el-table :data="examList" v-loading="listLoading" stripe style="width: 100%">
          <el-table-column prop="exam_id" label="ID" width="80" />
          <el-table-column prop="exam_name" label="考试名称" min-width="180" />
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.exam_status)">
                {{ getStatusText(scope.row.exam_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="release_date" label="发布日期" width="130" />
          <el-table-column prop="start_time" label="开始时间" min-width="160" />
          <el-table-column prop="duration" label="时长" width="100">
            <template #default="scope"> {{ scope.row.duration }}分钟 </template>
          </el-table-column>
          <el-table-column label="考生统计" width="200">
            <template #default="scope">
              <div>总数：{{ scope.row.total_counselors || 0 }}</div>
              <div style="font-size: 12px; color: #909399">
                已交卷：{{ scope.row.submitted_count || 0 }} | 已批改：{{
                  scope.row.graded_count || 0
                }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <div style="display: flex; gap: 8px">
                <el-button
                  type="primary"
                  size="small"
                  @click="handlePreview(scope.row.exam_id)"
                  :loading="previewLoading && selectedExamId === scope.row.exam_id"
                >
                  <el-icon><View /></el-icon>
                  预览
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(scope.row)"
                  :loading="deleteLoading && deleteExamId === scope.row.exam_id"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <el-empty
          v-if="examList.length === 0 && !listLoading"
          description="暂无考试数据，请先创建考试"
          style="margin-top: 40px"
        />
        <!-- 分页 -->
        <el-pagination
          v-if="totalPages > 1"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalCount"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadExamList"
          @current-change="loadExamList"
          style="margin-top: 20px; justify-content: flex-end"
        />
      </el-card>
    </div>

    <!-- 试卷预览对话框 -->
    <el-dialog v-model="previewDialogVisible" title="试卷预览" width="900px" destroy-on-close>
      <div v-loading="previewLoading">
        <!-- 试卷头部 -->
        <div v-if="previewExamInfo" class="paper-header">
          <div class="paper-title">{{ previewExamInfo.exam_name }}</div>
          <div class="paper-info">
            <span class="info-item">考试时长：{{ previewExamInfo.duration }}分钟</span>
            <span class="info-item">总分：{{ previewExamInfo.total_score }}分</span>
            <span class="info-item">题目数量：{{ previewExamInfo.question_count }}道</span>
          </div>
          <div class="paper-notice">
            <strong>注意事项：</strong>
            <span>请仔细阅读题目，按要求作答。考试时间结束后系统将自动提交试卷。</span>
          </div>
        </div>

        <!-- 试卷内容 -->
        <div v-if="previewData && previewData.length > 0" class="paper-content">
          <!-- 按题型分组显示 -->
          <div v-for="(group, type) in groupedQuestions" :key="type" class="question-group">
            <div class="group-header">
              <el-tag :type="getQuestionTypeTag(type)" size="medium">
                {{ getQuestionTypeText(type) }}
              </el-tag>
              <span class="group-info"
                >（共{{ group.length }}题，每题{{ group[0]?.score || 0 }}分，共{{
                  group.length * (group[0]?.score || 0)
                }}分）</span
              >
            </div>
            <div v-for="(question, index) in group" :key="question._index" class="question-item">
              <div class="question-number">{{ question._global_index }}.</div>
              <div class="question-body">
                <div class="question-text">{{ question.title }}</div>
                <div class="question-score-label">（{{ question.score }}分）</div>
                <!-- 选项区域 -->
                <div
                  v-if="question.options && Object.keys(question.options).length > 0"
                  class="options-area"
                >
                  <div v-for="(value, key) in question.options" :key="key" class="option-row">
                    <span class="option-label">{{ key }}.</span>
                    <span class="option-content">{{ value }}</span>
                  </div>
                </div>
                <!-- 简答题答题区域 -->
                <div v-else-if="question.question_type === 'essay'" class="essay-area">
                  <div class="essay-label">答题区域：</div>
                  <div class="essay-box"></div>
                </div>
                <!-- 解析区域 -->
                <div v-if="question.analysis" class="analysis-section">
                  <el-divider content-position="left">【解析】</el-divider>
                  <p class="analysis-content">{{ question.analysis }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无预览数据" />
      </div>
      <!-- 对话框底部 -->
      <template #footer>
        <div class="preview-footer">
          <span class="preview-total"
            >共 {{ previewData?.length || 0 }} 道题目，总分
            {{ previewExamInfo?.total_score || 0 }} 分</span
          >
          <el-button @click="previewDialogVisible = false">关闭预览</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Document, View, Refresh, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getQuestionList, createExam, previewExam, getExamList, deleteExam } from '@/api/system'

const router = useRouter()
const examFormRef = ref(null)
const questionTableRef = ref(null)
const loading = ref(false)
const submitLoading = ref(false)
const activeTab = ref('select')
const questionSearch = ref('')
const questionTypeFilter = ref('')

const generateMode = ref('by_student')
const selectedExamId = ref(null)
const examList = ref([])
const listLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

// 试卷预览相关变量
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewData = ref(null)
const previewExamName = ref('')
const previewExamInfo = ref(null)

// 删除考试相关变量
const deleteLoading = ref(false)
const deleteExamId = ref(null)

// 按题型分组的题目（用于预览显示）
const groupedQuestions = computed(() => {
  if (!previewData.value || !Array.isArray(previewData.value)) {
    return {}
  }
  const groups = {}
  let globalIndex = 1

  previewData.value.forEach((question) => {
    const type = question.question_type || 'single'
    if (!groups[type]) {
      groups[type] = []
    }
    groups[type].push({
      ...question,
      _index: groups[type].length,
      _global_index: globalIndex++,
    })
  })

  return groups
})

const examForm = reactive({
  examName: '',
  startDate: '',
  startTime: '',
  duration: 120,
  studentCount: 0,
})

const examRules = {
  examName: [{ required: true, message: '请输入考试名称', trigger: 'blur' }],
  startDate: [{ required: true, message: '请选择考试日期', trigger: 'change' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  duration: [
    { required: true, message: '请输入考试时长', trigger: 'blur' },
    { type: 'number', min: 1, message: '考试时长至少1分钟', trigger: 'blur' },
  ],
}

const questionList = ref([])
const selectedQuestions = ref([])

const questionConfig = reactive({
  single: { count: 2, score: 1 },
  multiple: { count: 1, score: 2 },
  judge: { count: 1, score: 1 },
  essay: { count: 1, score: 5 },
})

const totalQuestionCount = computed(() => {
  return (
    questionConfig.single.count +
    questionConfig.multiple.count +
    questionConfig.judge.count +
    questionConfig.essay.count
  )
})

const totalScore = computed(() => {
  return (
    questionConfig.single.count * questionConfig.single.score +
    questionConfig.multiple.count * questionConfig.multiple.score +
    questionConfig.judge.count * questionConfig.judge.score +
    questionConfig.essay.count * questionConfig.essay.score
  )
})

const questionTotalScore = computed(() => {
  return totalScore.value * examForm.studentCount
})

function updateTotalScore() {
  // 根据题目配置自动计算总分
}

function handleModeChange() {
  examForm.studentCount = 0
  if (generateMode.value === 'by_student') {
    questionConfig.single = { count: 2, score: 1 }
    questionConfig.multiple = { count: 1, score: 2 }
    questionConfig.judge = { count: 1, score: 1 }
    questionConfig.essay = { count: 1, score: 5 }
  } else {
    questionConfig.single = { count: 10, score: 2 }
    questionConfig.multiple = { count: 10, score: 3 }
    questionConfig.judge = { count: 10, score: 2 }
    questionConfig.essay = { count: 6, score: 5 }
  }
}

onMounted(() => {
  loadExamList()
})

async function loadQuestions() {
  loading.value = true
  try {
    const params = {
      page: pageInfo.page,
      size: pageInfo.size,
    }
    if (questionSearch.value) {
      params.keyword = questionSearch.value
    }
    if (questionTypeFilter.value) {
      params.type = questionTypeFilter.value
    }
    const response = await getQuestionList(params)
    const questionData = response.results || response.data || response.list || []
    if (Array.isArray(questionData) && questionData.length > 0) {
      questionList.value = questionData
      pageInfo.total = response.total || questionData.length
    }
  } catch (error) {
    console.error('获取题目列表失败', error)
  } finally {
    loading.value = false
  }
}

function handleQuestionSearch() {
  pageInfo.page = 1
  loadQuestions()
}

function handlePageSizeChange(size) {
  pageInfo.size = size
  pageInfo.page = 1
  loadQuestions()
}

function handlePageChange(page) {
  pageInfo.page = page
  loadQuestions()
}

function handleQuestionSelectionChange(selection) {
  selection.forEach((item) => {
    const exists = selectedQuestions.value.find((q) => q.id === item.id)
    if (!exists) {
      selectedQuestions.value.push({ ...item, index: selectedQuestions.value.length + 1 })
    }
  })

  const selectedIds = selection.map((item) => item.id)
  selectedQuestions.value = selectedQuestions.value.filter((q) => selectedIds.includes(q.id))
}

function removeSelectedQuestion(id) {
  selectedQuestions.value = selectedQuestions.value.filter((q) => q.id !== id)
  selectedQuestions.value.forEach((q, index) => {
    q.index = index + 1
  })

  if (questionTableRef.value) {
    questionTableRef.value.toggleRowSelection(
      questionList.value.find((q) => q.id === id),
      false,
    )
  }
}

// 加载考试列表
async function loadExamList() {
  listLoading.value = true
  try {
    const res = await getExamList({ page: currentPage.value, size: pageSize.value })
    console.log('考试列表响应:', res)
    const data = res?.data || res
    if (data) {
      examList.value = data?.list || []
      totalCount.value = data?.total || 0
    }
  } catch (error) {
    console.error('加载考试列表失败', error)
    ElMessage.error('加载考试列表失败：' + (error.message || '请检查后端服务'))
  } finally {
    listLoading.value = false
  }
}

// 获取考试状态标签类型
function getStatusType(status) {
  switch (status) {
    case 'not_started':
      return 'info'
    case 'normal':
      return 'success'
    case 'ended':
      return 'warning'
    case 'closed':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取考试状态文本
function getStatusText(status) {
  switch (status) {
    case 'not_started':
      return '未发布'
    case 'normal':
      return '进行中'
    case 'ended':
      return '已结束'
    case 'closed':
      return '已关闭'
    default:
      return '未知'
  }
}

// 删除考试功能
async function handleDelete(row) {
  if (!row || !row.exam_id) {
    ElMessage.warning('考试信息无效')
    return
  }

  try {
    await ElMessageBox.confirm(`确定要删除考试"${row.exam_name}"吗？删除后无法恢复。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  deleteLoading.value = true
  deleteExamId.value = row.exam_id

  try {
    const res = await deleteExam(row.exam_id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      await loadExamList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (error) {
    console.error('删除考试失败', error)
    ElMessage.error('删除失败：' + (error.message || '请检查后端服务'))
  } finally {
    deleteLoading.value = false
    deleteExamId.value = null
  }
}

// 试卷预览功能
async function handlePreview(examId) {
  if (!examId) {
    ElMessage.warning('请选择一个考试')
    return
  }

  selectedExamId.value = examId
  previewDialogVisible.value = true
  previewLoading.value = true
  try {
    const res = await previewExam(examId)
    console.log('试卷预览响应:', res)
    // 响应拦截器已扁平化处理，字段直接在 res 中
    if (res && res.code === 200) {
      // 兼容 by_student 模式：question_groups 扁平化为 questions 数组
      let flatQuestions = []
      if (res.question_groups && res.question_groups.length > 0) {
        flatQuestions = res.question_groups.flatMap(function (group) {
          return group.questions || []
        })
      } else {
        flatQuestions = res.questions || []
      }
      previewData.value = flatQuestions

      // 计算总分
      const totalScore = flatQuestions.reduce((sum, q) => sum + (q.score || 0), 0)

      // 设置考试信息
      previewExamInfo.value = {
        exam_name: res.exam_name || '试卷预览',
        duration: res.duration || examForm.duration || 90,
        total_score: totalScore,
        question_count: flatQuestions.length,
      }
    } else {
      ElMessage.warning(res?.msg || '预览数据为空')
    }
  } catch (error) {
    console.error('预览加载失败', error)
    ElMessage.error('加载预览失败：' + (error.message || '请检查后端服务'))
  } finally {
    previewLoading.value = false
  }
}

function handleBack() {
  router.push('/super-admin/home')
}

function handleReset() {
  examForm.examName = ''
  examForm.startDate = ''
  examForm.startTime = ''
  examForm.duration = 120
  examForm.studentCount = 0
  questionConfig.single = { count: 10, score: 2 }
  questionConfig.multiple = { count: 10, score: 3 }
  questionConfig.judge = { count: 10, score: 2 }
  questionConfig.essay = { count: 6, score: 5 }
}

async function handleSubmit() {
  try {
    await examFormRef.value.validate()

    if (totalQuestionCount.value === 0) {
      ElMessage.warning('请至少设置一道题目')
      return
    }

    if (generateMode.value === 'by_type' && totalScore.value !== 100) {
      ElMessage.error(
        `新型出题模式下，考试总分必须等于100分，当前配置总分为${totalScore.value}分`,
      )
      return
    }

    const questions = []
    if (questionConfig.single.count > 0) {
      questions.push({
        type: 'single',
        count: questionConfig.single.count,
        score: questionConfig.single.score,
      })
    }
    if (questionConfig.multiple.count > 0) {
      questions.push({
        type: 'multi',
        count: questionConfig.multiple.count,
        score: questionConfig.multiple.score,
      })
    }
    if (questionConfig.judge.count > 0) {
      questions.push({
        type: 'judge',
        count: questionConfig.judge.count,
        score: questionConfig.judge.score,
      })
    }
    if (questionConfig.essay.count > 0) {
      questions.push({
        type: 'essay',
        count: questionConfig.essay.count,
        score: questionConfig.essay.score,
      })
    }

    const data = {
      exam_name: examForm.examName,
      release_time: examForm.startDate || new Date().toISOString().split('T')[0],
      exam_start:
        examForm.startDate && examForm.startTime
          ? examForm.startDate + ' ' + examForm.startTime + ':00'
          : '',
      exam_duration: examForm.duration,
      questions: questions,
      generate_mode: generateMode.value,
    }

    if (generateMode.value === 'by_student') {
      data.student_count = examForm.studentCount
    }

    submitLoading.value = true

    try {
      await createExam(data)
      ElMessage.success('考试创建成功，将为所有辅导员自动生成试卷')
      handleReset()
      loadExamList()
    } finally {
      submitLoading.value = false
    }
  } catch (error) {
    console.log('表单验证失败')
  }
}

function getExamTypeText(type) {
  const texts = {
    quarter: '季度考试',
    year: '年度考试',
    practice: '模拟考试',
    special: '专项考试',
  }
  return texts[type] || '未设置'
}

function getQuestionTypeText(type) {
  const texts = {
    single: '单选题',
    multiple: '多选题',
    judge: '判断题',
    essay: '简答题',
  }
  return texts[type] || type
}

function getQuestionTypeTag(type) {
  const tags = {
    single: 'primary',
    multiple: 'success',
    judge: 'warning',
    essay: 'info',
  }
  return tags[type] || 'default'
}
</script>

<style scoped>
.setexam-page {
  padding: 20px;
  min-height: 100%;
  background: #f5f7fa;
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  flex: 1;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.header-left p {
  font-size: 14px;
  color: #999;
  margin: 8px 0 0;
}

.header-right {
  margin-left: 20px;
}

.back-button {
  padding: 8px 16px;
}

.form-section {
  margin-bottom: 20px;
}

.form-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 24px;
}

.mode-switch {
  margin-bottom: 24px;
  text-align: center;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.form-row {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.form-row .el-form-item {
  flex: 1;
}

.form-row:last-child {
  margin-bottom: 0;
}

.question-config {
  margin: 20px 0;
}

.question-header {
  margin-bottom: 16px;
  font-weight: 500;
  color: #606266;
}

.question-form {
  margin-bottom: 20px;
}

.question-type-row {
  display: flex;
  align-items: center;
}

.question-type-row span {
  white-space: nowrap;
}

.question-summary {
  margin-top: 20px;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-item .el-tag {
  min-width: 80px;
  text-align: center;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-bar .el-input {
  flex: 1;
  max-width: 300px;
}

.search-bar .el-select {
  width: 150px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

.empty-icon {
  color: #ccc;
  margin-bottom: 16px;
}

.empty-state p {
  color: #999;
  margin-bottom: 16px;
}

.score-summary {
  display: flex;
  align-items: baseline;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-label {
  color: #666;
  font-size: 14px;
  margin-right: 8px;
}

.summary-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
}

.summary-unit {
  color: #666;
  margin-left: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.preview-section {
  margin-bottom: 20px;
}

.card-header-with-refresh {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header-with-refresh h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.preview-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 24px;
}

.preview-content {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.preview-item {
  display: flex;
  width: calc(50% - 8px);
}

.preview-label {
  color: #999;
  margin-right: 8px;
  min-width: 100px;
}

/* 试卷预览对话框样式 */
.paper-header {
  padding: 20px;
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  border-radius: 8px;
  margin-bottom: 24px;
  color: #fff;
}

.paper-title {
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 12px;
}

.paper-info {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 12px;
}

.info-item {
  font-size: 14px;
  opacity: 0.9;
}

.paper-notice {
  font-size: 13px;
  opacity: 0.85;
  text-align: center;
}

.paper-content {
  max-height: 550px;
  overflow-y: auto;
  padding-right: 10px;
}

.question-group {
  margin-bottom: 30px;
}

.group-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e4e7ed;
}

.group-info {
  margin-left: 12px;
  color: #606266;
  font-size: 14px;
}

.question-item {
  display: flex;
  margin-bottom: 20px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.question-number {
  font-weight: bold;
  font-size: 16px;
  color: #409eff;
  min-width: 30px;
  text-align: right;
  margin-right: 12px;
}

.question-body {
  flex: 1;
}

.question-text {
  font-size: 15px;
  color: #303133;
  line-height: 1.8;
  margin-bottom: 8px;
}

.question-score-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 16px;
  display: block;
}

.options-area {
  padding-left: 20px;
}

.option-row {
  display: flex;
  margin-bottom: 10px;
  line-height: 1.6;
}

.option-row:last-child {
  margin-bottom: 0;
}

.option-label {
  font-weight: bold;
  color: #409eff;
  min-width: 24px;
}

.option-content {
  color: #606266;
}

.essay-area {
  margin-top: 12px;
}

.essay-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.essay-box {
  min-height: 150px;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  background: #fff;
}

.analysis-section {
  margin-top: 16px;
  padding-top: 16px;
}

.analysis-content {
  font-size: 14px;
  color: #67c23a;
  line-height: 1.8;
}

.preview-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.preview-total {
  font-size: 14px;
  color: #606266;
}

/* 滚动条样式 */
.paper-content::-webkit-scrollbar {
  width: 6px;
}

.paper-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.paper-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.paper-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
