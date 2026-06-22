/**
 * 用户状态管理模块
 * 管理用户登录信息、Token、角色等用户相关状态
 */
import { defineStore } from 'pinia'; // 引入Pinia的defineStore函数，用于定义状态管理
import { ref, computed } from 'vue'; // 引入Vue的ref和computed响应式API
import { counselorLogin, adminLogin, counselorLogout, adminLogout, getUserInfo, resetPassword as resetPasswordApi } from '@/api/auth'; // 引入认证相关API接口

/**
 * 用户状态管理Store
 * 使用组合式API风格定义状态管理
 */
export const useUserStore = defineStore('user', () => {
  // ==================== 状态定义 ====================
  // 用户信息
  const userInfo = ref(null); // 用户信息对象
  // Token令牌
  const token = ref(localStorage.getItem('token') || ''); // 从localStorage读取Token初始化
  // 登录加载状态
  const loading = ref(false); // 标记登录请求是否正在加载

  // ==================== 计算属性 ====================
  // 判断是否已登录
  const isLoggedIn = computed(() => !!token.value);
  // 判断是否为辅导员角色 (role=1)
  const isCounselor = computed(() => userInfo.value?.role === 1);
  // 判断是否为管理员角色（包含超级管理员）(role=2 或 role=3)
  const isAdmin = computed(() => [2, 3].includes(userInfo.value?.role));
  // 判断是否为超级管理员 (role=3)
  const isSuperAdmin = computed(() => userInfo.value?.role === 3);
  // 获取用户ID
  const userId = computed(() => userInfo.value?.id || null);
  // 获取用户名称
  const userName = computed(() => userInfo.value?.name || '');
  // 获取用户角色
  const userRole = computed(() => userInfo.value?.role || '');

  // ==================== 方法定义 ====================
  /**
   * 设置用户信息方法
   * @param {Object} info - 用户信息对象
   */
  function setUserInfo(info) {
    userInfo.value = info; // 更新用户信息状态
    if (info) {
      // 如果信息存在，存入localStorage持久化
      localStorage.setItem('userInfo', JSON.stringify(info));
    } else {
      // 信息为空，清除localStorage
      localStorage.removeItem('userInfo');
    }
  }

  /**
   * 设置Token方法
   * @param {string} newToken - 新的Token字符串
   */
  function setToken(newToken) {
    token.value = newToken; // 更新Token状态
    if (newToken) {
      // Token存在，存入localStorage持久化
      localStorage.setItem('token', newToken);
    } else {
      // Token为空，清除localStorage
      localStorage.removeItem('token');
    }
  }

  /**
   * 辅导员登录方法
   * @param {Object} loginData - 登录数据，包含工号和手机号
   * @param {string} loginData.jobNumber - 辅导员工号
   * @param {string} loginData.phone - 手机号
   * @returns {Promise} 返回登录结果
   */
  async function login(loginData) {
    loading.value = true; // 开始加载状态
    try {
      // 调用辅导员登录接口
      const res = await counselorLogin(loginData);
      // 保存Token到状态和本地存储
      setToken(res.token);
      // 保存用户信息
      setUserInfo(res.userInfo);
      // 返回成功结果
      return res;
    } finally {
      // 无论成功失败，都要关闭加载状态
      loading.value = false;
    }
  }

  /**
   * 管理员登录方法
   * @param {Object} loginData - 登录数据，包含用户名和密码
   * @param {string} loginData.username - 管理员用户名
   * @param {string} loginData.password - 密码
   * @returns {Promise} 返回登录结果
   */
  async function adminLoginAction(loginData) {
    loading.value = true; // 开始加载状态
    try {
      // 调用管理员登录接口
      const res = await adminLogin(loginData);
      // 保存Token到状态和本地存储
      setToken(res.token);
      // 保存用户信息
      setUserInfo(res.userInfo);
      // 返回成功结果
      return res;
    } finally {
      // 无论成功失败，都要关闭加载状态
      loading.value = false;
    }
  }

  /**
   * 登出方法
   * 清除本地状态和存储，并调用后端登出接口
   */
  async function logout() {
    try {
      // 根据用户角色调用对应的登出接口
      if (isCounselor.value) {
        await counselorLogout(); // 辅导员登出
      } else if (isAdmin.value) {
        await adminLogout(); // 管理员登出
      }
    } catch (error) {
      // 忽略登出接口错误，继续清除本地状态
      console.error('登出接口调用失败', error);
    } finally {
      // 清除Token和用户信息状态
      setToken('');
      setUserInfo(null);
    }
  }

  /**
   * 获取当前用户信息方法
   * 从后端获取最新用户信息并更新本地状态
   * @returns {Promise} 返回用户信息
   */
  async function fetchUserInfo() {
    try {
      // 调用获取用户信息接口
      const res = await getUserInfo();
      // 更新本地用户信息
      setUserInfo(res);
      return res;
    } catch (error) {
      // 获取失败时，清除本地登录状态
      console.error('获取用户信息失败', error);
      logout();
      throw error;
    }
  }

  /**
   * 重置密码方法
   * 通过手机号验证身份后重置密码
   * @param {Object} data - 重置密码数据
   * @param {string} data.username - 工号/账号
   * @param {string} data.phone - 手机号
   * @param {string} data.newPassword - 新密码
   * @returns {Promise} 返回重置结果
   */
  async function resetPassword(data) {
    try {
      // 调用重置密码接口
      await resetPasswordApi(data);
      return true;
    } catch (error) {
      console.error('密码重置失败', error);
      throw error;
    }
  }

  /**
   * 初始化用户状态方法
   * 应用启动时调用，恢复登录状态
   */
  function initUserState() {
    // 从localStorage恢复Token
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      token.value = storedToken;
    }
    // 从localStorage恢复用户信息
    const storedUserInfo = localStorage.getItem('userInfo');
    if (storedUserInfo) {
      try {
        userInfo.value = JSON.parse(storedUserInfo);
      } catch (e) {
        console.error('用户信息解析失败', e);
        // 解析失败，清除损坏的数据
        localStorage.removeItem('userInfo');
      }
    }
  }

  // 返回状态和方法，供组件使用
  return {
    // 状态
    userInfo, // 用户信息
    token, // 认证令牌
    loading, // 加载状态
    // 计算属性
    isLoggedIn, // 是否已登录
    isCounselor, // 是否为辅导员
    isAdmin, // 是否为管理员
    isSuperAdmin, // 是否为超级管理员
    userId, // 用户ID
    userName, // 用户名称
    userRole, // 用户角色
    // 方法
    setUserInfo, // 设置用户信息
    setToken, // 设置Token
    login, // 辅导员登录
    adminLogin: adminLoginAction, // 管理员登录
    logout, // 登出
    fetchUserInfo, // 获取用户信息
    initUserState, // 初始化用户状态
    resetPassword, // 重置密码
  };
});
