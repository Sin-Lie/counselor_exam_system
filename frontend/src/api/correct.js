/**
 * 批改相关API接口
 * 封装简答题批改、分数管理等接口
 * 接口路径遵循 V1.5 接口文档规范
 */
import request from '@/utils/request'; // 引入封装的axios实例

/**
 * 待批改列表接口（支持分页）
 * @param {Object} params - 查询参数
 * @param {string} params.exam_id - 考试ID（可选）
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @returns {Promise} 返回待批改列表分页数据
 */
export function getCorrectList(params) {
  return request({
    url: '/correct/list/', // 获取批改列表接口URL（V1.5）
    method: 'get', // GET请求方法
    params, // URL查询参数
  });
}

/**
 * 提交/修改批改分数接口（合并接口）
 * @param {string} answerId - 答题记录ID
 * @param {Object} data - 批改数据
 * @param {number} data.score - 给出的分数
 * @param {string} data.remark - 批改评语
 * @returns {Promise} 返回批改提交结果
 */
export function submitScore(answerId, data) {
  return request({
    url: `/correct/score/${answerId}/`, // 提交批改接口URL（V1.5）
    method: 'put', // PUT请求方法
    data, // 请求体数据
  });
}

/**
 * 批改进度统计接口
 * @param {string} examId - 考试ID（可选）
 * @returns {Promise} 返回批改进度数据
 */
export function getCorrectProgress(examId) {
  return request({
    url: '/correct/progress/', // 获取批改进度接口URL（V1.5）
    method: 'get', // GET请求方法
    params: examId ? { exam_id: examId } : {}, // URL查询参数
  });
}

/**
 * 批改日志查询接口
 * @param {Object} params - 查询参数
 * @param {string} params.exam_id - 考试ID（可选）
 * @param {string} params.grader_id - 批改员ID（可选）
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @returns {Promise} 返回批改日志分页数据
 */
export function getCorrectLogList(params) {
  return request({
    url: '/correct/log/list/', // 获取批改日志接口URL（V1.5）
    method: 'get', // GET请求方法
    params, // URL查询参数
  });
}

/**
 * 发布批改成绩接口
 * 批改员改完自己负责的全部试卷后才能发布
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回发布结果
 */
export function publishScores(examId) {
  return request({
    url: `/correct/publish/${examId}/`, // 发布批改成绩接口URL（V1.5）
    method: 'post', // POST请求方法
  });
}

/**
 * 获取辅导员成绩列表接口
 * @param {Object} params - 查询参数
 * @param {string} params.exam_id - 考试ID（必填）
 * @param {boolean} params.is_graded - 是否已批改（可选，true=已批改，false=未批改）
 * @param {string} params.job_number - 辅导员工号（可选，精确匹配）
 * @param {number} params.page - 页码，默认1
 * @param {number} params.size - 每页条数，默认10
 * @returns {Promise} 返回辅导员成绩列表分页数据
 */
export function getCounselorScoreList(params) {
  return request({
    url: '/correct/counselor/scores/', // 获取辅导员成绩列表接口URL（V1.5）
    method: 'get', // GET请求方法
    params, // URL查询参数
  });
}

/**
 * 手动录入/修改成绩接口
 * @param {Object} data - 录入数据
 * @param {string} data.exam_id - 考试ID
 * @param {string} data.job_number - 辅导员工号
 * @param {number} data.score - 录入分数
 * @returns {Promise} 返回录入结果
 */
export function importScore(data) {
  return request({
    url: '/correct/import/score/', // 手动录入成绩接口URL（V1.5）
    method: 'post', // POST请求方法
    data, // 请求体数据
  });
}
