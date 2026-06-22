/** * 辅导员主页面组件 * 采用「顶部导航栏 + 左侧导航栏 + 右侧主内容区」经典后台布局 *
蓝色主色调，简洁清爽风格 */
<template>
  <div class="layout-container">
    <!-- ==================== 顶部导航栏 ==================== -->
    <header class="top-navbar">
      <div class="navbar-left">
        <span class="system-name">辅导员考试系统</span>
      </div>
      <div class="navbar-right">
        <el-dropdown trigger="click" @command="handleUserCommand">
          <div class="user-info">
            <div class="user-avatar">
              <el-icon :size="18"><UserFilled /></el-icon>
            </div>
            <span class="user-name">{{ userName }}</span>
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="layout-body">
      <!-- ==================== 左侧导航栏 ==================== -->
      <aside class="sidebar" :class="{ collapsed: isCollapsed }">
        <!-- 用户信息区 -->
        <div class="sidebar-user">
          <div class="sidebar-avatar">
            <el-icon :size="28"><UserFilled /></el-icon>
          </div>
          <div class="sidebar-user-info" v-show="!isCollapsed">
            <span class="sidebar-username">{{ userName }}</span>
            <span class="sidebar-role">辅导员</span>
          </div>
        </div>

        <!-- 导航菜单 -->
        <nav class="sidebar-menu">
          <!-- 首页 -->
          <div
            class="menu-item"
            :class="{ active: activeMenu === 'home' }"
            @click="switchMenu('home')"
          >
            <el-icon :size="18"><HomeFilled /></el-icon>
            <span v-show="!isCollapsed" class="menu-text">首页</span>
          </div>

          <!-- 日常练习 -->
          <div
            class="menu-item"
            :class="{ active: activeMenu === 'practice' }"
            @click="goToPractice"
          >
            <el-icon :size="18"><EditPen /></el-icon>
            <span v-show="!isCollapsed" class="menu-text">日常练习</span>
          </div>

          <!-- 我的收藏 -->
          <div
            class="menu-item"
            :class="{ active: activeMenu === 'collection' }"
            @click="goToCollection"
          >
            <el-icon :size="18"><StarFilled /></el-icon>
            <span v-show="!isCollapsed" class="menu-text">我的收藏</span>
          </div>

          <!-- 考试中心（可展开子菜单） -->
          <div class="menu-group">
            <div
              class="menu-item"
              :class="{ active: activeMenu === 'exam' }"
              @click="toggleSubMenu('exam')"
            >
              <el-icon :size="18"><Document /></el-icon>
              <span v-show="!isCollapsed" class="menu-text">考试中心</span>
              <el-icon
                v-show="!isCollapsed"
                class="submenu-arrow"
                :class="{ rotated: expandedMenu === 'exam' }"
              >
                <ArrowDown />
              </el-icon>
            </div>
            <div class="submenu" v-show="expandedMenu === 'exam' && !isCollapsed">
              <div
                class="submenu-item"
                :class="{ active: activeMenu === 'exam' && activeSubMenu === 'list' }"
                @click="switchSubMenu('exam', 'list')"
              >
                考试列表
              </div>
            </div>
          </div>

          <!-- 我的成绩（可展开子菜单） -->
          <div class="menu-group">
            <div
              class="menu-item"
              :class="{ active: activeMenu === 'score' }"
              @click="toggleSubMenu('score')"
            >
              <el-icon :size="18"><DataAnalysis /></el-icon>
              <span v-show="!isCollapsed" class="menu-text">我的成绩</span>
              <el-icon
                v-show="!isCollapsed"
                class="submenu-arrow"
                :class="{ rotated: expandedMenu === 'score' }"
              >
                <ArrowDown />
              </el-icon>
            </div>
            <div class="submenu" v-show="expandedMenu === 'score' && !isCollapsed">
              <div
                class="submenu-item"
                :class="{ active: activeMenu === 'score' && activeSubMenu === 'list' }"
                @click="switchSubMenu('score', 'list')"
              >
                成绩列表
              </div>
            </div>
          </div>
        </nav>

        <!-- 折叠按钮 -->
        <div class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <el-icon :size="16">
            <DArrowLeft v-if="!isCollapsed" />
            <DArrowRight v-else />
          </el-icon>
        </div>
      </aside>

      <!-- ==================== 右侧主内容区 ==================== -->
      <main class="main-content">
        <!-- 首页仪表盘 -->
        <Dashboard
          v-show="activeMenu === 'home'"
          :user-name="userName"
          :exam-list="sortedExamList"
          :exam-scores="examScores"
          @navigate="handleDashboardNavigate"
          @enter-exam="enterExam"
        />

        <!-- 考试列表 -->
        <div class="info-card" v-show="activeMenu === 'exam'">
          <h2 class="card-title">考试信息</h2>
          <div v-if="loading" class="loading-container">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <p>加载考试列表中...</p>
          </div>
          <table v-else class="info-table">
            <thead>
              <tr>
                <th>考试编号</th>
                <th>考试名称</th>
                <th>考试开始时间</th>
                <th>考试状态</th>
                <th>成绩</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="exam in processedExamList" :key="exam.id">
                <td>{{ exam.id }}</td>
                <td>{{ exam.name }}</td>
                <td>{{ exam.time || '未知' }}</td>
                <td>{{ exam.status }}</td>
                <td>
                  <span :class="exam.hasScore ? 'score-value' : 'score-pending'">
                    {{ exam.score || '未参加' }}
                  </span>
                </td>
                <td v-if="canEnterExam(exam)">
                  <a href="#" class="action-link" @click.prevent="enterExam(exam.id)">进入考试</a>
                </td>
                <td v-else></td>
              </tr>
              <tr v-if="processedExamList.length === 0">
                <td colspan="6" class="empty-message">暂无考试信息</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 我的成绩 -->
        <div class="info-card" v-show="activeMenu === 'score' && !scoreDetailExamId">
          <h2 class="card-title">我的成绩</h2>
          <div v-if="scoreLoading" class="loading-container">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <p>加载成绩列表中...</p>
          </div>
          <table v-else class="info-table">
            <thead>
              <tr>
                <th>考试名称</th>
                <th>总分</th>
                <th>客观分</th>
                <th>主观分</th>
                <th>批改状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in scoreList" :key="item.examId">
                <td>{{ item.examTitle }}</td>
                <td>
                  <span :class="item.hasScore ? 'score-value' : 'score-pending'">
                    {{ item.totalScore }}
                  </span>
                </td>
                <td>{{ item.objectiveScore }}</td>
                <td>{{ item.subjectiveScore }}</td>
                <td>
                  <span :class="item.hasScore ? 'status-done' : 'status-pending'">
                    {{ item.hasScore ? '已批改' : '待批改' }}
                  </span>
                </td>
                <td>
                  <a
                    v-if="item.hasScore"
                    href="#"
                    class="action-link"
                    @click.prevent="viewScoreDetail(item)"
                    >查看详情</a
                  >
                  <span v-else class="no-action">-</span>
                </td>
              </tr>
              <tr v-if="scoreList.length === 0">
                <td colspan="6" class="empty-message">您还没有参加任何考试</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 成绩详情 -->
        <ScoreDetail
          v-if="scoreDetailExamId"
          :exam-id="scoreDetailExamId"
          :exam-title="scoreDetailExamTitle"
          @back="closeScoreDetail"
        />
      </main>
    </div>
  </div>
</template>

<script setup>
/**
 * 辅导员主页面逻辑
 * 管理顶部导航、侧边栏菜单、内容区切换
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Loading,
  UserFilled,
  ArrowDown,
  HomeFilled,
  EditPen,
  StarFilled,
  Document,
  DataAnalysis,
  DArrowLeft,
  DArrowRight,
} from '@element-plus/icons-vue'
import { getExamList, getExamDetail, getMyScore } from '@/api/exam'
import Dashboard from './Dashboard.vue'
import ScoreDetail from './ScoreDetail.vue'

const router = useRouter()

// ==================== 状态 ====================
const activeMenu = ref('home') // 当前激活菜单，默认首页
const activeSubMenu = ref('list') // 当前激活子菜单
const expandedMenu = ref('') // 当前展开的菜单组
const isCollapsed = ref(false) // 侧边栏折叠状态
const loading = ref(false) // 考试列表加载状态
const scoreLoading = ref(false) // 成绩加载状态
const scoreDetailExamId = ref(null) // 成绩详情-考试ID
const scoreDetailExamTitle = ref('') // 成绩详情-考试名称

// ==================== 数据 ====================
const examList = ref([])
const examScores = ref({})

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

// ==================== 考试状态映射 ====================
const statusMap = {
  not_started: '未开始',
  normal: '进行中',
  ended: '已结束',
  closed: '已关闭',
  submitted: '已提交',
}

// ==================== 计算属性 ====================
// 按规则排序的考试列表：还没考的优先，越晚发布的越在上面
const sortedExamList = computed(() => {
  return [...examList.value].sort((a, b) => {
    // 判断是否是还没考的考试（未开始或进行中）
    const aIsUnfinished = a.exam_status === 'not_started' || a.exam_status === 'normal'
    const bIsUnfinished = b.exam_status === 'not_started' || b.exam_status === 'normal'
    // 还没考的优先排在前面
    if (aIsUnfinished && !bIsUnfinished) return -1
    if (!aIsUnfinished && bIsUnfinished) return 1
    // 同为未考或同为己考，按发布顺序降序（越晚发的越在上面）
    // 用 exam_id 作为发布顺序的代理（ID越大越晚发布）
    const aId = a.exam_id || a.id || 0
    const bId = b.exam_id || b.id || 0
    return bId - aId
  })
})

const processedExamList = computed(() => {
  return sortedExamList.value.map((exam) => {
    const examId = getExamId(exam)
    const scoreData = examScores.value[examId] || {}
    const hasScore = scoreData.score !== undefined && scoreData.score !== null

    return {
      ...exam,
      id: exam.exam_id,
      name: exam.exam_name,
      status: statusMap[exam.exam_status] || exam.exam_status,
      time: exam.start_time || exam.time || '未知',
      score: hasScore ? scoreData.score : undefined,
      hasScore: hasScore,
    }
  })
})

// 获取考试ID的统一方法
function getExamId(exam) {
  return exam.exam_id !== undefined ? exam.exam_id : exam.id
}

const participatedExams = computed(() => {
  return examList.value.filter((exam) => {
    const examId = getExamId(exam)
    // 检查是否有参加标记或成绩数据
    if (exam.hasParticipated || exam.has_participated) return true
    if (examScores.value[examId]) return true
    return false
  })
})

const scoreList = computed(() => {
  return participatedExams.value.map((exam) => {
    const examId = getExamId(exam)
    const scoreData = examScores.value[examId] || {}

    // 确定是否有成绩
    const hasScore = scoreData.score !== undefined && scoreData.score !== null

    return {
      examId: examId,
      paperId: scoreData.paper_id || exam.paperId || exam.paper_id, // 试卷ID，优先使用成绩接口返回的
      examTitle: exam.exam_name || exam.title || exam.name || '未知考试',
      totalScore: hasScore ? scoreData.score : '待批改',
      objectiveScore:
        hasScore && scoreData.objective_score !== undefined ? scoreData.objective_score : '-',
      subjectiveScore:
        hasScore && scoreData.subjective_score !== undefined ? scoreData.subjective_score : '-',
      hasScore: hasScore,
    }
  })
})

// ==================== 生命周期 ====================
onMounted(async () => {
  loading.value = true
  try {
    const response = await getExamList()
    console.log('ExamStatus 考试列表返回:', response)
    if (response.code === 200 && response.list) {
      examList.value = response.list
    } else if (response.data) {
      examList.value = Array.isArray(response.data) ? response.data : response.data.list || []
    } else if (response.list) {
      examList.value = response.list
    } else if (Array.isArray(response)) {
      examList.value = response
    }
    console.log('ExamStatus 解析后的考试列表:', examList.value)
    // 调用考试详情API获取每个考试的时间信息
    await loadExamDetails()
    // 同时加载成绩数据，用于首页最近考试和考试列表显示
    await loadScores()
  } catch (error) {
    console.error('获取考试列表失败', error)
    ElMessage.error('获取考试列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
})

/**
 * 加载每个考试的详情信息（获取start_time、end_time等）
 */
async function loadExamDetails() {
  for (const exam of examList.value) {
    const examId = exam.exam_id || exam.id
    try {
      const detailRes = await getExamDetail(examId)
      if (detailRes && detailRes.data) {
        exam.start_time = detailRes.data.start_time || exam.start_time
        exam.end_time = detailRes.data.end_time || exam.end_time
        exam.duration = detailRes.data.duration || exam.duration
      } else if (detailRes && detailRes.start_time) {
        exam.start_time = detailRes.start_time || exam.start_time
        exam.end_time = detailRes.end_time || exam.end_time
        exam.duration = detailRes.duration || exam.duration
      }
    } catch {
      // 详情获取失败，使用列表中的原始数据
    }
  }
}

// ==================== 菜单操作 ====================
function switchMenu(menu) {
  activeMenu.value = menu
}

function toggleSubMenu(menu) {
  if (expandedMenu.value === menu) {
    expandedMenu.value = ''
  } else {
    expandedMenu.value = menu
    activeMenu.value = menu
    activeSubMenu.value = 'list'
    if (menu === 'score') {
      loadScores()
    }
  }
}

function switchSubMenu(menu, subMenu) {
  activeMenu.value = menu
  activeSubMenu.value = subMenu
  if (menu === 'score') {
    loadScores()
  }
}

// ==================== 仪表盘导航 ====================
function handleDashboardNavigate(target) {
  if (target === 'practice') {
    goToPractice()
  } else if (target === 'collection') {
    goToCollection()
  } else if (target === 'exam') {
    expandedMenu.value = 'exam'
    activeMenu.value = 'exam'
    activeSubMenu.value = 'list'
  } else if (target === 'score') {
    expandedMenu.value = 'score'
    activeMenu.value = 'score'
    activeSubMenu.value = 'list'
    loadScores()
  }
}

// ==================== 成绩加载 ====================
async function loadScores() {
  scoreLoading.value = true
  // 清空之前的成绩数据，重新加载
  examScores.value = {}

  try {
    for (const exam of examList.value) {
      const examId = exam.exam_id || exam.id

      try {
        const scoreRes = await getMyScore(examId, { silent: true })

        // 处理多种响应格式
        const data = scoreRes.data || scoreRes

        // 检查是否有成绩数据
        if (data.score !== undefined && data.score !== null) {
          examScores.value[examId] = {
            score: data.score,
            objective_score: data.objective_score,
            subjective_score: data.subjective_score,
            paper_id: data.paper_id, // 试卷ID，用于查看详情
          }
        } else if (data.total_score !== undefined) {
          // 兼容 total_score 字段名
          examScores.value[examId] = {
            score: data.total_score,
            objective_score: data.objective_score,
            subjective_score: data.subjective_score,
            paper_id: data.paper_id, // 试卷ID，用于查看详情
          }
        }
      } catch {
        // 未参加或未批改，跳过
      }
    }
  } catch (error) {
    console.error('加载成绩失败', error)
  } finally {
    scoreLoading.value = false
  }
}

// ==================== 页面跳转 ====================
function goToPractice() {
  activeMenu.value = 'practice'
  ElMessageBox.alert('日常练习功能即将上线，敬请期待！', '提示', {
    confirmButtonText: '知道了',
    type: 'info',
  }).finally(() => {
    activeMenu.value = 'home'
  })
}

function goToCollection() {
  activeMenu.value = 'collection'
  ElMessageBox.alert('收藏功能即将上线，敬请期待！', '提示', {
    confirmButtonText: '知道了',
    type: 'info',
  }).finally(() => {
    activeMenu.value = 'home'
  })
}

function enterExam(examId) {
  router.push(`/exam-waiting?examId=${examId}`)
}

/**
 * 判断是否可以进入考试
 * 进行中可直接进入；未开始的考试提前10分钟可入场等待
 * @param {Object} exam - 考试对象（processedExamList 中的项）
 * @returns {boolean} 是否可以进入
 */
function canEnterExam(exam) {
  // 进行中的考试可以直接进入
  if (exam.exam_status === 'normal') {
    return true
  }
  // 未开始的考试，检查是否在考前10分钟内
  if (exam.exam_status === 'not_started' && exam.start_time) {
    const startTimestamp = new Date(exam.start_time).getTime() // 考试开始时间戳（毫秒）
    const now = Date.now() // 当前时间戳
    const tenMinutesMs = 10 * 60 * 1000 // 10分钟的毫秒数
    // 当前时间在 [开始前10分钟, 开始时间) 范围内
    return now >= startTimestamp - tenMinutesMs && now < startTimestamp
  }
  return false
}

function viewScoreDetail(item) {
  // 切换到成绩详情视图，传递 paperId（试卷ID）
  scoreDetailExamId.value = item.paperId
  scoreDetailExamTitle.value = item.examTitle
}

/**
 * 关闭成绩详情，返回成绩列表
 */
function closeScoreDetail() {
  scoreDetailExamId.value = null
  scoreDetailExamTitle.value = ''
}

// ==================== 用户操作 ====================
function handleUserCommand(command) {
  if (command === 'logout') {
    handleLogout()
  }
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      ElMessage.success('退出登录成功')
      router.push('/login')
    })
    .catch(() => {})
}
</script>

<style scoped>
/**
 * 辅导员主页面样式
 * 蓝色主色调 + 浅灰/白色辅助
 */

/* ==================== 整体布局 ==================== */
.layout-container {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.layout-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ==================== 顶部导航栏 ==================== */
.top-navbar {
  height: 56px;
  background: linear-gradient(135deg, #409eff, #2b6cb0);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.system-name {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1px;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.15);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.user-name {
  font-size: 14px;
  color: #fff;
}

.dropdown-arrow {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

/* ==================== 左侧导航栏 ==================== */
.sidebar {
  width: 220px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
  border-right: 1px solid #e8eaed;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

/* 用户信息区 */
.sidebar-user {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px 16px;
  border-bottom: 1px solid #e8eaed;
}

.sidebar-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #d9e8f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
  margin-bottom: 10px;
}

.sidebar-user-info {
  text-align: center;
}

.sidebar-username {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.sidebar-role {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

/* 导航菜单 */
.sidebar-menu {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
  transition: all 0.2s ease;
  position: relative;
}

.sidebar.collapsed .menu-item {
  justify-content: center;
  padding: 12px 0;
}

.menu-item:hover {
  background: #e8eaed;
  color: #409eff;
}

.menu-item.active {
  background: #e8f4fd;
  color: #409eff;
  font-weight: 600;
}

.menu-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #409eff;
  border-radius: 0 2px 2px 0;
}

.menu-text {
  flex: 1;
}

.submenu-arrow {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.submenu-arrow.rotated {
  transform: rotate(180deg);
}

/* 子菜单 */
.submenu {
  background: #fafbfc;
}

.submenu-item {
  padding: 10px 20px 10px 52px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submenu-item:hover {
  color: #409eff;
  background: #f0f4f8;
}

.submenu-item.active {
  color: #409eff;
  font-weight: 500;
}

/* 折叠按钮 */
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px;
  border-top: 1px solid #e8eaed;
  cursor: pointer;
  color: #909399;
  transition: color 0.2s;
}

.collapse-btn:hover {
  color: #409eff;
}

/* ==================== 右侧主内容区 ==================== */
.main-content {
  flex: 1;
  padding: 24px;
  background: #f0f2f5;
  overflow-y: auto;
}

/* 信息卡片 */
.info-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

/* 加载状态 */
.loading-container {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.loading-icon {
  font-size: 32px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 信息表格 */
.info-table {
  width: 100%;
  border-collapse: collapse;
}

.info-table th {
  background: #f5f7fa;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #606266;
  font-size: 14px;
  border-bottom: 2px solid #ebeef5;
}

.info-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  font-size: 14px;
  color: #303133;
}

.info-table tr:hover {
  background: #f5f7fa;
}

.empty-message {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}

.action-link {
  color: #409eff;
  text-decoration: none;
  cursor: pointer;
}

.action-link:hover {
  color: #66b1ff;
}

/* 成绩相关样式 */
.score-value {
  font-weight: 600;
  color: #67c23a;
}

.score-pending {
  color: #c0c4cc;
}

.status-done {
  color: #67c23a;
}

.status-pending {
  color: #e6a23c;
}

.no-action {
  color: #c0c4cc;
}
</style>
