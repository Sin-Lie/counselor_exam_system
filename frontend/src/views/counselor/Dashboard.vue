/** * 首页仪表盘组件 * 显示欢迎横幅、功能模块和最近考试 */
<template>
  <div class="dashboard">
    <!-- ==================== 欢迎横幅 ==================== -->
    <div class="welcome-banner">
      <div class="welcome-left">
        <h1 class="welcome-title">欢迎回来，{{ userName }}！</h1>
        <p class="welcome-subtitle">今天是学习的一天，让我们开始练习吧</p>
      </div>
      <div class="welcome-right">
        <el-icon class="calendar-icon"><Calendar /></el-icon>
        <span class="date-text">{{ currentDate }}</span>
      </div>
    </div>

    <!-- ==================== 功能模块区 ==================== -->
    <div class="section-title">功能模块</div>
    <div class="function-cards">
      <div class="func-card" @click="$emit('navigate', 'practice')">
        <div class="func-icon practice-icon">
          <el-icon :size="28"><EditPen /></el-icon>
        </div>
        <div class="func-info">
          <h3 class="func-name">日常练习</h3>
          <p class="func-desc">随机抽题，巩固知识</p>
        </div>
      </div>
      <div class="func-card" @click="$emit('navigate', 'collection')">
        <div class="func-icon collection-icon">
          <el-icon :size="28"><StarFilled /></el-icon>
        </div>
        <div class="func-info">
          <h3 class="func-name">我的收藏</h3>
          <p class="func-desc">收藏错题，反复练习</p>
        </div>
      </div>
      <div class="func-card" @click="$emit('navigate', 'exam')">
        <div class="func-icon exam-icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="func-info">
          <h3 class="func-name">考试中心</h3>
          <p class="func-desc">参加考试，检验学习成果</p>
        </div>
      </div>
      <div class="func-card" @click="$emit('navigate', 'score')">
        <div class="func-icon score-icon">
          <el-icon :size="28"><DataAnalysis /></el-icon>
        </div>
        <div class="func-info">
          <h3 class="func-name">我的成绩</h3>
          <p class="func-desc">查看成绩，分析进步</p>
        </div>
      </div>
    </div>

    <!-- ==================== 最近考试模块 ==================== -->
    <div class="recent-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span class="header-title">最近考试</span>
            <el-button type="text" @click="$emit('navigate', 'exam')">查看全部</el-button>
          </div>
        </template>
        <el-table :data="recentExams" style="width: 100%">
          <el-table-column prop="title" label="考试名称" />
          <el-table-column prop="score" label="成绩" width="100">
            <template #default="{ row }">
              <el-tag :type="getScoreTagType(row.score)">{{ row.score || '待评分' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">{{ row.statusText }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="examTime" label="考试时间" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                v-if="canEnterDashboardExam(row)"
                type="primary"
                size="small"
                @click="$emit('enterExam', row.examId)"
              >
                进入考试
              </el-button>
              <span v-else class="no-action">-</span>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="recentExams.length === 0" description="暂无考试记录" />
      </el-card>
    </div>
  </div>
</template>

<script setup>
/**
 * 首页仪表盘逻辑
 * 展示用户概览信息和快捷入口
 */
import { computed } from 'vue'
import { EditPen, StarFilled, Document, DataAnalysis, Calendar } from '@element-plus/icons-vue'

const props = defineProps({
  userName: { type: String, default: '辅导员' },
  examList: { type: Array, default: () => [] },
  examScores: { type: Object, default: () => ({}) },
})

defineEmits(['navigate', 'enterExam'])

// ==================== 当前日期 ====================
const currentDate = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']
  const weekDay = weekDays[now.getDay()]
  return `${year}年${month}月${day}日 星期${weekDay}`
})

// ==================== 考试状态映射 ====================
const statusMap = {
  not_started: '未开始',
  normal: '进行中',
  ended: '已结束',
  closed: '已关闭',
  submitted: '已提交',
}

// ==================== 最近考试列表 ====================
const recentExams = computed(() => {
  return props.examList.slice(0, 5).map((exam) => {
    const examId = exam.exam_id || exam.id
    const scoreData = props.examScores[examId] || {}
    const rawStatus = exam.exam_status || exam.status
    return {
      examId: examId, // 添加考试ID，用于进入考试
      title: exam.exam_name || exam.name || '未知考试',
      score: scoreData.score,
      status: rawStatus,
      statusText: statusMap[rawStatus] || rawStatus || '未知',
      examTime: exam.start_time || exam.time || '未知',
    }
  })
})

// ==================== 标签类型判断 ====================
function getScoreTagType(score) {
  if (score === null || score === undefined) return 'info'
  if (score >= 90) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

function getStatusTagType(status) {
  const typeMap = {
    not_started: 'info',
    normal: 'success',
    ended: '',
    closed: 'warning',
    submitted: 'primary',
  }
  return typeMap[status] || 'info'
}

/**
 * 判断仪表盘中的考试是否可以进入
 * 进行中可直接进入；未开始的考试提前10分钟可入场
 * @param {Object} row - recentExams 中的行数据
 * @returns {boolean} 是否可以进入
 */
function canEnterDashboardExam(row) {
  if (row.status === 'normal') {
    return true
  }
  if (row.status === 'not_started' && row.examTime) {
    const startTimestamp = new Date(row.examTime).getTime() // 考试开始时间戳
    const now = Date.now() // 当前时间戳
    const tenMinutesMs = 10 * 60 * 1000 // 10分钟的毫秒数
    return now >= startTimestamp - tenMinutesMs && now < startTimestamp
  }
  return false
}
</script>

<style scoped>
.dashboard {
  padding: 0;
}

/* ==================== 欢迎横幅 ==================== */
.welcome-banner {
  background: linear-gradient(135deg, #409eff, #337ecc);
  border-radius: 12px;
  padding: 32px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  color: #fff;
}

.welcome-left {
  flex: 1;
}

.welcome-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #fff;
}

.welcome-subtitle {
  font-size: 14px;
  margin: 0;
  opacity: 0.85;
  color: #fff;
}

.welcome-right {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  opacity: 0.9;
}

.calendar-icon {
  font-size: 20px;
}

.date-text {
  white-space: nowrap;
}

/* ==================== 区域标题 ==================== */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

/* ==================== 功能模块卡片 ==================== */
.function-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.func-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.func-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.func-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.practice-icon {
  background: #e8f4fd;
  color: #409eff;
}

.collection-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.exam-icon {
  background: #e8f8e8;
  color: #67c23a;
}

.score-icon {
  background: #f0f0f0;
  color: #909399;
}

.func-info {
  flex: 1;
  min-width: 0;
}

.func-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.func-desc {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

/* ==================== 最近考试 ==================== */
.recent-section {
  margin-top: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.no-action {
  color: #c0c4cc;
  font-size: 12px;
}
</style>
