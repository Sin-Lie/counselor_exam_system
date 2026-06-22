/**
 * 系统管理相关API接口
 * 封装用户管理、题库管理、考试管理、统计、日志等接口
 * 接口路径遵循 V1.5 接口文档规范
 */
import request from '@/utils/request'

// ==================== 用户管理接口 ====================

/**
 * 导入辅导员接口
 * @param {FormData} data - 导入文件数据
 * @returns {Promise} 返回导入结果，包含success_num、fail_num、fail_reason
 */
export function importCounselors(data) {
  return request({
    url: '/system/import/users/',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * 导入学生信息接口
 * @param {FormData} data - 导入文件数据
 * @returns {Promise} 返回导入结果，包含success_num、fail_num、fail_reason
 */
export function importStudents(data) {
  return request({
    url: '/system/import/students/',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * 用户列表接口
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @param {string} params.role - 用户角色筛选（可选）
 * @param {string} params.keyword - 搜索关键词（可选）
 * @returns {Promise} 返回用户列表分页数据
 */
export function getUserList(params) {
  return request({
    url: '/system/user/list/',
    method: 'get',
    params,
  })
}

/**
 * 启用/禁用用户接口
 * @param {Object} data - 操作数据
 * @param {string} data.user_id - 用户ID
 * @param {number} data.status - 状态（1启用，0禁用）
 * @returns {Promise} 返回操作结果
 */
export function setUserStatus(data) {
  return request({
    url: '/system/user/set-status/',
    method: 'post',
    data,
  })
}

/**
 * 重置用户密码接口
 * @param {Object} data - 重置数据
 * @param {string} data.user_id - 用户ID
 * @param {string} data.new_password - 新密码（至少6位）
 * @returns {Promise} 返回重置结果
 */
export function resetUserPassword(data) {
  return request({
    url: '/system/user/reset-password/',
    method: 'post',
    data,
  })
}

/**
 * 编辑用户信息接口
 * @param {string} userId - 用户ID
 * @param {Object} data - 更新数据（name、phone）
 * @returns {Promise} 返回更新结果
 */
export function editUser(userId, data) {
  return request({
    url: `/system/user/edit/${userId}/`,
    method: 'put',
    data,
  })
}

/**
 * 创建管理员账号接口
 * @param {Object} data - 管理员信息
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @param {string} data.name - 姓名
 * @param {number} data.role - 角色（2=批改员，3=超管）
 * @returns {Promise} 返回创建结果，包含user_id
 */
export function createAdmin(data) {
  return request({
    url: '/system/admin/create/',
    method: 'post',
    data,
  })
}

// ==================== 题库管理接口 ====================

/**
 * 题库列表接口
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @param {string} params.type - 题目类型筛选（可选，single/multi/judge/essay）
 * @param {string} params.keyword - 搜索关键词（可选）
 * @returns {Promise} 返回题目列表分页数据
 */
export function getQuestionList(params) {
  return request({
    url: '/system/question/list/',
    method: 'get',
    params,
  })
}

/**
 * 新增题目接口
 * @param {Object} data - 题目数据
 * @param {string} data.title - 题目题干模板（用{name}占位学生姓名）
 * @param {string} data.type - 题目类型（single/multi/judge/essay）
 * @param {string} data.param_field - 参数字段（students表字段名）
 * @param {string} data.analysis - 解析
 * @returns {Promise} 返回创建结果，包含template_id
 */
export function addQuestion(data) {
  return request({
    url: '/system/question/add/',
    method: 'post',
    data,
  })
}

/**
 * 编辑题目接口
 * @param {string} templateId - 题目模板ID
 * @param {Object} data - 更新的题目数据
 * @returns {Promise} 返回更新结果
 */
export function editQuestion(templateId, data) {
  return request({
    url: `/system/question/edit/${templateId}/`,
    method: 'post',
    data,
  })
}

/**
 * 删除题目接口（软删除）
 * @param {string} templateId - 题目模板ID
 * @returns {Promise} 返回删除结果
 */
export function deleteQuestion(templateId) {
  return request({
    url: `/system/question/del/${templateId}/`,
    method: 'post',
  })
}

/**
 * 启用/禁用题目接口
 * @param {string} templateId - 题目模板ID
 * @param {Object} data - 操作数据
 * @param {number} data.status - 状态（1=启用，0=禁用）
 * @returns {Promise} 返回操作结果
 */
export function setQuestionStatus(templateId, data) {
  return request({
    url: `/system/question/set-status/${templateId}/`,
    method: 'post',
    data,
  })
}

// ==================== 考试管理接口 ====================

/**
 * 考试列表接口（管理员/超管）
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @returns {Promise} 返回考试列表分页数据
 */
export function getExamList(params) {
  return request({
    url: '/system/exam/list/',
    method: 'get',
    params,
  })
}

/**
 * 创建考试接口
 * @param {Object} data - 考试数据
 * @param {string} data.exam_name - 考试名称
 * @param {string} data.release_time - 发布时间（YYYY-MM-DD）
 * @param {string} data.exam_start - 考试开始时间（YYYY-MM-DD HH:MM:SS）
 * @param {number} data.exam_duration - 考试时长（分钟）
 * @param {Array} data.questions - 题型配置 [{type, count, score}, ...]
 * @returns {Promise} 返回创建结果，包含exam_id
 */
export function createExam(data) {
  return request({
    url: '/system/exam/create/',
    method: 'post',
    data,
    timeout: 180000,
  })
}

/**
 * 编辑考试接口
 * @param {string} examId - 考试ID
 * @param {Object} data - 更新的考试数据（全部可选）
 * @returns {Promise} 返回更新结果
 */
export function editExam(examId, data) {
  return request({
    url: `/system/exam/edit/${examId}/`,
    method: 'post',
    data,
  })
}

/**
 * 删除考试接口（软删除）
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回删除结果
 */
export function deleteExam(examId) {
  return request({
    url: `/system/exam/del/${examId}/`,
    method: 'post',
  })
}

/**
 * 考试发布/关闭接口
 * @param {Object} data - 操作数据
 * @param {string} data.exam_id - 考试ID
 * @param {string} data.status - 状态（publish/close）
 * @returns {Promise} 返回操作结果
 */
export function setExamStatus(data) {
  return request({
    url: '/system/exam/set-status/',
    method: 'post',
    data,
  })
}

/**
 * 考卷预览接口
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回预览数据
 */
export function previewExam(examId) {
  return request({
    url: `/system/exam/preview/${examId}/`,
    method: 'get',
  })
}

/**
 * 考试异常记录查看接口
 * @param {Object} params - 查询参数
 * @param {string} params.exam_id - 考试ID（可选）
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @returns {Promise} 返回异常记录分页数据
 */
export function getExamAbnormalList(params) {
  return request({
    url: '/system/exam/abnormal-list/',
    method: 'get',
    params,
  })
}

// ==================== 日志接口 ====================

/**
 * 系统日志查询接口
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @param {string} params.module - 模块筛选（可选）
 * @param {string} params.start_time - 开始时间（可选，格式：YYYY-MM-DD HH:MM:SS）
 * @param {string} params.end_time - 结束时间（可选，格式：YYYY-MM-DD HH:MM:SS）
 * @returns {Promise} 返回日志分页数据
 */
export function getSystemLogList(params) {
  return request({
    url: '/system/log/list/',
    method: 'get',
    params,
  })
}

// ==================== 别名导出（兼容旧组件导入） ====================

// 考试管理列表（管理员/超管）别名
export { getExamList as getExamManageList }

// 发布考试
export function publishExam(examId) {
  return setExamStatus({ exam_id: examId, status: 'publish' })
}

// 关闭考试
export function closeExam(examId) {
  return setExamStatus({ exam_id: examId, status: 'close' })
}

// 考试统计（从成绩模块导出）
export { getExamStatistics } from './exam'

// ==================== 日志分类查询 ====================

// 登录日志
export function getLoginLogs(params) {
  return getSystemLogList({ ...params, module: 'auth' })
}

// 考试异常日志
export function getExamExceptionLogs(params) {
  return getExamAbnormalList(params)
}

// 切屏日志
export function getFocusLeaveLogs(params) {
  return getSystemLogList({ ...params, module: '考试' })
}

// 批改日志
export { getCorrectLogList as getCorrectLogs } from './correct'
