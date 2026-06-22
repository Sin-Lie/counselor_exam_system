<template>
  <div class="checkexamstate-page">
    <div class="page-header">
      <div class="header-left">
        <h1>考试监控</h1>
        <p>实时监控考试状态和进度</p>
      </div>
      <div class="header-right">
        <el-button @click="handleRefresh" :loading="listLoading" type="primary">
          <el-icon :size="18"><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="handleBack" class="back-button">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
    </div>

    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-card ongoing">
          <div class="stat-icon">
            <el-icon :size="36"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ ongoingCount }}</div>
            <div class="stat-label">进行中</div>
          </div>
        </div>
        <div class="stat-card pending">
          <div class="stat-icon">
            <el-icon :size="36"><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ pendingCount }}</div>
            <div class="stat-label">未开始</div>
          </div>
        </div>
        <div class="stat-card completed">
          <div class="stat-icon">
            <el-icon :size="36"><Check /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ completedCount }}</div>
            <div class="stat-label">已结束</div>
          </div>
        </div>
        <div class="stat-card total">
          <div class="stat-icon">
            <el-icon :size="36"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ totalCount }}</div>
            <div class="stat-label">总考试数</div>
          </div>
        </div>
      </div>
    </div>

    <div class="filter-section">
      <div class="filter-tabs">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="全部" name="all">
          </el-tab-pane>
          <el-tab-pane label="进行中" name="normal">
          </el-tab-pane>
          <el-tab-pane label="未开始" name="not_started">
          </el-tab-pane>
          <el-tab-pane label="已结束" name="ended">
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <div class="list-section">
      <el-card class="list-card" v-loading="listLoading">
        <div class="list-header">
          <span>考试列表</span>
        </div>
        
        <el-table :data="filteredExams" style="width: 100%" @row-click="viewDetail">
          <el-table-column prop="exam_name" label="考试名称" min-width="200">
            <template #default="{ row }">
              <div class="exam-name">
                <span>{{ row.exam_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="exam_status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.exam_status)">
                {{ getStatusText(row.exam_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="考试时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="时长(分钟)" width="100" />
          <el-table-column prop="total_counselors" label="考生总数" width="100" />
          <el-table-column prop="submitted_count" label="已交卷" width="100">
            <template #default="{ row }">
              <span class="submitted-count">{{ row.submitted_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="graded_count" label="已批改" width="100">
            <template #default="{ row }">
              <span class="graded-count">{{ row.graded_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="进度" width="180">
            <template #default="{ row }">
              <el-progress 
                :percentage="getProgress(row)" 
                :color="getProgressColor(row.exam_status)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click.stop="viewDetail(row)">
                查看详情
              </el-button>
              <el-button
                type="success"
                size="small"
                @click.stop="handlePublish(row)"
                :disabled="row.exam_status !== 'ended'"
              >
                发布成绩
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>

    <el-dialog
      v-model="showDetail"
      :title="selectedExam?.exam_name || '考试详情'"
      width="90%"
      top="5vh"
      :fullscreen="isFullscreen"
    >
      <template #header>
        <div class="dialog-header">
          <span class="dialog-title">{{ selectedExam?.exam_name || '考试详情' }}</span>
          <el-button link @click="toggleFullscreen">
            <el-icon :size="20">
              <FullScreen v-if="!isFullscreen" />
              <Close v-else />
            </el-icon>
          </el-button>
        </div>
      </template>
      <div v-if="selectedExam" class="detail-content-simple">
        <div class="detail-stats-simple">
          <div class="big-stat-card">
            <div class="big-stat-value">{{ selectedExam.total_counselors || 0 }}</div>
            <div class="big-stat-label">考生总数</div>
          </div>
          <div class="big-stat-card submitted">
            <div class="big-stat-value">{{ selectedExam.submitted_count || 0 }}</div>
            <div class="big-stat-label">已交卷</div>
          </div>
          <div class="big-stat-card graded">
            <div class="big-stat-value">{{ selectedExam.graded_count || 0 }}</div>
            <div class="big-stat-label">已批改</div>
          </div>
        </div>

        <!-- 考生状态列表：仅非全屏模式下显示 -->
        <div v-if="!isFullscreen" class="user-status-section">
          <div class="section-header">
            <h3>考生状态列表</h3>
            <div class="filter-controls">
              <el-select
                v-model="userStatusFilter"
                placeholder="筛选状态"
                clearable
                style="width: 140px"
                @change="handleUserFilterChange"
              >
                <el-option label="全部" value="" />
                <el-option label="未开始" value="0" />
                <el-option label="考试中" value="1" />
                <el-option label="已交卷" value="2" />
                <el-option label="异常交卷" value="3" />
              </el-select>
            </div>
          </div>

          <el-table :data="userStatusList" v-loading="userListLoading" border>
            <el-table-column type="index" label="序号" width="60" />
            <el-table-column prop="teacher_gh" label="工号" width="120" />
            <el-table-column prop="teacher_name" label="姓名" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getUserStatusType(row.status)">
                  {{ getUserStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="submit_time" label="交卷时间" width="180">
              <template #default="{ row }">
                {{ row.submit_time || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="obj_score" label="客观题得分" width="110">
              <template #default="{ row }">
                {{ row.obj_score !== null && row.obj_score !== undefined ? row.obj_score : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="subj_score" label="主观题得分" width="110">
              <template #default="{ row }">
                {{ row.subj_score !== null && row.subj_score !== undefined ? row.subj_score : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="total_score" label="总成绩" width="100">
              <template #default="{ row }">
                <span
                  v-if="row.total_score !== null && row.total_score !== undefined"
                  class="total-score"
                >
                  {{ row.total_score }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="userCurrentPage"
              v-model:page-size="userPageSize"
              :page-sizes="[10, 20, 50]"
              :total="userTotalCount"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleUserSizeChange"
              @current-change="handleUserPageChange"
            />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowLeft, Clock, Timer, Check, Document, Refresh, FullScreen, Close } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getExamList } from '@/api/system';
import { getExamUserStatus } from '@/api/exam';
import { publishScores } from '@/api/correct';

const router = useRouter();
const activeTab = ref('all');
const showDetail = ref(false);
const selectedExam = ref(null);
const listLoading = ref(false);
const userListLoading = ref(false);
const isFullscreen = ref(false);

const examList = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const totalCount = ref(0);

const userStatusList = ref([]);
const userCurrentPage = ref(1);
const userPageSize = ref(10);
const userTotalCount = ref(0);
const userStatusFilter = ref('');

const ongoingCount = computed(() => examList.value.filter(e => e.exam_status === 'normal').length);
const pendingCount = computed(() => examList.value.filter(e => e.exam_status === 'not_started').length);
const completedCount = computed(() => examList.value.filter(e => e.exam_status === 'ended' || e.exam_status === 'closed').length);

const filteredExams = computed(() => {
  if (activeTab.value === 'all') return examList.value;
  return examList.value.filter(e => e.exam_status === activeTab.value);
});

onMounted(() => {
  loadExamList();
});

async function loadExamList() {
  listLoading.value = true;
  try {
    const res = await getExamList({ page: currentPage.value, size: pageSize.value });
    console.log('考试列表响应:', res);
    
    if (res && res.list) {
      examList.value = res.list;
      totalCount.value = res.total || 0;
    }
  } catch (error) {
    console.error('加载考试列表失败', error);
    ElMessage.error('加载考试列表失败：' + (error.message || '请检查后端服务'));
  } finally {
    listLoading.value = false;
  }
}

async function loadUserStatusList() {
  if (!selectedExam.value) return;
  
  userListLoading.value = true;
  try {
    const params = {
      page: userCurrentPage.value,
      size: userPageSize.value
    };
    
    if (userStatusFilter.value) {
      params.status = userStatusFilter.value;
    }
    
    const res = await getExamUserStatus(selectedExam.value.exam_id, params);
    console.log('考生状态列表响应:', res);
    
    if (res && res.list) {
      userStatusList.value = res.list;
      userTotalCount.value = res.total || 0;
    }
  } catch (error) {
    console.error('加载考生状态列表失败', error);
    ElMessage.error('加载考生状态列表失败：' + (error.message || '请检查后端服务'));
  } finally {
    userListLoading.value = false;
  }
}

function handleBack() {
  router.push('/super-admin/home');
}

function handleRefresh() {
  loadExamList();
}

async function handlePublish(exam) {
  try {
    await ElMessageBox.confirm(
      `确认发布「${exam.exam_name}」的成绩？发布后不可修改。`,
      '发布成绩',
      { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'warning' }
    );
    const res = await publishScores(exam.exam_id);
    ElMessage.success(res.msg || '发布成功');
    loadExamList();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '发布失败，请重试');
    }
  }
}

function handleTabChange() {
}

function handleSizeChange() {
  currentPage.value = 1;
  loadExamList();
}

function handlePageChange() {
  loadExamList();
}

function handleUserSizeChange() {
  userCurrentPage.value = 1;
  loadUserStatusList();
}

function handleUserPageChange() {
  loadUserStatusList();
}

async function viewDetail(exam) {
  selectedExam.value = exam;
  showDetail.value = true;
  isFullscreen.value = false;
  // 重置考生列表状态并加载
  userStatusFilter.value = '';
  userCurrentPage.value = 1;
  loadUserStatusList();
}

function handleUserFilterChange() {
  userCurrentPage.value = 1;
  loadUserStatusList();
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value;
}

function getStatusType(status) {
  const types = {
    normal: 'warning',
    not_started: 'info',
    ended: 'success',
    closed: 'danger'
  };
  return types[status] || 'default';
}

function getStatusText(status) {
  const texts = {
    normal: '进行中',
    not_started: '未开始',
    ended: '已结束',
    closed: '已关闭'
  };
  return texts[status] || status;
}

function getUserStatusType(status) {
  // 根据接口文档 7.6.5，返回的状态为字符串：not_started / normal / submitted / graded
  const types = {
    not_started: 'info',
    normal: 'warning',
    submitted: '',
    graded: 'success',
  };
  return types[status] || 'default';
}

function getUserStatusText(status) {
  // 根据接口文档 7.6.5 的状态枚举
  const texts = {
    not_started: '未开始',
    normal: '考试中',
    submitted: '已交卷',
    graded: '已批改',
  }
  return texts[status] || status
}

function getProgress(row) {
  if (!row.total_counselors || row.total_counselors === 0) return 0
  return Math.round(((row.submitted_count || 0) / row.total_counselors) * 100)
}

function getProgressColor(status) {
  const colors = {
    normal: '#667eea',
    not_started: '#909399',
    ended: '#67c23a',
    closed: '#f56c6c',
  }
  return colors[status] || '#667eea'
}

function formatDateTime(datetime) {
  if (!datetime) return '-'
  return datetime
}
</script>

<style scoped>
.checkexamstate-page {
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
  display: flex;
  gap: 10px;
}

.back-button {
  padding: 8px 16px;
}

.stats-section {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-card.ongoing .stat-icon {
  background: linear-gradient(135deg, #faad14, #ffc53d);
}

.stat-card.pending .stat-icon {
  background: linear-gradient(135deg, #409eff, #69c0ff);
}

.stat-card.completed .stat-icon {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-card.total .stat-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-tabs {
  background: #fff;
  border-radius: 12px;
  padding: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.list-section {
  margin-bottom: 20px;
}

.list-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.list-header {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.exam-name {
  font-weight: 500;
}

.submitted-count {
  color: #409eff;
  font-weight: 600;
}

.graded-count {
  color: #67c23a;
  font-weight: 600;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.detail-content {
  padding: 10px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 40px;
  margin-bottom: 20px;
}

.detail-info {
  flex: 1;
}

.detail-row {
  display: flex;
  padding: 10px 0;
}

.detail-label {
  width: 100px;
  color: #999;
  font-weight: 500;
}

.detail-stats {
  display: flex;
  gap: 20px;
}

.big-stat-card {
  flex: 1;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
  min-width: 120px;
}

.big-stat-card.submitted {
  background: linear-gradient(135deg, #409eff 0%, #69c0ff 100%);
}

.big-stat-card.graded {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.big-stat-value {
  font-size: 48px;
  font-weight: 700;
  color: #333;
  line-height: 1;
}

.big-stat-card.submitted .big-stat-value,
.big-stat-card.graded .big-stat-value {
  color: #fff;
}

.big-stat-label {
  font-size: 16px;
  color: #666;
  margin-top: 12px;
}

.big-stat-card.submitted .big-stat-label,
.big-stat-card.graded .big-stat-label {
  color: rgba(255, 255, 255, 0.9);
}

.divider {
  height: 1px;
  background: #f0f0f0;
  margin: 20px 0;
}

.user-status-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.filter-controls {
  display: flex;
  gap: 10px;
}

.total-score {
  font-weight: 600;
  color: #67c23a;
}

/* 简化版对话框样式 */
.detail-content-simple {
  padding: 20px 0;
  height: 100%;
}

.detail-stats-simple {
  display: flex;
  justify-content: center;
  gap: 20px;
  height: 100%;
}

.detail-stats-simple .big-stat-card {
  flex: 1;
  padding: 30px 20px;
  border-radius: 12px;
  text-align: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
  min-width: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* 全屏模式下卡片占满整个屏幕 */
:deep(.el-dialog.is-fullscreen) .detail-content-simple {
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-dialog.is-fullscreen) .detail-stats-simple {
  width: 100%;
  height: calc(100vh - 120px);
  gap: 40px;
}

:deep(.el-dialog.is-fullscreen) .detail-stats-simple .big-stat-card {
  min-height: 300px;
}

:deep(.el-dialog.is-fullscreen) .detail-stats-simple .big-stat-value {
  font-size: 120px;
}

:deep(.el-dialog.is-fullscreen) .detail-stats-simple .big-stat-label {
  font-size: 32px;
  margin-top: 30px;
}

.detail-stats-simple .big-stat-card.submitted {
  background: linear-gradient(135deg, #409eff 0%, #69c0ff 100%);
}

.detail-stats-simple .big-stat-card.graded {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.detail-stats-simple .big-stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #333;
  line-height: 1;
}

.detail-stats-simple .big-stat-card.submitted .big-stat-value,
.detail-stats-simple .big-stat-card.graded .big-stat-value {
  color: #fff;
}

.detail-stats-simple .big-stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 10px;
}

.detail-stats-simple .big-stat-card.submitted .big-stat-label,
.detail-stats-simple .big-stat-card.graded .big-stat-label {
  color: rgba(255, 255, 255, 0.9);
}

/* 对话框标题样式 */
.dialog-header {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  position: relative;
}

.dialog-title {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  text-align: center;
}

.dialog-header .el-button {
  position: absolute;
  right: 0;
}

/* 全屏模式下标题更大 */
:deep(.el-dialog.is-fullscreen) .dialog-title {
  font-size: 48px;
}
</style>
