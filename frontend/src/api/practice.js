/**
 * 练习相关API接口
 * 封装日常练习、题目获取、答案提交、收藏等接口
 * 接口路径遵循 V1.5 接口文档规范
 */
import request from '@/utils/request';

/**
 * 开始练习/恢复练习接口
 * @returns {Promise} 返回练习会话信息，包含session_id、student_xid、student_name、questions、progress
 */
export function startPractice() {
  return request({
    url: '/practice/start/',
    method: 'post',
  });
}

/**
 * 提交本题答案接口（支持单题/批量）
 * @param {Object} data - 答题数据
 * @param {string} data.session_id - 练习会话ID
 * @param {number} data.question_id - 题目ID（单题模式）
 * @param {string} data.user_answer - 用户答案（单题模式）
 * @param {Array} data.answers - 批量答案数组（批量模式）[{question_id, user_answer}, ...]
 * @returns {Promise} 返回提交结果，包含is_correct和correct_answer或results数组
 */
export function submitPracticeAnswer(data) {
  return request({
    url: '/practice/submit/',
    method: 'post',
    data,
  });
}

/**
 * 查看本题答案接口
 * @param {string} sessionId - 练习会话ID
 * @param {number} questionId - 题目ID
 * @returns {Promise} 返回正确答案和解析
 */
export function getPracticeAnswer(sessionId, questionId) {
  return request({
    url: '/practice/answer/',
    method: 'get',
    params: { session_id: sessionId, question_id: questionId },
  });
}

/**
 * 下一组题目（换学生）接口
 * @param {string} sessionId - 当前会话ID
 * @returns {Promise} 返回新会话信息
 */
export function nextQuestionGroup(sessionId) {
  return request({
    url: '/practice/next-group/',
    method: 'post',
    data: { session_id: sessionId },
  });
}

/**
 * 重置练习进度接口
 * @returns {Promise} 返回重置结果
 */
export function resetPracticeProgress() {
  return request({
    url: '/practice/reset-progress/',
    method: 'post',
  });
}

/**
 * 练习结果统计接口
 * @returns {Promise} 返回练习统计数据，包含total_questions、passed_questions、progress、wrong_distribution、redo_count
 */
export function getPracticeResult() {
  return request({
    url: '/practice/result/',
    method: 'get',
  });
}

// ==================== 收藏夹模块接口 ====================

/**
 * 我的收藏列表接口
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @param {string} params.sort_type - 排序类型（time_desc/name_asc）
 * @param {string} params.keyword - 按学生姓名模糊搜索
 * @returns {Promise} 返回收藏列表分页数据（含完整快照数据）
 */
export function getCollectionList(params) {
  return request({
    url: '/collection/list/',
    method: 'get',
    params,
  });
}

/**
 * 收藏题目接口
 * @param {Object} data - 收藏数据
 * @param {string} data.session_id - 练习会话ID
 * @param {number} data.question_id - 题目ID
 * @returns {Promise} 返回收藏结果，包含favorite_id
 */
export function addCollection(data) {
  return request({
    url: '/collection/add/',
    method: 'post',
    data,
  });
}

/**
 * 取消收藏接口
 * @param {string} favoriteId - 收藏ID
 * @returns {Promise} 返回取消收藏结果
 */
export function removeCollection(favoriteId) {
  return request({
    url: '/collection/remove/',
    method: 'post',
    data: { favorite_id: favoriteId },
  });
}

/**
 * 清空收藏接口
 * @returns {Promise} 返回清空结果
 */
export function clearCollection() {
  return request({
    url: '/collection/clear/',
    method: 'post',
  });
}

/**
 * 收藏题目回放练习接口
 * @param {Object} data - 回放数据
 * @param {string} data.favorite_id - 收藏记录ID
 * @param {string} data.user_answer - 用户提交的答案
 * @returns {Promise} 返回判题结果，包含is_correct、correct_answer、question_title、question_type
 */
export function replayCollection(data) {
  return request({
    url: '/collection/replay/',
    method: 'post',
    data,
  });
}