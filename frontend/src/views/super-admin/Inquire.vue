<template>
  <div class="inquire-page">
    <div class="page-header">
      <div class="header-left">
        <h1>查询考试信息和成绩</h1>
        <p>快速查询考生考试信息和成绩数据</p>
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
          <el-button type="primary" @click="loadExamList" class="refresh-btn">
            <el-icon :size="16"><Refresh /></el-icon>
            刷新
          </el-button>
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
            <span>{{ selectedExam.submitted_count || 0 }}人</span>
          </div>
          <div class="info-item">
            <span class="info-label">已批改：</span>
            <span>{{ selectedExam.graded_count || 0 }}人</span>
          </div>
        </div>
      </el-card>
    </div>

    <div v-if="selectedExamId" class="result-section">
      <el-card class="result-card">
        <div class="result-header">
          <div class="header-left">
            <span>考生成绩列表</span>
            <span class="count">共 {{ total }} 条记录</span>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchKeyword"
              placeholder="请输入姓名或工号"
              clearable
              style="width: 200px; margin-right: 10px"
              @keyup.enter="handleSearch"
            />
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleExport" :loading="exportLoading">
              <el-icon><Download /></el-icon>
              导出Excel
            </el-button>
          </div>
        </div>

        <el-table :data="tableData" border v-loading="listLoading">
          <el-table-column prop="teacher_name" label="考生姓名" />
          <el-table-column prop="teacher_gh" label="工号" />
          <el-table-column prop="department" label="部门" />
          <el-table-column prop="submit_time" label="交卷时间">
            <template #default="scope">
              <span>{{ scope.row.submit_time || '未交卷' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="成绩">
            <template #default="scope">
              <span v-if="getEffectiveStatus(scope.row) === 'graded'">{{
                scope.row.score ?? '-'
              }}</span>
              <span v-else-if="scope.row.submit_time">待批改</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-tag :type="getStatusType(getEffectiveStatus(scope.row))">
                {{ getStatusText(getEffectiveStatus(scope.row)) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button size="small" @click="viewDetail(scope.row)">查看详情</el-button>
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

    <el-dialog v-model="showDetail" title="考试详情">
      <div v-if="selectedRow" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">考生姓名：</span>
          <span>{{ selectedRow.teacher_name }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">工号：</span>
          <span>{{ selectedRow.teacher_gh }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">交卷时间：</span>
          <span>{{ selectedRow.submit_time || '未交卷' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">成绩：</span>
          <span class="score" v-if="getEffectiveStatus(selectedRow) === 'graded'">{{
            selectedRow.score ?? '-'
          }}</span>
          <span v-else>待批改</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">状态：</span>
          <el-tag :type="getStatusType(getEffectiveStatus(selectedRow))">
            {{ getStatusText(getEffectiveStatus(selectedRow)) }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Refresh, Document, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getExamList } from '@/api/system'
import { getExamUserStatus, exportScoresExcel } from '@/api/exam'

const router = useRouter()

const examList = ref([])
const selectedExamId = ref('')
const selectedExam = computed(() => examList.value.find((e) => e.exam_id === selectedExamId.value))

const tableData = ref([])
const listLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showDetail = ref(false)
const selectedRow = ref(null)

const searchKeyword = ref('')
const exportLoading = ref(false)

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
    console.error('获取考试列表失败:', error)
    ElMessage.error('获取考试列表失败：' + (error.message || '请检查后端服务'))
  }
}

async function handleExamChange() {
  tableData.value = []
  currentPage.value = 1
  total.value = 0
  if (selectedExamId.value) {
    await loadStudentList()
  }
}

async function loadStudentList() {
  console.log('loadStudentList 被调用')
  console.log('  selectedExamId:', selectedExamId.value)
  console.log('  searchKeyword:', searchKeyword.value)
  console.log('  currentPage:', currentPage.value)

  listLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    console.log('  请求参数:', params)

    const res = await getExamUserStatus(selectedExamId.value, params)
    console.log('考生列表接口返回:', res)

    if (res && res.list) {
      tableData.value = res.list
      total.value = res.total || 0
    } else {
      tableData.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取考生列表失败:', error)
    ElMessage.error('获取考生列表失败')
  } finally {
    listLoading.value = false
  }
}

function handleSizeChange(val) {
  pageSize.value = val
  loadStudentList()
}

function handleCurrentChange(val) {
  currentPage.value = val
  loadStudentList()
}

function handleSearch() {
  console.log('handleSearch 被调用，searchKeyword:', searchKeyword.value)
  currentPage.value = 1
  loadStudentList()
}

function handleReset() {
  console.log('handleReset 被调用')
  searchKeyword.value = ''
  currentPage.value = 1
  loadStudentList()
}

async function handleExport() {
  if (!selectedExamId.value) {
    ElMessage.warning('请先选择考试')
    return
  }

  try {
    await ElMessageBox.confirm('请选择导出范围：', '导出成绩', {
      confirmButtonText: '导出全部',
      cancelButtonText: '仅已批改',
      cancelButtonClass: 'el-button--primary',
      type: 'info',
      distinguishCancelAndClose: true,
    })
    await doExport('all')
  } catch (action) {
    if (action === 'cancel' || action === 'close') {
      await doExport('graded_only')
    }
  }
}

async function doExport(exportScope) {
  exportLoading.value = true
  try {
    const blob = await exportScoresExcel(selectedExamId.value, { export_scope: exportScope })
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    const examName = selectedExam.value?.exam_name || '考试成绩'
    link.href = url
    link.download = `${examName}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败：' + (error.message || '请检查后端服务'))
  } finally {
    exportLoading.value = false
  }
}

function handleBack() {
  router.push('/super-admin/home')
}

function viewDetail(row) {
  selectedRow.value = row
  showDetail.value = true
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

function getStatusType(status) {
  const types = {
    graded: 'success',
    submitted: 'warning',
    not_submitted: 'info',
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    graded: '已批改',
    submitted: '待批改',
    not_submitted: '未交卷',
  }
  return texts[status] || status
}

/**
 * 获取考生的有效状态
 * 如果 score 字段有值（数字），说明已批改，即使 status 不是 'graded' 也按已批改处理
 * 解决后端发布成绩后未及时更新 status 字段的问题
 */
function getEffectiveStatus(row) {
  if (row.score !== null && row.score !== undefined && row.score !== '') {
    return 'graded'
  }
  return row.status
}

loadExamList()
</script>

<style scoped>
.inquire-page {
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

.back-button {
  display: flex;
  align-items: center;
  gap: 4px;
}

.exam-select-section {
  margin-bottom: 20px;
}

.select-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
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

.refresh-btn {
  margin-left: auto;
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

.result-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.result-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 500;
}

.result-header .header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-header .header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.count {
  font-size: 14px;
  color: #999;
  font-weight: normal;
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

.detail-content {
  padding: 10px 0;
}

.detail-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  width: 100px;
  color: #999;
  font-weight: 500;
}

.detail-row .score {
  font-size: 24px;
  font-weight: 600;
  color: #667eea;
}
</style>
