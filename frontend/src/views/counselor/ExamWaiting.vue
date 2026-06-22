/** * 考前等待页面组件 * 辅导员点击"进入考试"后，在考前10分钟内进入此页面 *
功能：预加载试卷图片、显示考试信息、倒计时等待考试开始 */
<template>
  <div class="exam-waiting-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <div class="loading-text">正在准备考试...</div>
    </div>

    <!-- 等待卡片 -->
    <div v-else class="waiting-card">
      <!-- 顶部图标 -->
      <div class="card-icon">
        <el-icon :size="56"><Clock /></el-icon>
      </div>

      <!-- 标题 -->
      <h2 class="card-title">考前等待</h2>

      <!-- 考生信息区 -->
      <div class="info-section">
        <div class="info-row">
          <span class="info-label">工号</span>
          <span class="info-value">{{ userWorkNo }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">姓名</span>
          <span class="info-value">{{ userName }}</span>
        </div>
      </div>

      <!-- 考试信息区 -->
      <div class="info-section">
        <div class="info-row">
          <span class="info-label">考试名称</span>
          <span class="info-value">{{ examName }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">开始时间</span>
          <span class="info-value">{{ examStartTime }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">结束时间</span>
          <span class="info-value">{{ examEndTime }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">考试时长</span>
          <span class="info-value">{{ examDurationText }}</span>
        </div>
      </div>

      <!-- 倒计时区 -->
      <div class="countdown-section">
        <div class="countdown-label">距离考试开始</div>
        <div class="countdown-timer" :class="{ 'countdown-ready': countdown <= 0 }">
          {{ countdown > 0 ? formattedCountdown : '考试已开始' }}
        </div>
      </div>

      <!-- 图片预加载状态 -->
      <div class="preload-status">
        <span v-if="preloadDone" class="preload-done">
          <el-icon :size="14"><CircleCheckFilled /></el-icon>
          试卷资源已就绪
        </span>
        <span v-else-if="preloading" class="preload-loading">
          <el-icon :size="14" class="rotating"><Loading /></el-icon>
          正在预加载试卷资源...
        </span>
        <span v-else class="preload-pending">
          <el-icon :size="14"><Clock /></el-icon>
          试卷资源将在考试开始后加载
        </span>
      </div>

      <!-- 确认按钮 -->
      <button
        class="btn-confirm"
        :class="{ disabled: !canEnter || entering }"
        :disabled="!canEnter || entering"
        @click="handleConfirm"
      >
        <template v-if="entering">
          <el-icon :size="16" class="rotating" style="margin-right: 6px"><Loading /></el-icon>
          正在进入...
        </template>
        <template v-else> 确认进入考试 </template>
      </button>

      <!-- 未到时间提示 -->
      <div v-if="!canEnter && !loading" class="not-ready-tip">
        <el-icon :size="14"><WarningFilled /></el-icon>
        考试尚未开始，请耐心等待倒计时结束
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 考前等待页面逻辑
 * 预加载试卷图片、展示考试信息、倒计时
 */
import { ref, computed, onMounted, onUnmounted } from 'vue' // 引入Vue响应式API
import { useRouter, useRoute } from 'vue-router' // 引入路由
import { ElMessage } from 'element-plus' // 引入消息提示
import { Loading, Clock, CircleCheckFilled, WarningFilled } from '@element-plus/icons-vue' // 引入图标
import { enterExam, getExamDetail } from '@/api/exam' // 引入考试API
import { useExamStore } from '@/stores/exam' // 引入考试状态管理

const router = useRouter() // 路由导航实例
const route = useRoute() // 路由信息
const examStore = useExamStore() // 考试状态管理实例

// ==================== 页面状态 ====================
const loading = ref(true) // 加载状态
const preloadDone = ref(false) // 图片预加载是否完成
const preloading = ref(false) // 正在预加载图片中
const entering = ref(false) // 正在进入考试状态，防止重复点击
const enterReady = ref(false) // 倒计时结束后再等1秒才开放按钮

// ==================== 考试信息 ====================
const examId = ref(null) // 考试ID
const paperId = ref(null) // 试卷ID
const examName = ref('') // 考试名称
const examStartTime = ref('') // 考试开始时间（格式化字符串）
const examEndTime = ref('') // 考试结束时间（格式化字符串）
const examDurationText = ref('') // 考试时长（格式化）
const examStartTimestamp = ref(0) // 考试开始时间戳（毫秒）

// ==================== 用户信息 ====================
const userName = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    try {
      const info = JSON.parse(userInfo)
      return info.name || info.username || '辅导员'
    } catch {
      return '辅导员'
    }
  }
  return '辅导员'
})

const userWorkNo = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    try {
      const info = JSON.parse(userInfo)
      return info.username || info.workNo || '-'
    } catch {
      return '-'
    }
  }
  return '-'
})

// ==================== 倒计时 ====================
const countdown = ref(0) // 距考试开始的秒数
let countdownTimer = null // 倒计时定时器ID
let readyTimer = null // 延迟开放按钮的定时器ID

// 格式化倒计时显示（时:分:秒）
const formattedCountdown = computed(() => {
  const absSeconds = Math.abs(countdown.value) // 取绝对值
  const hours = Math.floor(absSeconds / 3600) // 小时
  const minutes = Math.floor((absSeconds % 3600) / 60) // 分钟
  const seconds = absSeconds % 60 // 秒
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})

// 是否可以进入考试（倒计时结束）
const canEnter = computed(() => enterReady.value)

// ==================== 格式化函数 ====================
/**
 * 格式化时间字符串为可读格式
 * @param {string} timeStr - YYYY-MM-DD HH:MM:SS 格式的时间字符串
 * @returns {string} 格式化后的时间
 */
function formatTime(timeStr) {
  if (!timeStr) return '-'
  return timeStr
}

/**
 * 格式化分钟数为可读时长
 * @param {number} minutes - 分钟数
 * @returns {string} 格式化后的时长
 */
function formatDuration(minutes) {
  if (!minutes || minutes <= 0) return '-'
  const hours = Math.floor(minutes / 60) // 小时
  const mins = minutes % 60 // 剩余分钟
  if (hours > 0) {
    return `${hours}小时${mins > 0 ? mins + '分钟' : ''}`
  }
  return `${mins}分钟`
}

// ==================== 倒计时逻辑 ====================
/**
 * 启动倒计时
 * 每秒更新一次，倒计时到0时自动停止
 */
function startCountdown() {
  enterReady.value = false // 重置按钮开放状态
  countdownTimer = setInterval(() => {
    const now = Date.now() // 当前时间戳（毫秒）
    const remaining = Math.ceil((examStartTimestamp.value - now) / 1000) // 剩余秒数
    countdown.value = Math.max(0, remaining) // 不显示负数
    // 倒计时归零时停止定时器
    if (remaining <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      // 倒计时结束后再等 1 秒才开放按钮，避免用户误触
      readyTimer = setTimeout(() => {
        enterReady.value = true
      }, 500)
    }
  }, 1000)
}

// ==================== 确认进入考试 ====================
/**
 * 点击确认按钮：调用 enterExam 获取 paper_id、预加载图片、跳转到考试页
 * 仅在倒计时结束后可调用，enterExam API 考试开始前会返回 4032
 */
async function handleConfirm() {
  if (!canEnter.value) {
    ElMessage.warning('未到考试时间，请等待倒计时结束')
    return
  }
  if (entering.value) return // 防止重复点击
  entering.value = true
  try {
    // 如果已有 paperId（onMounted 中已从 getExamDetail 获取），跳过 enterExam
    if (!paperId.value) {
      // 1. 进入考试，获取试卷ID（考试开始后接口才会放行）
      const enterRes = await enterExam(examId.value)
      // 请求拦截器已扁平化，且仅 code === 200 时会 resolve
      paperId.value = enterRes.paper_id
    }
    // 2. 预加载试卷中的图片（store 内已做去重，不会重复请求）
    if (paperId.value) {
      await examStore.preloadExamImages(paperId.value)
    }
    preloadDone.value = true
    // 3. 跳转到考试答题页
    router.push(`/exam-do?examId=${examId.value}`)
  } catch (error) {
    // 响应拦截器会 reject 非 200 的响应（如 4032 未到考试时间）
    // 错误消息已由拦截器统一弹出，此处做兜底处理
    console.error('进入考试失败', error)
  } finally {
    entering.value = false
  }
}

// ==================== 生命周期 ====================
onMounted(async () => {
  // 从路由参数获取考试ID
  examId.value = route.query.examId
  if (!examId.value) {
    ElMessage.error('缺少考试ID，请从考试列表重新进入')
    router.push('/exam-status')
    return
  }

  try {
    // 1. 获取考试详情（包含开始/结束时间和时长）
    const detailRes = await getExamDetail(examId.value)
    // 处理响应拦截器扁平化后的数据
    const detailData = detailRes.data || detailRes
    examName.value = detailData.exam_name || '未知考试'
    examStartTime.value = formatTime(detailData.start_time)
    examEndTime.value = formatTime(detailData.end_time)
    examDurationText.value = formatDuration(detailData.duration)
    // 解析开始时间时间戳
    examStartTimestamp.value = new Date(detailData.start_time).getTime()

    // 2. 计算并启动倒计时
    const now = Date.now()
    countdown.value = Math.max(0, Math.ceil((examStartTimestamp.value - now) / 1000))
    startCountdown()

    // 3. 尝试提前获取试卷ID并预加载图片
    // 如果 getExamDetail 返回了 paper_id，则直接使用它进行预加载
    const detailPaperId = detailData.paper_id // 检查详情响应中是否包含 paper_id
    if (detailPaperId) {
      paperId.value = detailPaperId // 缓存试卷ID
      preloading.value = true // 标记正在预加载中
      await examStore.preloadExamImages(detailPaperId) // 提前预加载图片
      preloading.value = false
      preloadDone.value = true
    } else {
      preloadDone.value = false
    }
  } catch (error) {
    console.error('考前准备失败', error)
    ElMessage.error('考前准备失败，请稍后重试')
    router.push('/exam-status')
    return
  } finally {
    loading.value = false
  }
})

// 组件卸载时清除计时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  if (readyTimer) {
    clearTimeout(readyTimer)
    readyTimer = null
  }
})
</script>

<style scoped>
/* ==================== 页面整体 ==================== */
.exam-waiting-page {
  width: 100vw; /* 全屏宽度 */
  height: 100vh; /* 全屏高度 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  background: linear-gradient(135deg, #e8f4fd 0%, #f0f5ff 100%); /* 淡蓝渐变背景 */
}

/* ==================== 加载状态 ==================== */
.loading-container {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  align-items: center; /* 垂直居中 */
  gap: 16px; /* 间距 */
  color: #606266; /* 灰色文字 */
}

.loading-icon {
  font-size: 40px; /* 加载图标大小 */
  animation: spin 1s linear infinite; /* 旋转动画 */
}

.loading-text {
  font-size: 15px; /* 字号 */
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* ==================== 等待卡片 ==================== */
.waiting-card {
  width: 480px; /* 卡片宽度 */
  background: #ffffff; /* 白色背景 */
  border-radius: 20px; /* 圆角 */
  padding: 44px 40px 36px 40px; /* 内边距 */
  text-align: center; /* 文字居中 */
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.08); /* 阴影 */
}

/* 卡片顶部图标 */
.card-icon {
  color: #409eff; /* Element Plus 蓝色 */
  margin-bottom: 8px; /* 底部间距 */
}

/* 卡片标题 */
.card-title {
  font-size: 24px; /* 标题字号 */
  font-weight: 700; /* 加粗 */
  color: #303133; /* 深色文字 */
  margin: 0 0 28px 0; /* 底部间距 */
}

/* ==================== 信息区 ==================== */
.info-section {
  background: #f5f7fa; /* 浅灰背景 */
  border-radius: 12px; /* 圆角 */
  padding: 16px 20px; /* 内边距 */
  margin-bottom: 16px; /* 底部间距 */
  text-align: left; /* 左对齐 */
}

/* 单行信息 */
.info-row {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  padding: 6px 0; /* 上下内边距 */
}

.info-row + .info-row {
  border-top: 1px solid #ebeef5; /* 行间分隔线 */
}

/* 信息标签 */
.info-label {
  width: 72px; /* 固定宽度 */
  font-size: 14px; /* 字号 */
  color: #909399; /* 浅灰文字 */
  flex-shrink: 0; /* 不缩小 */
}

/* 信息值 */
.info-value {
  font-size: 14px; /* 字号 */
  color: #303133; /* 深色文字 */
  font-weight: 500; /* 中等加粗 */
}

/* ==================== 倒计时区 ==================== */
.countdown-section {
  margin-bottom: 20px; /* 底部间距 */
}

/* 倒计时标签 */
.countdown-label {
  font-size: 13px; /* 小字号 */
  color: #909399; /* 浅灰 */
  margin-bottom: 8px; /* 底部间距 */
}

/* 倒计时计时器 */
.countdown-timer {
  font-size: 48px; /* 大号数字 */
  font-weight: 800; /* 超粗 */
  color: #409eff; /* 蓝色 */
  line-height: 1.2; /* 行高 */
  font-variant-numeric: tabular-nums; /* 等宽数字 */
  letter-spacing: 4px; /* 字符间距 */
}

/* 倒计时结束 */
.countdown-timer.countdown-ready {
  color: #67c23a; /* 绿色 */
}

/* ==================== 预加载状态 ==================== */
.preload-status {
  margin-bottom: 24px; /* 底部间距 */
  font-size: 13px; /* 字号 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  gap: 6px; /* 间距 */
}

.preload-done {
  color: #67c23a; /* 绿色 */
}

.preload-loading {
  color: #409eff; /* 蓝色，加载中 */
}

.preload-pending {
  color: #909399; /* 浅灰 */
}

.rotating {
  animation: spin 1s linear infinite; /* 旋转动画 */
}

/* ==================== 确认按钮 ==================== */
.btn-confirm {
  width: 100%; /* 全宽 */
  height: 48px; /* 高度 */
  background: #409eff; /* 蓝色背景 */
  color: #ffffff; /* 白色文字 */
  border: none; /* 无边框 */
  border-radius: 10px; /* 圆角 */
  font-size: 16px; /* 字号 */
  font-weight: 600; /* 加粗 */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.25s ease; /* 过渡动画 */
}

.btn-confirm:hover:not(.disabled) {
  background: #337ecc; /* 深蓝色 */
  transform: translateY(-2px); /* 上移 */
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.35); /* 阴影 */
}

.btn-confirm.disabled {
  background: #a0cfff; /* 浅蓝色 */
  cursor: not-allowed; /* 禁用鼠标 */
  transform: none; /* 不移动 */
  box-shadow: none; /* 无阴影 */
}

/* ==================== 未到时间提示 ==================== */
.not-ready-tip {
  margin-top: 12px; /* 上边距 */
  font-size: 13px; /* 字号 */
  color: #e6a23c; /* 橙色 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  gap: 6px; /* 间距 */
}
</style>
