/** * 考试答题页面组件 * 提供考试答题功能 *
采用左窄右宽分栏布局：左侧为考生信息+倒计时+答题卡，右侧为主做题区 */
<template>
  <div class="exam-do-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <div class="loading-text">加载中...</div>
    </div>

    <!-- 考试内容：左窄右宽分栏 -->
    <div v-else-if="questions.length > 0" class="exam-content">
      <!-- ========== 左侧辅助区（窄） ========== -->
      <div class="left-panel">
        <!-- 上方白色框：考生信息 + 倒计时 -->
        <div class="card-info">
          <div class="student-name">{{ userName }}</div>
          <span class="timer-label">剩余时间</span>
          <span class="timer-display" :class="{ warning: timeRemaining <= 300 }">
            {{ formattedTime }}
          </span>
        </div>

        <!-- 下方白色框：答题卡 -->
        <div class="card-answer-sheet">
          <!-- 考试基础信息 -->
          <div class="exam-info-text">共 {{ totalQuestions }} 题 | 总计 {{ totalScore }} 分</div>
          <!-- 题号按钮区：一行五题 -->
          <div class="question-grid">
            <div
              v-for="i in totalQuestions"
              :key="i"
              class="question-num-btn"
              :class="getQuestionBtnClass(i)"
              @click="goToQuestion(i)"
            >
              {{ i }}
            </div>
          </div>
          <!-- 底部交卷按钮 -->
          <button class="btn-submit-card" @click="submitExam">交卷</button>
        </div>
      </div>

      <!-- ========== 右侧主做题区（宽） ========== -->
      <div class="right-panel">
        <div class="card-main">
          <!-- 题目内容区 -->
          <div class="question-body">
            <!-- 题目标题栏：左侧题型 + 题目 + 右侧分值 -->
            <div class="question-header">
              <!-- 左侧：题型标签 -->
              <span class="question-type-tag">{{
                getQuestionTypeText(currentQuestionData.question_type)
              }}</span>
              <!-- 中间：题号和题干 -->
              <span class="question-title">
                第 {{ currentQuestion }} 题：{{ currentQuestionData.title || '加载中...' }}
              </span>
              <!-- 右侧：分值 -->
              <span class="question-score">({{ currentQuestionData.score || 0 }}分)</span>
            </div>

            <!-- 选择题选项区域 -->
            <div v-if="currentQuestionData.type !== 'essay'" class="options-list">
              <div
                v-for="option in options"
                :key="option.key"
                class="option-item"
                :class="{ selected: isOptionSelected(option.key) }"
                @click="selectOption(option.key)"
              >
                <span class="option-key">{{ option.key }}</span>
                <!-- 图片选项：使用缓存的 Blob URL 渲染 -->
                <img
                  v-if="isImagePath(option.text)"
                  :src="getOptionImageUrl(option.text, currentQuestionData.question_id, option.key)"
                  class="option-image"
                  alt="选项图片"
                />
                <!-- 文本选项：直接显示 -->
                <span v-else class="option-text">{{ option.text }}</span>
              </div>
            </div>

            <!-- 简答题输入区域 -->
            <div v-else class="essay-area">
              <el-input
                v-model="answers[currentQuestion]"
                type="textarea"
                :rows="6"
                :maxlength="1500"
                placeholder="请在此输入您的答案（最多1500字）..."
                class="essay-input"
                :show-word-limit="false"
              />
              <!-- 字数统计 -->
              <div class="word-count">{{ answers[currentQuestion]?.length || 0 }}/1500</div>
            </div>
          </div>

          <!-- 底部导航操作区 -->
          <div class="bottom-nav">
            <button
              class="btn-prev"
              :class="{ disabled: currentQuestion === 1 }"
              @click="prevQuestion"
            >
              上一题
            </button>
            <button class="btn-save" @click="saveCurrentAnswer">保存答案</button>
            <button class="btn-next" :class="{ disabled: isLastQuestion }" @click="nextQuestion">
              下一题
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-container">
      <el-empty description="暂无考试数据" />
    </div>

    <!-- ========== 交卷结果展示 ========== -->
    <div v-if="hasSubmitted" class="exam-result-overlay">
      <div class="result-card">
        <!-- 完成图标 -->
        <div class="result-icon">
          <el-icon :size="48"><CircleCheckFilled /></el-icon>
        </div>
        <!-- 标题 -->
        <h2 class="result-title">考试结束，交卷成功</h2>
        <!-- 客观题得分 -->
        <div class="result-score-box">
          <div class="score-item">
            <span class="score-label">客观题得分</span>
            <span class="score-value">{{ submissionResult.objective_score ?? '--' }}</span>
            <span class="score-unit">分</span>
          </div>
        </div>
        <!-- 提示文字 -->
        <p class="result-note">主观题答卷已提交，请等待管理员批改后查看完整成绩</p>
        <!-- 返回按钮 -->
        <button class="btn-back" @click="goToExamStatus">返回考试列表</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue' // 引入Vue响应式API和生命周期钩子
import { useRouter, useRoute } from 'vue-router' // 引入Vue Router
import {
  enterExam,
  getExamDetail,
  getSavedAnswers,
  saveAnswer,
  submitExam as submitExamAPI,
} from '@/api/exam' // 引入考试相关API
import { useExamStore } from '@/stores/exam' // 引入考试状态管理
import { ElMessage, ElEmpty, ElIcon, ElMessageBox } from 'element-plus' // 引入Element Plus组件
import { Loading, CircleCheckFilled } from '@element-plus/icons-vue' // 引入Loading图标和勾选图标
import { AntiCheatEngine } from '@/utils/antiCheat' // 引入防作弊引擎

const router = useRouter() // 获取路由导航实例
const route = useRoute() // 获取路由信息
const examStore = useExamStore() // 获取考试状态管理实例

// 考试人姓名（从localStorage获取，与考试状态界面保持一致）
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

// 加载状态
const loading = ref(true)

// 考试数据
const examData = ref(null)
const paperId = ref(null)
const questions = ref([])

// 总题目数
const totalQuestions = computed(() => {
  return questions.value.length
})

const totalScore = computed(function () {
  return questions.value.reduce(function (sum, q) {
    return sum + (q.score || 0)
  }, 0)
})

// 当前题目索引
const currentQuestion = ref(1)

// 用户答案存储
const answers = ref({})

// 不认识的题目
const dontKnowQuestions = ref([])

// 收藏的题目
const collectedQuestions = ref([])

// 当前题目是否已收藏
const isCollected = computed(() => {
  return collectedQuestions.value.includes(currentQuestion.value)
})

// 考试倒计时（秒）
const timeRemaining = ref(0) // 剩余时间（秒）
let timerInterval = null // 定时器引用
let examEndTime = 0 // 考试结束的绝对时间戳（毫秒），用于后台倒计时不中断

// 交卷状态
const hasSubmitted = ref(false) // 是否已交卷
const submissionResult = ref({}) // 交卷结果（包含客观题分数等）

// 格式化时间显示（XX:XX）
const formattedTime = computed(() => {
  const minutes = Math.floor(timeRemaining.value / 60) // 计算分钟数
  const seconds = timeRemaining.value % 60 // 计算秒数
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}` // 格式化为XX:XX
})

// 当前题目数据
const currentQuestionData = computed(() => {
  const raw = questions.value[currentQuestion.value - 1]
  if (!raw) return {}
  return {
    ...raw,
    type: raw.question_type,
    content: raw.title,
    answer: raw.correct_answer,
  }
})

// 选项数据
const options = computed(() => {
  const q = currentQuestionData.value
  if (q && q.options) {
    return Object.entries(q.options).map(([key, text]) => ({
      key,
      text,
    }))
  }
  return []
})

/**
 * 判断选项值是否为图片路径
 * 根据文档规范，以图片扩展名结尾的判定为图片文件路径
 * @param {string} text - 选项文本
 * @returns {boolean} 是否为图片路径
 */
function isImagePath(text) {
  if (!text || typeof text !== 'string') return false // 空值或非字符串
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'] // 图片扩展名列表
  const lowerText = text.toLowerCase() // 转小写比较
  return imageExtensions.some((ext) => lowerText.endsWith(ext)) // 匹配任意图片扩展名
}

/**
 * 获取题型文字描述
 * @param {string} type - 题型英文标识
 * @returns {string} 题型中文名称
 */
function getQuestionTypeText(type) {
  const typeMap = {
    single: '单选题',
    multiple: '多选题',
    multi: '多选题', // 兼容后端返回的 multi 格式
    judge: '判断题',
    blank: '填空题',
    essay: '问答题',
  }
  return typeMap[type] || type || '未知题型'
}

/**
 * 获取选项图片的URL
 * 优先使用预加载缓存的Blob URL，未缓存时拼接后端URL
 * @param {string} path - 图片路径（相对于 media/ 目录）
 * @param {string|number} questionId - 题目ID
 * @param {string} optionKey - 选项键（A/B/C/D）
 * @returns {string} 图片URL
 */
function getOptionImageUrl(path, questionId, optionKey) {
  // 尝试从缓存中获取Blob URL
  const cachedUrl = examStore.getCachedImage(questionId, optionKey)
  if (cachedUrl) {
    return cachedUrl // 返回预加载的Blob URL
  }
  // 未缓存时拼接后端媒体文件URL（兜底方案）
  // 去除路径中可能已存在的 media/ 前缀，避免重复拼接
  let cleanPath = path.replace(/^\/?media\//, '') // 去除开头的 media/ 或 /media/
  return `/media/${cleanPath}` // 直接使用 /media/ 路径，由 Vite 代理转发到后端
}

/**
 * 判断是否为最后一题
 */
const isLastQuestion = computed(() => {
  return currentQuestion.value === totalQuestions.value
})

// 是否为模拟练习模式（根据URL参数判断）
const isPracticeMode = computed(() => {
  return route.query.mode === 'practice'
})

// 防作弊引擎
const antiCheatEngine = ref(null)

function setupAntiCheat() {
  antiCheatEngine.value = new AntiCheatEngine({
    maxLeaveCount: 3, // 最大切屏3次
    examStore: examStore, // 考试状态管理
    paperId: paperId.value, // 当前试卷ID，用于异常上报（避免传null到后端）
    onLeave: (info) => {
      if (info.isFirst) {
        ElMessage.warning('检测到您离开了考试页面，考试期间请勿切屏！')
      } else {
        ElMessage.warning(`检测到您离开了考试页面！剩余 ${info.remaining} 次机会`)
      }
      examStore.reportException('screen_out', `第${info.count}次切屏`)
    },
    onForceSubmit: () => {
      ElMessage.error('切屏次数过多，考试被强制终止！')
      examStore.reportException('screen_out', '切屏次数达到上限，强制交卷')
      submitExamPaperDirectly()
    },
    onDevtoolsOpen: () => {
      console.warn('检测到开发者工具打开')
      examStore.reportException('devtools_open', '检测到开发者工具')
    },
    onWindowResize: (info) => {
      ElMessage.warning('检测到窗口异常缩放，请保持正常考试状态')
      examStore.reportException('abnormal_resize', `窗口从${info.initialWidth}缩放至${info.currentWidth}`)
    },
    onReFocus: () => {
      // 防止多次弹窗叠加
      if (window._antiCheatConfirming) return
      window._antiCheatConfirming = true
      ElMessageBox.confirm('检测到您刚刚离开了考试页面，请确认是本人作答', '身份确认', {
        confirmButtonText: '是本人作答',
        cancelButtonText: '取消',
        type: 'warning',
        closeOnPressEscape: false,
        closeOnClickModal: false,
      }).then(() => {
        window._antiCheatConfirming = false
        ElMessage.success('已确认，请继续作答')
      }).catch(() => {
        window._antiCheatConfirming = false
        ElMessage.warning('请确保是本人作答，此行为已被记录')
        examStore.reportException('screen_out', '切屏返回未确认身份')
      })
    },
    onFullscreenExit: () => {
      ElMessage.warning('请勿退出全屏')
    },
  })
  antiCheatEngine.value.start()
}

// 组件挂载时获取考试数据
onMounted(async () => {
  const examId = route.query.examId
  if (!examId) {
    ElMessage.error('缺少考试ID')
    router.push('/exam-status')
    return
  }

  try {
    // 获取考试详情，包含剩余时间
    const detailResponse = await getExamDetail(examId)
    if (detailResponse.code === 200) {
      examData.value = detailResponse
      // 使用后端返回的剩余时间（秒）
      timeRemaining.value = detailResponse.remaining_time || 0
    }

    // 进入考试，获取试卷数据
    const response = await enterExam(examId)

    if (response.code === 200) {
      paperId.value = response.paper_id
      // 图片预加载已在考前等待页面完成，store 内已做去重，此处不再重复调用
      // 转换字段名以匹配组件期望
      // 兼容 by_student 模式：question_groups 按学生分组，扁平化为统一 questions 数组
      let rawQuestions = []
      if (response.question_groups && response.question_groups.length > 0) {
        rawQuestions = response.question_groups.flatMap(function (group) {
          return group.questions || []
        })
      } else {
        rawQuestions = response.questions || []
      }
      questions.value = rawQuestions.map(function (q) {
        q.type = q.question_type
        q.content = q.title
        return q
      })

      // 恢复已保存的答案
      if (paperId.value) {
        try {
          const savedAnswersResponse = await getSavedAnswers(paperId.value)
          if (savedAnswersResponse.code === 200 && savedAnswersResponse.answers) {
            // 将多选题的字符串答案转换为数组
            const restoredAnswers = {}
            Object.keys(savedAnswersResponse.answers).forEach((key) => {
              const answer = savedAnswersResponse.answers[key]
              const questionIndex = questions.value.findIndex((q) => q.question_id === Number(key))

              // 如果找到对应的题目，使用题目序号（从1开始）作为key
              if (questionIndex !== -1) {
                const questionNumber = questionIndex + 1 // 题目序号从1开始
                const question = questions.value[questionIndex]

                // 多选题答案转换为数组
                if (
                  question &&
                  question.question_type === 'multi' &&
                  typeof answer === 'string' &&
                  answer.includes(',')
                ) {
                  restoredAnswers[questionNumber] = answer.split(',')
                } else {
                  restoredAnswers[questionNumber] = answer
                }
              }
            })
            answers.value = restoredAnswers
            console.log('已恢复保存的答案:', restoredAnswers)
          }
        } catch (error) {
          console.error('获取已保存答案失败', error)
        }
      }

      // 启动计时器
      startTimer()

      // 监听页面可见性变化，切回前台时立即同步倒计时
      document.addEventListener('visibilitychange', handleVisibilitySync)

      // 启动防作弊引擎
      setupAntiCheat()
    } else {
      ElMessage.error(response.msg || '进入考试失败')
      router.push('/exam-status')
    }
  } catch (error) {
    console.error('进入考试失败', error)
    ElMessage.error('进入考试失败，请稍后重试')
    router.push('/exam-status')
  } finally {
    loading.value = false
  }
})

// 启动计时器
function startTimer() {
  // 记录考试结束的绝对时间戳（当前时间 + 剩余秒数），确保后台也能准确倒计时
  examEndTime = Date.now() + timeRemaining.value * 1000

  timerInterval = setInterval(() => {
    // 基于绝对时间戳计算剩余秒数，而非每次减1
    // 这样即使浏览器在后台节流了setInterval，回来后也能正确计算
    const remaining = Math.max(0, Math.ceil((examEndTime - Date.now()) / 1000)) // 向上取整，避免显示为0后还没到时间
    timeRemaining.value = remaining

    if (remaining <= 0) {
      // 时间到，自动提交
      clearInterval(timerInterval) // 清除定时器
      timerInterval = null
      examEndTime = 0
      ElMessage.warning('考试时间已到，系统将自动提交！')
      submitExam(true) // 传入true跳过确认弹窗，直接自动交卷
    }
  }, 500) // 每500ms检查一次，保证显示精度同时减少性能消耗
}

/**
 * 页面可见性变化处理
 * 当用户从后台切回考试页面时，立即同步倒计时
 */
function handleVisibilitySync() {
  if (document.hidden || !examEndTime) return // 页面隐藏或未开始计时，不处理
  const remaining = Math.max(0, Math.ceil((examEndTime - Date.now()) / 1000)) // 基于绝对时间戳重新计算
  timeRemaining.value = remaining
  if (remaining <= 0) {
    // 时间已到，立即触发交卷
    if (timerInterval) {
      clearInterval(timerInterval) // 清除定时器
      timerInterval = null
    }
    examEndTime = 0
    ElMessage.warning('考试时间已到，系统将自动提交！')
    submitExam(true) // 直接交卷
  }
}

/**
 * 获取题目按钮样式类
 * @param {number} index - 题目序号
 * @returns {object} 样式类对象
 */
function getQuestionBtnClass(index) {
  const isCurrent = index === currentQuestion.value
  const hasAnswer =
    answers.value[index] !== undefined &&
    answers.value[index] !== null &&
    answers.value[index] !== ''

  return {
    current: isCurrent, // 当前题目：蓝色高亮
    answered: hasAnswer && !isCurrent, // 已作答：绿色
    unanswered: !hasAnswer && !isCurrent, // 未作答：白色
  }
}

/**
 * 标记为不认识
 */
function markAsDontKnow() {
  const q = currentQuestion.value
  if (!dontKnowQuestions.value.includes(q)) {
    dontKnowQuestions.value.push(q)
  }
  // 显示正确答案
  const correctAnswer = currentQuestionData.value.answer
  ElMessage.info(`正确答案：${correctAnswer}`)
  // 自动标错
  answers.value[q] = 'WRONG'
  // 自动跳转到下一题
  if (!isLastQuestion.value) {
    nextQuestion()
  }
}

/**
 * 切换收藏状态
 */
function toggleCollect() {
  const q = currentQuestion.value
  const index = collectedQuestions.value.indexOf(q)
  if (index > -1) {
    // 取消收藏
    collectedQuestions.value.splice(index, 1)
    ElMessage.info('已取消收藏')
  } else {
    // 添加收藏
    collectedQuestions.value.push(q)
    ElMessage.success('收藏成功')
  }
}

/**
 * 切换到指定题目
 * @param {number} index - 题目序号
 */
function goToQuestion(index) {
  currentQuestion.value = index
}

/**
 * 选择选项
 * @param {string} key - 选项键值
 */
function selectOption(key) {
  const q = currentQuestionData.value
  if (q.type === 'multi') {
    // 多选题：支持多选
    if (!answers.value[currentQuestion.value]) {
      answers.value[currentQuestion.value] = []
    }
    const currentAnswers = answers.value[currentQuestion.value]
    const index = currentAnswers.indexOf(key)
    if (index > -1) {
      // 已选中则取消
      currentAnswers.splice(index, 1)
    } else {
      // 未选中则添加
      currentAnswers.push(key)
    }
    // 触发响应式更新
    answers.value[currentQuestion.value] = [...currentAnswers]
  } else {
    // 单选题：直接替换
    answers.value[currentQuestion.value] = key
  }
}

/**
 * 判断选项是否被选中
 * @param {string} key - 选项键值
 * @returns {boolean} 是否选中
 */
function isOptionSelected(key) {
  const answer = answers.value[currentQuestion.value]
  if (Array.isArray(answer)) {
    // 多选题
    return answer.includes(key)
  }
  // 单选题
  return answer === key
}

/**
 * 收集并批量保存所有已答题目
 * 将本地的 answers 对象转换为接口格式并调用保存API
 * @param {boolean} silent - 是否静默保存（不弹提示），交卷前自动保存时设为 true
 * @returns {Promise<boolean>} 返回保存是否成功
 */
async function collectAndSaveAnswers(silent = false) {
  if (!paperId.value) {
    return false
  }

  // 收集所有已答题目
  const answeredList = []
  for (const [questionNum, answer] of Object.entries(answers.value)) {
    if (answer !== undefined && answer !== null && answer !== '') {
      const questionIndex = Number(questionNum) - 1 // 转换为数组索引
      const question = questions.value[questionIndex]
      if (question && question.question_id) {
        let formattedAnswer = answer
        // 多选题答案转换为逗号分隔字符串（已排序）
        if (question.question_type === 'multi' && Array.isArray(answer)) {
          formattedAnswer = [...answer].sort().join(',')
        }
        answeredList.push({
          question_id: question.question_id,
          user_answer: formattedAnswer,
        })
      }
    }
  }

  // 如果没有已答题目
  if (answeredList.length === 0) {
    if (!silent) {
      ElMessage.warning('请先作答后再保存')
    }
    return false
  }

  try {
    // 使用批量保存接口
    const response = await saveAnswer({
      paper_id: paperId.value,
      answers: answeredList,
      save_time: Date.now(),
      reconnect: false,
    })

    if (response.code === 200) {
      if (!silent) {
        ElMessage.success(`已保存 ${answeredList.length} 道题的答案`)
      }
      return true
    } else if (response.code === 4033) {
      if (!silent) {
        ElMessage.error('考试已交卷，不可保存答案')
      }
      return false
    } else {
      if (!silent) {
        ElMessage.error(response.msg || '保存答案失败')
      }
      return false
    }
  } catch (error) {
    console.error('批量保存答案失败', error)
    if (!silent) {
      ElMessage.error('保存答案失败，请稍后重试')
    }
    return false
  }
}

/**
 * 批量保存所有答案（手动保存按钮触发）
 */
async function saveCurrentAnswer() {
  await collectAndSaveAnswers(false)
}

/**
 * 上一题
 */
function prevQuestion() {
  if (currentQuestion.value > 1) {
    currentQuestion.value--
  }
}

/**
 * 下一题
 */
function nextQuestion() {
  if (!isLastQuestion.value) {
    currentQuestion.value++
  }
}

/**
 * 强制交卷（不弹确认框，直接提交）
 */
async function submitExamPaperDirectly() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
    examEndTime = 0 // 清除结束时间戳
  }

  if (!paperId.value) return

  try {
    await collectAndSaveAnswers(true)
    const response = await submitExamAPI(paperId.value)
    if (response.code === 200) {
      // 交卷成功，停止防作弊引擎并退出全屏
      if (antiCheatEngine.value) {
        antiCheatEngine.value.exitFullscreen() // 先退出全屏
        antiCheatEngine.value.stop() // 再停止所有监控
      }
      hasSubmitted.value = true
      submissionResult.value = {
        objective_score: response.objective_score ?? response.data?.objective_score ?? 0,
      }
    }
  } catch (error) {
    console.error('强制交卷失败，正在恢复监控', error)
    ElMessage.error('交卷失败，请稍后重试')
    // 恢复计时器
    if (!timerInterval) {
      startTimer()
    }
    // 交卷失败，重启防作弊引擎
    if (antiCheatEngine.value) {
      antiCheatEngine.value.reset()
      antiCheatEngine.value.start()
    }
  }
}

/**
 * 提交考试
 * @param {boolean} skipConfirm - 是否跳过确认弹窗（时间到自动交卷时为true）
 */
async function submitExam(skipConfirm) {
  if (skipConfirm === void 0) { skipConfirm = false } // 默认手动交卷需要确认
  try {
    // 手动交卷时弹出确认框，时间到自动交卷时跳过确认
    if (!skipConfirm) {
      await ElMessageBox.confirm('确定要提交试卷吗？提交后将无法修改答案。', '确认交卷', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
    }

    // 清除定时器
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
      examEndTime = 0 // 清除结束时间戳
    }

    if (!paperId.value) {
      ElMessage.error('缺少试卷ID')
      return
    }

    // 交卷前自动保存所有答案
    await collectAndSaveAnswers(true)

    const response = await submitExamAPI(paperId.value)
    if (response.code === 200) {
      // 交卷成功，停止防作弊引擎并退出全屏
      if (antiCheatEngine.value) {
        antiCheatEngine.value.exitFullscreen() // 先退出全屏
        antiCheatEngine.value.stop() // 再停止所有监控
      }

      // 保存交卷结果，包含客观题分数等
      hasSubmitted.value = true
      submissionResult.value = {
        objective_score: response.objective_score ?? response.data?.objective_score ?? 0,
      }
    } else {
      ElMessage.error(response.msg || '提交考试失败')
    }
  } catch (error) {
    // 用户取消提交时不显示错误信息
    if (error !== 'cancel') {
      console.error('提交考试失败', error)
      ElMessage.error('提交考试失败，请稍后重试')
    }
  }
}

/**
 * 返回考试列表
 */
function goToExamStatus() {
  router.push('/exam-status')
}

// 组件卸载时清除计时器
onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  examEndTime = 0 // 清除结束时间戳
  // 移除页面可见性监听
  document.removeEventListener('visibilitychange', handleVisibilitySync)
  // 停止防作弊引擎
  if (antiCheatEngine.value) {
    antiCheatEngine.value.stop()
    antiCheatEngine.value = null
  }

  // 清理缓存的图片 Blob URL，释放浏览器内存
  examStore.cleanupImages()
})
</script>

<style scoped>
/* ==================== 页面整体 ==================== */
.exam-do-page {
  display: flex; /* 弹性布局 */
  width: 100vw; /* 宽度100%视口 */
  height: 100vh; /* 高度100%视口 */
  overflow: hidden; /* 溢出隐藏 */
  position: relative; /* 相对定位 */
  background: #f0f2f5; /* 全局浅灰背景 */
}

/* ==================== 考试内容：左右分栏 ==================== */
.exam-content {
  display: flex; /* 弹性布局，左右排列 */
  width: 100%; /* 宽度100% */
  height: 100%; /* 高度100% */
  padding: 16px; /* 四周留白 */
  gap: 16px; /* 左右面板间距 */
}

/* ==================== 加载状态 ==================== */
.loading-container {
  position: absolute; /* 绝对定位 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0; /* 撑满整个页面 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直方向排列 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  background: rgba(255, 255, 255, 0.9); /* 半透明白色背景 */
  z-index: 1000; /* 层级 */
}

.loading-icon {
  font-size: 48px; /* 图标大小 */
  color: #409eff; /* 图标颜色 */
  animation: spin 1s linear infinite; /* 旋转动画 */
  margin-bottom: 20px; /* 底部外边距 */
}

.loading-text {
  font-size: 18px; /* 字体大小 */
  color: #666; /* 字体颜色 */
  font-weight: bold; /* 字体加粗 */
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  } /* 初始状态 */
  to {
    transform: rotate(360deg);
  } /* 结束状态 */
}

/* 空状态 */
.empty-container {
  position: absolute; /* 绝对定位 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0; /* 撑满 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  background: rgba(255, 255, 255, 0.9); /* 半透明背景 */
}

/* ==================== 左侧辅助区（窄） ==================== */
.left-panel {
  width: 260px; /* 固定宽度 */
  flex-shrink: 0; /* 不缩小 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  gap: 16px; /* 上下卡片间距 */
  height: 100%; /* 高度撑满 */
}

/* ---------- 上部白色框：考生信息 + 倒计时 ---------- */
.card-info {
  background: #ffffff; /* 白色背景 */
  border-radius: 12px; /* 圆角 */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06); /* 细微阴影 */
  padding: 24px 20px; /* 内边距 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  align-items: center; /* 居中 */
}

.student-name {
  font-size: 20px; /* 字号 */
  font-weight: 700; /* 加粗 */
  color: #409eff; /* 蓝色 */
  margin-bottom: 16px; /* 底部间距，增加以替代分割线 */
}

.timer-label {
  font-size: 13px; /* 字号 */
  color: #909399; /* 灰色文字 */
  margin-bottom: 8px; /* 底部间距 */
  font-weight: 500; /* 中等粗细 */
}

.timer-display {
  font-size: 32px; /* 大字显示 */
  font-weight: bold; /* 加粗 */
  color: #409eff; /* 蓝色字体 */
  font-family: 'Courier New', monospace; /* 等宽字体 */
  letter-spacing: 3px; /* 字间距 */
  padding: 12px 20px; /* 添加内边距 */
  background: #ffffff; /* 白色背景 */
  border-radius: 8px; /* 圆角 */
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15); /* 淡蓝色阴影效果 */
}

.timer-display.warning {
  color: #ff4d4f; /* 警告时红色 */
  animation: pulse 0.8s ease-in-out infinite; /* 脉冲动画 */
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.06);
  }
}

/* ---------- 下部白色框：答题卡 ---------- */
.card-answer-sheet {
  background: #ffffff; /* 白色背景 */
  border-radius: 12px; /* 圆角 */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06); /* 细微阴影 */
  padding: 20px 16px 20px 16px; /* 内边距 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  flex: 1; /* 撑满剩余空间 */
  min-height: 0; /* 允许滚动 */
}

/* 考试基础信息 */
.exam-info-text {
  font-size: 13px; /* 字号 */
  color: #909399; /* 灰色文字 */
  text-align: center; /* 居中 */
  margin-bottom: 16px; /* 底部间距 */
  font-weight: 500; /* 中等粗细 */
}

/* 题号网格：一行五题 */
.question-grid {
  display: grid; /* 网格布局 */
  grid-template-columns: repeat(5, 1fr); /* 一行5个 */
  gap: 8px; /* 缩小间距 */
  padding: 0 2px; /* 两侧微调 */
  overflow-y: auto; /* 题多时垂直滚动 */
  flex: 1; /* 占满中间空间 */
  align-content: flex-start; /* 顶部对齐 */
  overflow-x: hidden; /* 禁用水平滚动，避免出现左右滑杆 */
}

/* 题号按钮基础样式 */
.question-num-btn {
  width: 32px; /* 缩小按钮宽度 */
  height: 32px; /* 缩小按钮高度 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  font-size: 12px; /* 缩小字号 */
  font-weight: 500; /* 中等粗细 */
  border-radius: 6px; /* 缩小圆角 */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.2s ease; /* 过渡效果 */
  border: 1.5px solid #e8e8e8; /* 默认灰色边框 */
  background: #ffffff; /* 默认白色背景 */
  color: #606266; /* 默认灰色文字 */
}

/* 当前题目：蓝色高亮 */
.question-num-btn.current {
  background: #409eff; /* 蓝色背景 */
  color: #ffffff; /* 白色文字 */
  border-color: #409eff; /* 蓝色边框 */
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.35); /* 蓝色阴影 */
}

/* 已作答：绿色 */
.question-num-btn.answered {
  background: #67c23a; /* 绿色背景 */
  color: #ffffff; /* 白色文字 */
  border-color: #67c23a; /* 绿色边框 */
}

/* 未作答：白色 */
.question-num-btn.unanswered {
  background: #ffffff; /* 白色背景 */
  color: #606266; /* 灰色文字 */
  border-color: #e0e0e0; /* 浅灰边框 */
}

.question-num-btn:hover {
  transform: scale(1.08); /* 悬停微放大 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12); /* 悬停阴影 */
}

.question-num-btn.current:hover {
  transform: scale(1); /* 当前题悬停不放大 */
}

/* 底部交卷按钮 */
.btn-submit-card {
  margin-top: 16px; /* 顶部间距 */
  width: 100%; /* 撑满宽度 */
  height: 44px; /* 高度 */
  background: #409eff; /* 蓝色背景 */
  border: none; /* 无边框 */
  border-radius: 8px; /* 圆角 */
  font-size: 15px; /* 字号 */
  font-weight: 600; /* 加粗 */
  color: #ffffff; /* 白色文字 */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.25s ease; /* 过渡效果 */
  flex-shrink: 0; /* 不缩小 */
}

.btn-submit-card:hover {
  background: #337ecc; /* 深蓝色 */
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4); /* 阴影 */
}

/* ==================== 右侧主做题区（宽） ==================== */
.right-panel {
  flex: 1; /* 占据剩余空间 */
  height: 100%; /* 高度撑满 */
  min-width: 0; /* 允许收缩 */
}

.card-main {
  background: #ffffff; /* 白色背景 */
  border-radius: 12px; /* 圆角 */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06); /* 细微阴影 */
  padding: 32px 36px 24px 36px; /* 内边距 */
  height: 100%; /* 高度撑满 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
}

/* ==================== 题目内容区 ==================== */
.question-body {
  flex: 1; /* 占据中间空间 */
  overflow-y: auto; /* 内容滚动 */
  padding-right: 4px; /* 滚动条留白 */
}

/* 题目标题栏：左题型 + 中题目 + 右分值 */
.question-header {
  display: flex; /* flex 布局 */
  align-items: flex-start; /* 顶部对齐 */
  margin-bottom: 28px; /* 底部间距 */
  flex-wrap: wrap; /* 换行 */
}

/* 题型标签 */
.question-type-tag {
  background: #409eff; /* 蓝色背景 */
  color: #fff; /* 白色文字 */
  font-size: 12px; /* 字号 */
  font-weight: 600; /* 加粗 */
  padding: 3px 8px; /* 内边距 */
  border-radius: 4px; /* 圆角 */
  flex-shrink: 0; /* 不收缩 */
  margin-top: 2px; /* 顶部微调 */
  margin-right: 10px; /* 与题干的间距 */
}

/* 题目标题文字 */
.question-title {
  font-size: 17px; /* 字号 */
  font-weight: 600; /* 中等加粗 */
  color: #303133; /* 深灰色文字 */
  line-height: 1.8; /* 行高 */
}

/* 题目分值 */
.question-score {
  font-size: 15px; /* 字号 */
  font-weight: 600; /* 加粗 */
  color: #e6a23c; /* 橙色/警告色 */
  flex-shrink: 0; /* 不收缩 */
  margin-left: 8px; /* 紧贴题干右侧 */
}

/* 选项列表区域 */
.options-list {
  display: flex; /* 弹性布局 */
  flex-wrap: wrap; /* 自动换行 */
  gap: 12px; /* 间距 */
  max-width: 800px; /* 最大宽度，增加以容纳两列 */
  width: 100%; /* 宽度100% */
}

/* 选项项 */
.option-item {
  background: #fafbfc; /* 浅灰底色 */
  border: 2px solid #e8e8e8; /* 灰色边框 */
  border-radius: 10px; /* 圆角 */
  padding: 15px 20px; /* 内边距 */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.2s ease; /* 过渡效果 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  gap: 14px; /* 间距 */
  width: calc(50% - 6px); /* 一行显示两个选项，减去一半间距 */
  box-sizing: border-box; /* 盒模型包含内边距和边框 */
}

/* 选中选项：蓝色边框高亮 */
.option-item.selected {
  border-color: #409eff; /* 蓝色边框 */
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f7ff 100%); /* 渐变浅蓝底色 */
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2); /* 蓝色阴影 */
}

.option-item:hover {
  border-color: #409eff; /* 悬停蓝色边框 */
  box-shadow: 0 2px 10px rgba(64, 158, 255, 0.15); /* 悬停阴影 */
}

/* 选项字母圆圈 */
.option-key {
  width: 32px; /* 宽度 */
  height: 32px; /* 高度 */
  background: #eef0f4; /* 浅灰色背景 */
  border-radius: 50%; /* 圆形 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  font-size: 14px; /* 字号 */
  font-weight: bold; /* 加粗 */
  color: #606266; /* 灰色文字 */
  transition: all 0.2s ease; /* 过渡效果 */
  flex-shrink: 0; /* 不缩小 */
}

.option-item.selected .option-key {
  background: #409eff; /* 蓝色背景 */
  color: #ffffff; /* 白色文字 */
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3); /* 蓝色阴影 */
}

/* 选项文字 */
.option-text {
  flex: 1; /* 占据剩余空间 */
  font-size: 15px; /* 字号 */
  color: #303133; /* 深灰色文字 */
  line-height: 1.5; /* 行高 */
}

/* 选项图片 */
.option-image {
  max-width: 100%; /* 最大宽度不超过容器 */
  max-height: 200px; /* 最大高度限制 */
  border-radius: 6px; /* 圆角 */
  border: 1px solid #e8e8e8; /* 边框 */
  object-fit: contain; /* 保持图片原始比例 */
  flex-shrink: 0; /* 不收缩 */
}

/* ==================== 简答题输入区域 ==================== */
.essay-area {
  position: relative; /* 相对定位 */
  margin-bottom: 0; /* 无底部间距 */
}

.essay-input {
  max-width: 1200px; /* 最大宽度 */
  width: 100%; /* 宽度100% */
}

.word-count {
  position: absolute; /* 绝对定位 */
  right: 12px; /* 右侧内边距 */
  bottom: 10px; /* 底部内边距 */
  font-size: 12px; /* 小号字体 */
  color: #909399; /* 浅灰色 */
  pointer-events: none; /* 禁止鼠标事件 */
  z-index: 10; /* 层级 */
}

.essay-input :deep(.el-textarea__inner) {
  font-size: 15px; /* 字号 */
  line-height: 1.8; /* 行高 */
  border-color: #d0d0d0; /* 边框颜色 */
  min-height: 380px; /* 最小高度 */
  padding-right: 80px; /* 右侧留白给字数统计 */
  padding-bottom: 30px; /* 底部留白 */
}

.essay-input :deep(.el-textarea__inner:focus) {
  border-color: #409eff; /* 聚焦蓝色边框 */
}

/* ==================== 底部导航操作区 ==================== */
.bottom-nav {
  display: flex; /* 弹性布局 */
  gap: 16px; /* 按钮间距 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  padding-top: 20px; /* 顶部内边距 */
  border-top: 1px solid #f0f0f0; /* 顶部分隔线 */
  flex-shrink: 0; /* 不缩小 */
}

/* 上一题 / 下一题 / 保存答案 通用按钮样式 */
.btn-prev,
.btn-next,
.btn-save {
  width: 120px; /* 宽度 */
  height: 44px; /* 高度 */
  border-radius: 8px; /* 圆角 */
  font-size: 14px; /* 字号 */
  font-weight: 600; /* 加粗 */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.2s ease; /* 过渡效果 */
  border: 1px solid #dcdfe6; /* 边框 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
}

/* 上一题按钮 */
.btn-prev {
  background: #ffffff; /* 白色背景 */
  color: #606266; /* 灰色文字 */
}

.btn-prev:hover:not(.disabled) {
  border-color: #409eff; /* 悬停蓝色边框 */
  color: #409eff; /* 悬停蓝色文字 */
}

/* 保存答案按钮 */
.btn-save {
  background: #409eff; /* 蓝色背景 */
  color: #ffffff; /* 白色文字 */
  border-color: #409eff; /* 蓝色边框 */
}

.btn-save:hover {
  background: #337ecc; /* 深蓝色 */
  border-color: #337ecc; /* 深蓝色边框 */
}

/* 下一题按钮 */
.btn-next {
  background: #ffffff; /* 白色背景 */
  color: #606266; /* 灰色文字 */
}

.btn-next:hover:not(.disabled) {
  border-color: #409eff; /* 悬停蓝色边框 */
  color: #409eff; /* 悬停蓝色文字 */
}

/* 禁用状态 */
.btn-prev.disabled,
.btn-next.disabled {
  background: #f5f5f5; /* 灰色背景 */
  border-color: #e8e8e8; /* 灰色边框 */
  color: #c0c4cc; /* 浅灰文字 */
  cursor: not-allowed; /* 禁用鼠标 */
}

/* ==================== 交卷结果展示遮罩层 ==================== */
.exam-result-overlay {
  position: fixed; /* 固定定位，覆盖全屏 */
  top: 0;
  left: 0;
  width: 100vw; /* 全屏宽度 */
  height: 100vh; /* 全屏高度 */
  background: rgba(0, 0, 0, 0.45); /* 半透明黑色遮罩 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  z-index: 9999; /* 最高层级 */
}

/* 结果卡片 */
.result-card {
  width: 420px; /* 卡片宽度 */
  background: #ffffff; /* 白色背景 */
  border-radius: 16px; /* 大圆角 */
  padding: 40px 36px 36px 36px; /* 内边距 */
  text-align: center; /* 文字居中 */
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15); /* 卡片阴影 */
}

/* 完成图标 */
.result-icon {
  color: #67c23a; /* 成功绿色 */
  margin-bottom: 16px; /* 底部间距 */
}

/* 标题 */
.result-title {
  font-size: 22px; /* 标题字号 */
  font-weight: 700; /* 加粗 */
  color: #303133; /* 深色文字 */
  margin: 0 0 24px 0; /* 底部间距 */
}

/* 分数展示区 */
.result-score-box {
  background: #f0f9eb; /* 浅绿色背景 */
  border-radius: 12px; /* 圆角 */
  padding: 24px 20px; /* 内边距 */
  margin-bottom: 20px; /* 底部间距 */
}

/* 单条分数 */
.score-item {
  display: flex; /* 弹性布局 */
  align-items: baseline; /* 基线对齐 */
  justify-content: center; /* 水平居中 */
  gap: 8px; /* 间距 */
}

/* 分数标签 */
.score-label {
  font-size: 15px; /* 字号 */
  color: #606266; /* 灰色 */
}

/* 分数数值 */
.score-value {
  font-size: 42px; /* 大号数字 */
  font-weight: 800; /* 超粗 */
  color: #67c23a; /* 成功绿色 */
  line-height: 1; /* 紧凑行高 */
}

/* 分数单位 */
.score-unit {
  font-size: 16px; /* 字号 */
  color: #67c23a; /* 成功绿色 */
  font-weight: 600; /* 加粗 */
}

/* 提示文字 */
.result-note {
  font-size: 13px; /* 小号文字 */
  color: #909399; /* 浅灰 */
  margin: 0 0 24px 0; /* 底部间距 */
  line-height: 1.6; /* 行高 */
}

/* 返回按钮 */
.btn-back {
  width: 100%; /* 全宽 */
  height: 44px; /* 高度 */
  background: #409eff; /* Element Plus 蓝色 */
  color: #ffffff; /* 白色文字 */
  border: none; /* 无边框 */
  border-radius: 8px; /* 圆角 */
  font-size: 15px; /* 字号 */
  font-weight: 600; /* 加粗 */
  cursor: pointer; /* 鼠标指针 */
  transition: background 0.2s ease; /* 过渡动画 */
}

.btn-back:hover {
  background: #337ecc; /* 悬停深蓝色 */
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 900px) {
  .left-panel {
    width: 220px; /* 小屏幕左侧宽度缩小 */
  }

  .card-main {
    padding: 24px 20px 20px 20px; /* 减小内边距 */
  }
}
</style>
