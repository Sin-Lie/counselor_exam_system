/**
 * Axios 实例配置文件
 * 封装请求拦截器、响应拦截器、错误处理等通用逻辑
 * 提供统一的请求配置和错误提示
 * 接口路径遵循 V1.5 接口文档规范
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

instance.interceptors.request.use(
  (config) => {
    // 登录接口不添加 token（避免旧token干扰登录）
    // 注意：config.url 不包含 baseURL，所以直接匹配 /auth/login 和 /admin/login
    const url = config.url || ''
    const isLoginRequest = url.includes('/auth/login') || url.includes('/admin/login')
    if (!isLoginRequest) {
      const token = localStorage.getItem('token')
      if (token && token !== 'undefined') {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

instance.interceptors.response.use(
  (response) => {
    // 如果是 blob 类型的响应（如导出Excel），直接返回，不做统一处理
    if (response.data instanceof Blob) {
      return response.data
    }
    
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.msg || '操作失败')
      return Promise.reject(new Error(res.msg || '操作失败'))
    }
    // 扁平化返回：将 code、msg 与 data 内容合并，方便视图层直接使用
    // 兼容两种后端返回格式：有 data 包裹层 和 无 data 包裹层（字段直接在顶层）
    if (res.data !== undefined && typeof res.data === 'object' && !Array.isArray(res.data)) {
      return { code: res.code, msg: res.msg, ...res.data }
    }
    return res
  },
  (error) => {
    // 如果请求配置了 _silent 标记，跳过错误提示
    if (error.config && error.config._silent) {
      return Promise.reject(error)
    }
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 400:
          ElMessage.error(data.msg || '参数错误')
          break
        case 4001:
          ElMessage.error('账号不存在')
          break
        case 4002:
          ElMessage.error('密码错误')
          break
        case 4003:
          ElMessage.error(data.msg || '考试总分配置错误')
          break
        case 4004:
          ElMessage.error(data.msg || '考试时长配置错误')
          break
        case 4005:
          ElMessage.error(data.msg || '试卷生成条件不满足')
          break
        case 401:
          localStorage.removeItem('token')
          localStorage.removeItem('userInfo')
          ElMessage.error('登录已过期，请重新登录')
          router.push('/login')
          break
        case 403:
          ElMessage.error(data.msg || '权限不足')
          break
        case 4031:
          ElMessage.error('无批改权限')
          break
        case 4032:
          ElMessage.error(data.msg || '不在考试时间内或考试已关闭')
          break
        case 4033:
          ElMessage.error(data.msg || '考试已交卷，不可重复提交')
          break
        case 4034:
          ElMessage.error('练习会话不存在或已过期')
          break
        case 404:
          ElMessage.error(data.msg || '请求的资源不存在')
          break
        case 500:
          ElMessage.error(data.msg || '服务器内部错误，请稍后再试')
          break
        case 5001:
          ElMessage.error(data.msg || 'Excel导入失败')
          break
        default:
          ElMessage.error(data.msg || '请求失败，请稍后再试')
      }
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络设置')
    } else {
      ElMessage.error('请求配置错误')
    }
    return Promise.reject(error)
  },
)

export default instance
