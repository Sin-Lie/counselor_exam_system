/**
 * 考试相关API接口
 * 封装考试列表、考试详情、考试答题、交卷等接口
 * 接口路径遵循 V1.5 接口文档规范
 */
import request from '@/utils/request'

/**
 * 获取考试列表接口（辅导员端）
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页数量
 * @param {string} params.status - 状态筛选
 * @returns {Promise} 返回考试列表数据
 */
export function getExamList(params) {
  return request({
    url: '/exam/list/',
    method: 'get',
    params: params,
  })
}

/**
 * 获取考试详情接口
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回考试详细信息，包含考试规则、时间、题型、exam_status、remaining_time
 */
export function getExamDetail(examId) {
  return request({
    url: `/exam/info/${examId}/`,
    method: 'get',
  })
}

/**
 * 进入考试接口（支持断线恢复）
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回试卷题目列表，包含paper_id、is_resumed、questions、exam_status
 */
export function enterExam(examId) {
  return request({
    url: `/exam/enter/${examId}/`,
    method: 'post',
  })
}

/**
 * 获取当前已保存答案接口（用于断线快速恢复）
 * @param {string} paperId - 试卷ID
 * @returns {Promise} 返回已答题目的答案记录
 */
export function getSavedAnswers(paperId) {
  return request({
    url: `/exam/saved-answers/${paperId}/`,
    method: 'get',
  })
}

/**
 * 实时保存答案接口（支持单题/批量）
 * @param {Object} data - 答题数据
 * @param {string} data.paper_id - 试卷ID
 * @param {string} data.question_id - 题目ID（单题模式）
 * @param {string} data.user_answer - 用户答案（单题模式）
 * @param {Array} data.answers - 批量答案数组（批量模式）[{question_id, user_answer}, ...]
 * @param {number} data.save_time - 保存时间（毫秒时间戳）
 * @param {boolean} data.reconnect - 是否为断线重连
 * @returns {Promise} 返回保存结果，包含save_status
 */
export function saveAnswer(data) {
  return request({
    url: '/exam/save/',
    method: 'post',
    data,
  })
}

/**
 * 交卷接口
 * @param {string} paperId - 试卷ID
 * @returns {Promise} 返回交卷结果
 */
export function submitExam(paperId) {
  return request({
    url: `/exam/submit/${paperId}/`,
    method: 'post',
  })
}

/**
 * 考试异常日志上报接口
 * @param {Object} data - 异常数据
 * @param {string} data.paper_id - 试卷ID
 * @param {string} data.exam_id - 考试ID
 * @param {string} data.type - 异常类型（screen_out/timeout/abnormal_operation）
 * @param {number} data.duration - 持续时间（秒）
 * @param {number} data.screen_out_count - 切屏次数
 * @returns {Promise} 返回上报结果，包含force_submit、backend_count
 */
export function reportAbnormal(data) {
  return request({
    url: '/exam/report-abnormal/',
    method: 'post',
    data,
  })
}

/**
 * 获取考生状态列表接口（管理端）
 * @param {string} examId - 考试ID
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @param {string} params.status - 筛选考生状态（0=未开始，1=进行中，2=已交卷，3=异常交卷）
 * @returns {Promise} 返回考生状态列表
 */
export function getExamUserStatus(examId, params) {
  return request({
    url: `/exam/user-status/${examId}/`,
    method: 'get',
    params,
  })
}

/**
 * 超管试卷检查接口
 * @param {string} paperId - 试卷ID
 * @returns {Promise} 返回试卷详情（不含答案），包含paper_id、teacher_name、teacher_gh、questions
 */
export function getPaperReview(paperId) {
  return request({
    url: `/exam/paper-review/${paperId}/`,
    method: 'get',
  })
}

// ==================== 图片预加载接口 ====================

/**
 * 预加载试卷图片接口
 * 考试开始前调用，将题目选项中的图片 base64 编码后缓存为 Blob URL
 * @param {string} paperId - 试卷ID（ExamPaper.id）
 * @returns {Promise} 返回图片数据，包含paper_id、images数组
 */
export function preloadImages(paperId) {
  return request({
    url: `/exam/preload-images/${paperId}/`,
    method: 'get',
  })
}

// ==================== 成绩模块接口 ====================

/**
 * 获取我的成绩列表接口
 * @param {number} params.page - 页码，默认1
 * @param {number} params.pageSize - 每页条数，默认10
 * @returns {Promise} 返回成绩列表，包含exam_title、score、objective_score、subjective_score、status等
 */
export function getMyScores(params) {
  return request({
    url: '/score/my/list/',
    method: 'get',
    params,
  })
}

/**
 * 获取我的成绩接口
 * @param {string} examId - 考试ID
 * @param {Object} options - 可选配置
 * @param {boolean} options.silent - 是否静默处理错误（不弹提示）
 * @returns {Promise} 返回成绩信息，包含score、objective_score、subjective_score
 */
export function getMyScore(examId, options = {}) {
  return request({
    url: `/score/my/${examId}/`,
    method: 'get',
    _silent: options.silent || false,
  })
}

/**
 * 获取我的试卷详情接口
 * @param {string} paperId - 试卷ID
 * @returns {Promise} 返回试卷详情，包含每题得分、正确答案等
 */
export function getMyPaperDetail(paperId) {
  return request({
    url: `/score/my-paper/${paperId}/`,
    method: 'get',
  })
}

/**
 * 查看任意考生试卷详情接口（管理员/超管）
 * @param {string} paperId - 试卷ID
 * @returns {Promise} 返回试卷详情
 */
export function getPaperDetail(paperId) {
  return request({
    url: `/score/paper-detail/${paperId}/`,
    method: 'get',
  })
}

/**
 * 整体考试统计接口（超管）
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回统计数据，包含avg_score、attend_rate、objective_score_rate等
 */
export function getExamStatistics(examId) {
  return request({
    url: `/score/statistics/${examId}/`,
    method: 'get',
  })
}

/**
 * 未参考人员清单接口（超管）
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回未参考人员列表
 */
export function getUnattendedList(examId) {
  return request({
    url: `/score/unattended/${examId}/`,
    method: 'get',
  })
}

/**
 * 导出成绩Excel接口（超管）
 * @param {string} examId - 考试ID
 * @param {string} params.export_scope - 导出范围（all=全部，graded_only=仅已出成绩）
 * @returns {Promise} 返回Excel文件blob
 */
export function exportScoresExcel(examId, params) {
  return request({
    url: `/score/export/${examId}/`,
    method: 'get',
    params,
    responseType: 'blob',
  })
}

/**
 * 导出考试学生信息Excel接口（超管）
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回Excel文件blob
 */
export function exportExamStudents(examId) {
  return request({
    url: `/exam/export-students/${examId}/`,
    method: 'get',
    responseType: 'blob',
  })
}
