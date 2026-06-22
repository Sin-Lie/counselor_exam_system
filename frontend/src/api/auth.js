/**
 * 认证相关API接口
 * 封装登录、登出、Token刷新等认证相关接口
 * 接口路径遵循 V1.5 接口文档规范
 */
import request from '@/utils/request'; // 引入封装的axios实例

/**
 * 辅导员登录接口
 * @param {Object} data - 登录参数
 * @param {string} data.username - 工号/账号
 * @param {string} data.password - 密码
 * @returns {Promise} 返回登录结果，包含Token和用户信息
 */
export function counselorLogin(data) {
  return request({
    url: '/auth/login/', // 辅导员登录接口URL（V1.5）
    method: 'post', // POST请求方法
    data, // 请求体数据
  });
}

/**
 * 管理员/超管登录接口
 * @param {Object} data - 登录参数
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @returns {Promise} 返回登录结果，包含Token和用户信息
 */
export function adminLogin(data) {
  return request({
    url: '/admin/login/', // 管理员登录接口URL（V1.5）
    method: 'post', // POST请求方法
    data, // 请求体数据
  });
}

/**
 * 获取当前用户信息接口
 * @returns {Promise} 返回当前登录用户的信息
 */
export function getUserInfo() {
  return request({
    url: '/auth/info/', // 获取用户信息接口URL（V1.5）
    method: 'get', // GET请求方法
  });
}

/**
 * 用户登出接口
 * @returns {Promise} 返回登出结果
 */
export function logout() {
  return request({
    url: '/auth/logout/', // 登出接口URL（V1.5）
    method: 'post', // POST请求方法
  });
}

/**
 * 辅导员登出接口
 * @returns {Promise} 返回登出结果
 */
export function counselorLogout() {
  return request({
    url: '/auth/logout/', // 登出接口URL（V1.5）
    method: 'post', // POST请求方法
  });
}

/**
 * 管理员登出接口
 * @returns {Promise} 返回登出结果
 */
export function adminLogout() {
  return request({
    url: '/auth/logout/', // 登出接口URL（V1.5，与辅导员共用）
    method: 'post', // POST请求方法
  });
}

/**
 * 刷新Token接口
 * @param {string} refreshToken - 刷新令牌
 * @returns {Promise} 返回新的Token信息
 */
export function refreshToken(refreshToken) {
  return request({
    url: '/auth/refresh/', // 刷新Token接口URL（V1.5）
    method: 'post', // POST请求方法
    data: { refresh_token: refreshToken }, // 请求体数据
  });
}

/**
 * 重置用户密码接口（管理员操作）
 * @param {Object} data - 重置密码数据
 * @param {string} data.user_id - 用户ID
 * @param {string} data.new_password - 新密码
 * @returns {Promise} 返回重置结果
 */
export function resetPassword(data) {
  return request({
    url: '/system/user/reset-password/', // 重置密码接口URL（V1.5）
    method: 'post', // POST请求方法
    data, // 请求体数据
  });
}
