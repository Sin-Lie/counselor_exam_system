<template>
  <div class="collection-page">
    <!-- 左侧题目导航栏 -->
    <div class="question-nav">
      <div class="nav-header">
        <h3>收藏题目列表</h3>
        <span class="total-count">共 {{ total }} 题</span>
      </div>
      <div class="question-list">
        <div
          v-for="(item, index) in collectionList"
          :key="item.favorite_id"
          class="question-item"
          :class="{ active: currentIndex === index }"
          @click="selectQuestion(index)"
        >
          <span class="question-number">{{ index + 1 }}</span>
          <span class="student-name">{{ item.student_name }}</span>
          <span class="question-preview">{{ item.question_title.slice(0, 20) }}...</span>
        </div>
        <div v-if="collectionList.length === 0" class="empty-list">
          <p>暂无收藏题目</p>
        </div>
      </div>

      <!-- 分页组件 -->
      <div v-if="total > size" class="pagination-wrapper">
        <el-pagination
          background
          :current-page="page"
          :page-size="size"
          :total="total"
          @current-change="handlePageChange"
          layout="prev, pager, next, jumper"
        />
      </div>
    </div>

    <!-- 右侧题目内容区 -->
    <div class="question-content">
      <!-- 顶部工具栏 -->
      <div class="toolbar">
        <!-- 排序选择 -->
        <el-select v-model="sortType" size="small" @change="loadCollectionList">
          <el-option label="按时间倒序" value="time_desc" />
          <el-option label="按时间正序" value="time_asc" />
        </el-select>
        <el-button type="danger" icon="Delete" @click="handleClearCollection" class="clear-btn">
          一键清空
        </el-button>
        <el-button type="primary" icon="ArrowLeft" @click="handleExit" class="exit-btn">
          退出收藏
        </el-button>
      </div>

      <!-- 题目显示区域 -->
      <div class="question-area" v-if="currentItem">
        <!-- 题目头部 -->
        <div class="question-header">
          <span class="student-tag">{{ currentItem.student_name }}</span>
          <span class="create-time">{{ formatTime(currentItem.create_time) }}</span>
        </div>

        <!-- 题目内容 -->
        <div class="question-body">
          <div class="question-text">{{ currentIndex + 1 }}. {{ currentItem.question_title }}</div>

          <!-- 答案显示区域 -->
          <div class="answer-section" v-if="showAnswer">
            <span class="answer-label">正确答案：</span>
            <span class="answer-value">{{ formatAnswer(currentItem.answer, currentItem.question_type) }}</span>
          </div>

          <!-- 选项列表 -->
          <div class="options-list" v-if="currentItem.options">
            <div
              v-for="option in currentItem.options"
              :key="option.key"
              class="option-item"
              :class="{
                'correct-answer':
                  showAnswer &&
                  isCorrectOption(currentItem.answer, option.key, currentItem.question_type),
              }"
            >
              <span class="option-label">{{ option.key }}.</span>
              <span class="option-content">{{ option.value }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
            type="primary"
            icon="ArrowRight"
            @click="nextQuestion"
            :disabled="currentIndex >= collectionList.length - 1"
            class="next-btn"
          >
            下一题
          </el-button>
          <el-button type="success" icon="Eye" @click="toggleShowAnswer" class="show-answer-btn">
            {{ showAnswer ? '隐藏答案' : '显示答案' }}
          </el-button>
          <el-button
            type="warning"
            icon="StarOff"
            @click="handleRemoveCollection"
            class="remove-btn"
          >
            取消收藏
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-else>
        <div class="empty-icon">
          <el-icon name="Collection" :size="48" />
        </div>
        <p>暂无收藏的题目</p>
        <p class="empty-hint">在练习时点击题目旁的收藏按钮可以收藏题目</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue' // 引入Vue响应式API
import { useRouter } from 'vue-router' // 引入Vue Router
import { ElMessage, ElIcon, ElMessageBox } from 'element-plus' // 引入Element Plus组件
import { getCollectionList, removeCollection, clearCollection } from '@/api/practice' // 引入收藏相关API

const router = useRouter() // 获取路由导航实例

// ==================== 状态定义 ====================
const page = ref(1) // 当前页码
const size = ref(10) // 每页条数
const sortType = ref('time_desc') // 排序类型
const collectionList = ref([]) // 收藏列表
const total = ref(0) // 总条数
const currentIndex = ref(0) // 当前选中的题目索引
const showAnswer = ref(false) // 是否显示答案

// ==================== 计算属性 ====================
// 当前选中的收藏项
const currentItem = computed(() => {
  if (collectionList.value.length > 0) {
    return collectionList.value[currentIndex.value]
  }
  return null
})

// ==================== 方法定义 ====================
/**
 * 加载收藏列表
 */
async function loadCollectionList() {
  try {
    const res = await getCollectionList({
      page: page.value,
      size: size.value,
      sort_type: sortType.value,
    })

    const data = res.data || res
    collectionList.value = data.list || []
    total.value = data.total || 0
    currentIndex.value = 0
    showAnswer.value = false

    // 转换选项格式：从 {A: "选项A", B: "选项B"} 转换为 [{key: "A", value: "选项A"}, ...]
    collectionList.value = collectionList.value.map((item) => ({
      ...item,
      answer: item.correct_answer, // 将 correct_answer 映射为 answer
      options: convertOptions(item.options),
    }))

    console.log('收藏列表数据:', collectionList.value)
  } catch (error) {
    console.error('获取收藏列表失败', error)
    ElMessage.error('获取收藏列表失败')
  }
}

/**
 * 转换选项格式：从 {A: "选项A", B: "选项B"} 转换为 [{key: "A", value: "选项A"}, ...]
 */
function convertOptions(options) {
  if (!options) return []
  if (Array.isArray(options)) return options
  return Object.keys(options).map((key) => ({
    key: key,
    value: String(options[key]),
  }))
}

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

function formatAnswer(answer, questionType) {
  if (questionType !== 'multi' && questionType !== 'multiple') {
    return answer || '暂无答案'
  }
  const answers = normalizeAnswerList(answer)
  return answers.length > 0 ? answers.join('、') : '暂无答案'
}

function isCorrectOption(answer, optionKey, questionType) {
  if (questionType === 'multi' || questionType === 'multiple') {
    return normalizeAnswerList(answer).includes(String(optionKey))
  }
  return String(answer) === String(optionKey)
}

/**
 * 获取模拟答案（实际项目中从题库获取）
 */
function getMockAnswer(item) {
  const answers = ['A', 'B', 'C', 'D', 'AB', 'CD', 'ABCD']
  return answers[Math.floor(Math.random() * answers.length)]
}

/**
 * 获取模拟选项（实际项目中从题库获取）
 */
function getMockOptions(item) {
  const optionSets = [
    [
      { key: 'A', value: '选项A内容' },
      { key: 'B', value: '选项B内容' },
      { key: 'C', value: '选项C内容' },
      { key: 'D', value: '选项D内容' },
    ],
    [
      { key: 'A', value: '临床医学' },
      { key: 'B', value: '儿科学' },
      { key: 'C', value: '儿科学（定向）' },
      { key: 'D', value: '眼视光医学（五年制）' },
    ],
    [
      { key: 'A', value: '学生日常管理' },
      { key: 'B', value: '教学科研' },
      { key: 'C', value: '心理健康辅导' },
      { key: 'D', value: '学业指导' },
    ],
  ]
  return optionSets[Math.floor(Math.random() * optionSets.length)]
}

/**
 * 选择题目
 * @param {number} index - 题目索引
 */
function selectQuestion(index) {
  currentIndex.value = index
  showAnswer.value = false // 切换题目时隐藏答案
}

/**
 * 下一题
 */
function nextQuestion() {
  if (currentIndex.value < collectionList.value.length - 1) {
    currentIndex.value++
    showAnswer.value = false // 切换题目时隐藏答案
  } else {
    // 如果当前页已完成，尝试加载下一页
    if (page.value * size.value < total.value) {
      page.value++
      loadCollectionList()
    }
  }
}

/**
 * 切换答案显示
 */
function toggleShowAnswer() {
  showAnswer.value = !showAnswer.value
}

/**
 * 取消收藏当前题目
 */
async function handleRemoveCollection() {
  if (!currentItem.value) return

  try {
    await removeCollection(currentItem.value.favorite_id)

    // 从本地列表中移除
    const removedItem = collectionList.value[currentIndex.value]
    collectionList.value.splice(currentIndex.value, 1)
    total.value--

    // 如果删除的是最后一题，且还有其他题目，切换到上一题
    if (currentIndex.value >= collectionList.value.length && collectionList.value.length > 0) {
      currentIndex.value = collectionList.value.length - 1
    }

    showAnswer.value = false
    ElMessage.success(`已取消收藏题目：${removedItem.question_title.slice(0, 20)}...`)
  } catch (error) {
    console.error('取消收藏失败', error)
    ElMessage.error('取消收藏失败')
  }
}

/**
 * 退出收藏页面，返回首页
 */
function handleExit() {
  router.push('/exam-status')
}

/**
 * 一键清空收藏夹
 */
async function handleClearCollection() {
  if (collectionList.value.length === 0) {
    ElMessage.info('收藏夹已经是空的')
    return
  }

  try {
    await ElMessageBox.confirm('确定要清空所有收藏的题目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await clearCollection()

    collectionList.value = []
    total.value = 0
    currentIndex.value = 0
    showAnswer.value = false

    ElMessage.success('收藏夹已清空')
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('清空收藏失败', error)
      ElMessage.error('清空收藏失败')
    }
  }
}

/**
 * 格式化时间
 * @param {string} timeStr - 时间字符串
 * @returns {string} 格式化后的时间
 */
function formatTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

/**
 * 分页变化处理
 * @param {number} newPage - 新页码
 */
function handlePageChange(newPage) {
  page.value = newPage
  loadCollectionList()
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadCollectionList()
})
</script>

<style scoped>
/**
 * 收藏夹页面样式
 */
.collection-page {
  display: flex; /* 弹性布局 */
  width: 100vw; /* 宽度100%视口 */
  height: 100vh; /* 高度100%视口 */
  overflow: hidden; /* 溢出隐藏 */
  background: #f5f7fa; /* 淡灰色背景 */
}

/* ==================== 左侧题目导航栏 ==================== */
.question-nav {
  width: 280px; /* 固定宽度280px */
  height: 100vh; /* 高度100%视口 */
  background: white; /* 白色背景 */
  border-right: 1px solid #e0e0e0; /* 右侧边框 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直方向排列 */
}

/* 导航头部 */
.nav-header {
  padding: 20px; /* 内边距20px */
  border-bottom: 1px solid #e0e0e0; /* 底部边框 */
  background: #409eff; /* 蓝色背景 */
  display: flex; /* 弹性布局 */
  justify-content: space-between; /* 左右分散对齐 */
  align-items: center; /* 垂直居中对齐 */
}

.nav-header h3 {
  margin: 0; /* 清除默认外边距 */
  font-size: 16px; /* 字号16px */
  font-weight: bold; /* 加粗 */
  color: white; /* 白色文字 */
}

.total-count {
  font-size: 12px; /* 字号12px */
  color: rgba(255, 255, 255, 0.8); /* 半透明白色 */
  background: rgba(255, 255, 255, 0.2); /* 半透明背景 */
  padding: 4px 10px; /* 内边距 */
  border-radius: 10px; /* 圆角 */
}

/* 题目列表 */
.question-list {
  flex: 1; /* 占据剩余空间 */
  overflow-y: auto; /* 垂直滚动 */
  padding: 10px; /* 内边距10px */
}

/* 题目项 */
.question-item {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  padding: 12px 16px; /* 内边距 */
  margin-bottom: 8px; /* 下方外边距8px */
  background: #f8f9fa; /* 淡灰色背景 */
  border-radius: 6px; /* 圆角6px */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.3s; /* 过渡效果 */
  border-left: 3px solid transparent; /* 左侧边框透明 */
}

.question-item:hover {
  background: #e6f7ff; /* 悬停时浅蓝色背景 */
}

.question-item.active {
  background: #e6f7ff; /* 激活时浅蓝色背景 */
  border-left-color: #409eff; /* 左侧蓝色边框 */
}

/* 题目编号 */
.question-number {
  width: 24px; /* 宽度24px */
  height: 24px; /* 高度24px */
  line-height: 24px; /* 行高24px */
  text-align: center; /* 文本居中 */
  background: #409eff; /* 蓝色背景 */
  color: white; /* 白色文字 */
  border-radius: 50%; /* 圆形 */
  font-size: 12px; /* 字号12px */
  font-weight: bold; /* 加粗 */
  margin-bottom: 8px; /* 下方外边距8px */
}

.question-item.active .question-number {
  background: #67c23a; /* 激活时绿色背景 */
}

/* 学生姓名 */
.student-name {
  font-size: 13px; /* 字号13px */
  color: #409eff; /* 蓝色文字 */
  font-weight: 500; /* 中等粗细 */
  margin-bottom: 4px; /* 下方外边距4px */
}

/* 题目预览 */
.question-preview {
  font-size: 12px; /* 字号12px */
  color: #666; /* 灰色文字 */
  overflow: hidden; /* 溢出隐藏 */
  text-overflow: ellipsis; /* 省略号 */
  white-space: nowrap; /* 不换行 */
}

/* 空列表 */
.empty-list {
  text-align: center; /* 文本居中 */
  padding: 40px 20px; /* 内边距 */
  color: #999; /* 浅灰色文字 */
}

/* 分页组件 */
.pagination-wrapper {
  padding: 10px; /* 内边距10px */
  border-top: 1px solid #e0e0e0; /* 顶部边框 */
}

.pagination-wrapper .el-pagination {
  text-align: center; /* 居中对齐 */
}

/* ==================== 右侧题目内容区 ==================== */
.question-content {
  flex: 1; /* 占据剩余空间 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直方向排列 */
  padding: 20px; /* 内边距20px */
  overflow-y: auto; /* 垂直滚动 */
}

/* 顶部工具栏 */
.toolbar {
  display: flex; /* 弹性布局 */
  justify-content: flex-end; /* 右对齐 */
  align-items: center; /* 垂直居中对齐 */
  gap: 12px; /* 间距12px */
  margin-bottom: 20px; /* 下方外边距20px */
}

/* 一键清空按钮 */
.clear-btn {
  padding: 8px 20px; /* 内边距 */
  font-size: 14px; /* 字号14px */
}

/* 退出按钮 */
.exit-btn {
  padding: 8px 20px; /* 内边距 */
  font-size: 14px; /* 字号14px */
}

/* 题目显示区域 */
.question-area {
  flex: 1; /* 占据剩余空间 */
  background: white; /* 白色背景 */
  border-radius: 8px; /* 圆角8px */
  padding: 30px; /* 内边距30px */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); /* 阴影效果 */
}

/* 题目头部 */
.question-header {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 12px; /* 间距12px */
  margin-bottom: 20px; /* 下方外边距20px */
}

.student-tag {
  display: inline-block; /* 行内块 */
  padding: 4px 12px; /* 内边距 */
  background: #e6f7ff; /* 浅蓝色背景 */
  color: #1890ff; /* 蓝色文字 */
  border-radius: 4px; /* 圆角4px */
  font-size: 12px; /* 字号12px */
  font-weight: bold; /* 加粗 */
}

.create-time {
  font-size: 12px; /* 字号12px */
  color: #999; /* 灰色文字 */
}

/* 题目主体 */
.question-body {
  margin-bottom: 30px; /* 下方外边距30px */
}

/* 题目文本 */
.question-text {
  font-size: 16px; /* 字号16px */
  color: #333; /* 深灰色文字 */
  line-height: 1.8; /* 行高1.8 */
  margin-bottom: 20px; /* 下方外边距20px */
}

/* 答案区域 */
.answer-section {
  display: inline-block; /* 行内块 */
  padding: 10px 20px; /* 内边距 */
  background: #f6ffed; /* 浅绿色背景 */
  border: 1px solid #b7eb8f; /* 绿色边框 */
  border-radius: 4px; /* 圆角4px */
  margin-bottom: 20px; /* 下方外边距20px */
}

.answer-label {
  font-size: 14px; /* 字号14px */
  color: #52c41a; /* 绿色文字 */
  font-weight: bold; /* 加粗 */
}

.answer-value {
  font-size: 16px; /* 字号16px */
  color: #52c41a; /* 绿色文字 */
  font-weight: bold; /* 加粗 */
  margin-left: 5px; /* 左侧外边距5px */
}

/* 选项列表 */
.options-list {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直方向排列 */
  gap: 12px; /* 间距12px */
}

/* 选项项 */
.option-item {
  display: flex; /* 弹性布局 */
  align-items: flex-start; /* 顶部对齐 */
  padding: 12px 16px; /* 内边距 */
  background: #f8f9fa; /* 淡灰色背景 */
  border-radius: 6px; /* 圆角6px */
  transition: all 0.3s; /* 过渡效果 */
}

.option-item:hover {
  background: #e0e0e0; /* 悬停时灰色背景 */
}

.option-item.correct-answer {
  background: #f6ffed; /* 正确答案浅绿色背景 */
  border: 1px solid #b7eb8f; /* 绿色边框 */
}

/* 选项标签 */
.option-label {
  font-size: 14px; /* 字号14px */
  font-weight: bold; /* 加粗 */
  color: #333; /* 深灰色文字 */
  margin-right: 10px; /* 右侧外边距10px */
  min-width: 24px; /* 最小宽度24px */
}

/* 选项内容 */
.option-content {
  font-size: 14px; /* 字号14px */
  color: #333; /* 深灰色文字 */
  line-height: 1.6; /* 行高1.6 */
}

/* 操作按钮 */
.action-buttons {
  display: flex; /* 弹性布局 */
  gap: 12px; /* 间距12px */
  justify-content: center; /* 水平居中 */
  padding-top: 20px; /* 上方内边距20px */
  border-top: 1px solid #e0e0e0; /* 顶部边框 */
}

.action-buttons .el-button {
  padding: 10px 24px; /* 内边距 */
  font-size: 14px; /* 字号14px */
}

/* 空状态 */
.empty-state {
  flex: 1; /* 占据剩余空间 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直方向排列 */
  align-items: center; /* 水平居中 */
  justify-content: center; /* 垂直居中 */
  background: white; /* 白色背景 */
  border-radius: 8px; /* 圆角8px */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); /* 阴影效果 */
}

.empty-icon {
  color: #ccc; /* 灰色图标 */
  margin-bottom: 20px; /* 下方外边距20px */
}

.empty-state p {
  margin: 0 0 10px 0; /* 外边距 */
  font-size: 16px; /* 字号16px */
  color: #666; /* 灰色文字 */
}

.empty-hint {
  font-size: 14px !important; /* 字号14px */
  color: #999 !important; /* 浅灰色文字 */
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 768px) {
  .question-nav {
    width: 200px; /* 小屏幕时宽度200px */
  }

  .question-area {
    padding: 20px; /* 小屏幕时内边距20px */
  }

  .action-buttons {
    flex-direction: column; /* 垂直排列 */
    align-items: stretch; /* 拉伸 */
  }
}
</style>
