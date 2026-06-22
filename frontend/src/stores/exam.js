/**
 * 考试状态管理模块
 * 管理考试进行中的状态，包括答题进度、倒计时、自动保存等
 */
import { defineStore } from 'pinia' // 引入Pinia的defineStore函数，用于定义状态管理
import { ref, computed } from 'vue' // 引入Vue的ref和computed响应式API
import {
  saveAnswer as saveExamAnswerAPI,
  submitExam,
  reportAbnormal,
  preloadImages as preloadImagesAPI,
} from '@/api/exam' // 引入考试相关API接口

/**
 * 考试状态管理Store
 * 管理考试进行时的各种状态和数据
 */
export const useExamStore = defineStore('exam', () => {
  // ==================== 考试信息状态 ====================
  // 当前考试ID
  const currentExamId = ref(null) // 当前进行中的考试ID
  // 当前试卷ID
  const currentPaperId = ref(null) // 当前试卷的ID
  // 考试开始时间
  const examStartTime = ref(null) // 考试开始的绝对时间戳
  // 考试时长（分钟）
  const examDuration = ref(0) // 考试设定的总时长
  // 考试剩余时间（秒）
  const remainingTime = ref(0) // 考试剩余的倒计时秒数
  // 定时器引用
  let timerInterval = null // 倒计时定时器ID

  // ==================== 答题状态 ====================
  // 答题记录Map，key为题目ID，value为用户答案
  const answers = ref(new Map()) // 使用Map存储答题记录，便于快速查找和更新
  // 已答题目ID列表
  const answeredQuestions = ref([]) // 已作答的题目ID数组
  // 当前题目索引
  const currentQuestionIndex = ref(0) // 当前正在作答的题目索引
  // 题目列表
  const questions = ref([]) // 试卷包含的题目列表

  // ==================== 图片缓存 ====================
  // 图片缓存Map，key为 "questionId_optionKey"，value为 Blob URL
  const examImages = ref(new Map()) // 缓存考试题目中的图片 Blob URL，考试结束后释放
  // 已预加载的试卷ID集合，避免重复请求预加载接口
  const preloadedPaperIds = ref(new Set()) // 记录已完成预加载的试卷ID

  // ==================== 考试状态标志 ====================
  // 是否正在考试
  const isExamining = ref(false) // 标记当前是否处于考试状态
  // 是否已交卷
  const isSubmitted = ref(false) // 标记是否已提交试卷
  // 是否全屏模式
  const isFullScreen = ref(false) // 标记当前是否正在全屏模式
  // 自动保存状态
  const isAutoSaving = ref(false) // 标记自动保存是否正在进行
  // 上次保存时间
  const lastSaveTime = ref(null) // 记录最后一次成功保存的时间

  // ==================== 计算属性 ====================
  // 计算已答题数量
  const answeredCount = computed(() => answeredQuestions.value.length)
  // 计算总题目数量
  const totalQuestions = computed(() => questions.value.length)
  // 计算未答题目数量
  const unansweredCount = computed(() => totalQuestions.value - answeredCount.value)
  // 计算答题进度百分比
  const progressPercent = computed(() => {
    if (totalQuestions.value === 0) return 0
    return Math.round((answeredCount.value / totalQuestions.value) * 100)
  })
  // 格式化剩余时间（时:分:秒）
  const formattedRemainingTime = computed(() => {
    const hours = Math.floor(remainingTime.value / 3600) // 计算小时数
    const minutes = Math.floor((remainingTime.value % 3600) / 60) // 计算分钟数
    const seconds = remainingTime.value % 60 // 计算秒数
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  })

  // ==================== 方法定义 ====================
  /**
   * 开始考试方法
   * @param {Object} examData - 考试相关数据
   * @param {string} examData.examId - 考试ID
   * @param {string} examData.paperId - 试卷ID
   * @param {number} examData.duration - 考试时长（分钟）
   * @param {Array} examData.questions - 题目列表
   */
  function startExam(examData) {
    // 重置所有考试相关状态
    currentExamId.value = examData.examId
    currentPaperId.value = examData.paperId
    examDuration.value = examData.duration
    questions.value = examData.questions || []
    remainingTime.value = examData.duration * 60 // 将分钟转换为秒
    examStartTime.value = Date.now() // 记录考试开始时间
    answers.value = new Map() // 清空答题记录
    answeredQuestions.value = [] // 清空已答列表
    currentQuestionIndex.value = 0 // 重置当前题目索引
    isExamining.value = true // 设置为考试中状态
    isSubmitted.value = false // 重置交卷状态

    // 启动倒计时
    startTimer()
  }

  /**
   * 启动考试倒计时
   * 每秒递减剩余时间，剩余时间为0时自动交卷
   */
  function startTimer() {
    // 清除可能存在的旧定时器
    if (timerInterval) {
      clearInterval(timerInterval)
    }
    // 创建新的定时器，每秒执行一次
    timerInterval = setInterval(() => {
      if (remainingTime.value > 0) {
        // 剩余时间大于0，每秒减1
        remainingTime.value--
      } else {
        // 剩余时间为0，自动交卷
        handleAutoSubmit()
      }
    }, 1000)
  }

  /**
   * 停止考试倒计时
   */
  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
  }

  /**
   * 保存单题答案方法
   * @param {string} questionId - 题目ID
   * @param {string|Array} answer - 用户答案
   */
  function saveAnswer(questionId, answer) {
    // 更新答案Map
    answers.value.set(questionId, answer)
    // 如果不在已答列表中，则添加
    if (!answeredQuestions.value.includes(questionId)) {
      answeredQuestions.value.push(questionId)
    }
  }

  /**
   * 获取单题答案方法
   * @param {string} questionId - 题目ID
   * @returns {string|Array} 返回保存的答案
   */
  function getAnswer(questionId) {
    return answers.value.get(questionId)
  }

  /**
   * 批量保存答案到服务器
   * @param {Array} answersData - 答案数据数组，每项包含question_id和user_answer
   * @returns {Promise} 返回保存结果
   */
  async function autoSaveAnswers(answersData) {
    // 如果已交卷或正在保存，不执行保存
    if (isSubmitted.value || isAutoSaving.value) {
      return
    }

    // 如果没有要保存的答案，直接返回
    if (!answersData || answersData.length === 0) {
      return
    }

    // 设置保存状态为进行中
    isAutoSaving.value = true
    try {
      // 调用批量保存API
      await saveExamAnswerAPI({
        paper_id: currentPaperId.value,
        answers: answersData,
        save_time: Date.now(),
        reconnect: false,
      })
      // 更新最后保存时间
      lastSaveTime.value = new Date()
    } catch (error) {
      // 保存失败，输出错误日志（不弹窗提示，避免打扰考试）
      console.error('答案批量自动保存失败', error)
    } finally {
      // 无论成功失败，都要关闭保存状态
      isAutoSaving.value = false
    }
  }

  /**
   * 自动保存答案到服务器（兼容旧版单题保存）
   * @param {string} questionId - 题目ID
   * @param {string|Array} answer - 用户答案
   * @returns {Promise} 返回保存结果
   */
  async function autoSaveAnswer(questionId, answer) {
    // 调用批量保存方法，传入单题数据
    await autoSaveAnswers([
      {
        question_id: questionId,
        user_answer: answer,
      },
    ])
  }

  /**
   * 自动提交试卷方法
   * 当考试时间结束时自动调用
   */
  async function handleAutoSubmit() {
    // 防止重复提交
    if (isSubmitted.value) {
      return
    }
    // 停止倒计时
    stopTimer()
    // 标记为已交卷
    isSubmitted.value = true
    // 设置考试状态为结束
    isExamining.value = false

    try {
      // 调用交卷接口
      await submitExam(currentPaperId.value)
    } catch (error) {
      console.error('自动交卷失败', error)
    }
  }

  /**
   * 手动交卷方法
   * 用户主动点击交卷按钮时调用
   * @returns {Promise} 返回交卷结果
   */
  async function submitExamPaper() {
    // 如果未考试或已交卷，直接返回
    if (!isExamining.value || isSubmitted.value) {
      return
    }

    // 停止倒计时
    stopTimer()
    // 标记为已交卷
    isSubmitted.value = true
    // 设置考试状态为结束
    isExamining.value = false

    // 调用交卷接口
    const result = await submitExam(currentPaperId.value)
    return result
  }

  /**
   * 上报考试异常方法
   * @param {string} type - 异常类型
   * @param {string} detail - 异常详情
   */
  async function reportException(type, detail = '') {
    // 防止 paper_id 为 null 时发送无效请求到后端
    if (!currentPaperId.value || !currentExamId.value) {
      console.warn(`[异常上报跳过] paperId=${currentPaperId.value}, examId=${currentExamId.value}, type=${type}`)
      return
    }
    try {
      // 调用异常上报接口
      await reportAbnormal({
        paper_id: currentPaperId.value, // 试卷ID
        exam_id: currentExamId.value, // 考试ID
        type: type, // 异常类型
        detail: detail, // 异常详情
        duration: 0, // 持续时间
        screen_out_count: 0, // 切屏次数
      })
    } catch (error) {
      console.error('异常上报失败', error) // 上报失败只输出日志，不打扰考试
    }
  }

  /**
   * 设置全屏状态方法
   * @param {boolean} fullScreen - 是否全屏
   */
  function setFullScreen(fullScreen) {
    isFullScreen.value = fullScreen
  }

  /**
   * 进入全屏方法
   */
  function enterFullScreen() {
    const element = document.documentElement // 获取HTML根元素
    if (element.requestFullscreen) {
      // 尝试使用标准全屏API
      element.requestFullscreen()
    } else if (element.webkitRequestFullScreen) {
      // 兼容WebKit内核浏览器
      element.webkitRequestFullScreen()
    } else if (element.msRequestFullscreen) {
      // 兼容IE浏览器
      element.msRequestFullscreen()
    }
    isFullScreen.value = true
  }

  /**
   * 退出全屏方法
   */
  function exitFullScreen() {
    if (document.exitFullscreen) {
      // 尝试使用标准退出全屏API
      document.exitFullscreen()
    } else if (document.webkitCancelFullScreen) {
      // 兼容WebKit内核浏览器
      document.webkitCancelFullScreen()
    } else if (document.msExitFullscreen) {
      // 兼容IE浏览器
      document.msExitFullscreen()
    }
    isFullScreen.value = false
  }

  /**
   * 重置考试状态方法
   * 考试结束后或需要重置时调用
   */
  function resetExam() {
    // 停止定时器
    stopTimer()
    // 清理缓存的图片 Blob URL，释放内存
    cleanupImages()
    // 重置所有状态
    currentExamId.value = null
    currentPaperId.value = null
    examStartTime.value = null
    remainingTime.value = 0
    answers.value = new Map()
    answeredQuestions.value = []
    currentQuestionIndex.value = 0
    questions.value = []
    isExamining.value = false
    isSubmitted.value = false
    isFullScreen.value = false
    isAutoSaving.value = false
    lastSaveTime.value = null
  }

  /**
   * 加载答题进度方法
   * 断点续答时调用，从服务器获取已保存的答题进度
   * @param {Array} savedAnswers - 已保存的答题记录列表
   */
  function loadProgress(savedAnswers) {
    if (!savedAnswers || !Array.isArray(savedAnswers)) {
      return
    }
    // 遍历已保存的答案，恢复到本地状态
    savedAnswers.forEach((item) => {
      answers.value.set(item.questionId, item.answer)
      if (!answeredQuestions.value.includes(item.questionId)) {
        answeredQuestions.value.push(item.questionId)
      }
    })
  }

  /**
   * 预加载考试图片方法
   * 考试开始前调用，将试卷中所有题目选项的图片 base64 解码后缓存为 Blob URL
   * @param {string} paperId - 试卷ID
   */
  async function preloadExamImages(paperId) {
    // 如果该试卷已预加载过，跳过重复请求
    if (preloadedPaperIds.value.has(paperId)) {
      console.log(`试卷 ${paperId} 图片已预加载，跳过`)
      return
    }
    try {
      const res = await preloadImagesAPI(paperId) // 调用预加载接口
      console.log('预加载接口原始返回:', res) // 调试日志
      // 请求拦截器已扁平化返回，images 在顶层
      const images = res.images
      console.log('images 数据:', images) // 调试日志
      if (!images || images.length === 0) {
        // 无图片也标记为已预加载，避免后续重复请求
        preloadedPaperIds.value.add(paperId)
        console.log('该试卷无需预加载图片')
        return
      }
      // 遍历每张图片，将 base64 解码为 Blob URL 并缓存
      for (const img of images) {
        const bytes = Uint8Array.from(atob(img.base64), (c) => c.charCodeAt(0)) // base64 解码为字节数组
        const blob = new Blob([bytes], { type: img.mime_type }) // 创建 Blob 对象
        const blobUrl = URL.createObjectURL(blob) // 生成 Blob URL
        const key = `${img.question_id}_${img.option_key}` // 缓存 key：题目ID_选项键
        // 释放旧 URL（如果存在）
        if (examImages.value.has(key)) {
          URL.revokeObjectURL(examImages.value.get(key))
        }
        examImages.value.set(key, blobUrl) // 缓存新的 Blob URL
      }
      // 标记该试卷已预加载完成
      preloadedPaperIds.value.add(paperId)
      console.log(`预加载完成，共缓存 ${images.length} 张图片`)
    } catch (error) {
      console.error('图片预加载失败', error)
    }
  }

  /**
   * 获取缓存图片 Blob URL
   * @param {string|number} questionId - 题目ID
   * @param {string} optionKey - 选项键（A/B/C/D）
   * @returns {string|null} 返回缓存的 Blob URL，未缓存返回 null
   */
  function getCachedImage(questionId, optionKey) {
    const key = `${questionId}_${optionKey}` // 构造缓存 key
    return examImages.value.get(key) || null // 返回缓存的 Blob URL
  }

  /**
   * 清理所有缓存的图片 Blob URL
   * 考试结束后调用，释放浏览器内存
   */
  function cleanupImages() {
    examImages.value.forEach((blobUrl) => {
      URL.revokeObjectURL(blobUrl) // 释放 Blob URL
    })
    examImages.value.clear() // 清空缓存 Map
    preloadedPaperIds.value.clear() // 清空已预加载标记
  }

  // 返回状态和方法，供组件使用
  return {
    // 考试信息状态
    currentExamId, // 当前考试ID
    currentPaperId, // 当前试卷ID
    examStartTime, // 考试开始时间
    examDuration, // 考试时长
    remainingTime, // 剩余时间
    // 答题状态
    answers, // 答题记录
    answeredQuestions, // 已答题目ID列表
    currentQuestionIndex, // 当前题目索引
    questions, // 题目列表
    // 考试状态标志
    isExamining, // 是否正在考试
    isSubmitted, // 是否已交卷
    isFullScreen, // 是否全屏
    isAutoSaving, // 是否自动保存中
    lastSaveTime, // 上次保存时间
    // 计算属性
    answeredCount, // 已答数量
    totalQuestions, // 总题数
    unansweredCount, // 未答数量
    progressPercent, // 答题进度百分比
    formattedRemainingTime, // 格式化剩余时间
    // 方法
    startExam, // 开始考试
    stopTimer, // 停止计时器
    saveAnswer, // 保存答案
    getAnswer, // 获取答案
    autoSaveAnswer, // 自动保存答案（单题）
    autoSaveAnswers, // 自动保存答案（批量）
    handleAutoSubmit, // 自动交卷
    submitExamPaper, // 手动交卷
    reportException, // 上报异常
    setFullScreen, // 设置全屏状态
    enterFullScreen, // 进入全屏
    exitFullScreen, // 退出全屏
    resetExam, // 重置考试状态
    loadProgress, // 加载答题进度
    // 图片缓存
    examImages, // 图片缓存 Map
    preloadExamImages, // 预加载考试图片
    getCachedImage, // 获取缓存的图片 URL
    cleanupImages, // 清理图片缓存
  }
})
