/**
 * Vue Router 路由配置文件
 * 配置整个应用的路由规则
 */
import { createRouter, createWebHistory } from 'vue-router' // 引入Vue Router创建函数
import { ElMessage } from 'element-plus' // 引入Element Plus消息组件
import NProgress from 'nprogress' // 引入路由进度条库
import 'nprogress/nprogress.css' // 引入进度条样式

// ==================== 页面组件引入 ====================
// 登录页组件
const Login = () => import('@/views/counselor/Login.vue')
// 考试状态页组件
const ExamStatus = () => import('@/views/counselor/ExamStatus.vue')
// 考前等待页组件
const ExamWaiting = () => import('@/views/counselor/ExamWaiting.vue')
// 考试答题页组件
const ExamDo = () => import('@/views/counselor/ExamDo.vue')
// 收藏夹页面组件
const Collection = () => import('@/views/counselor/Collection.vue')
// 练习页面组件
const Practice = () => import('@/views/counselor/Practice.vue')

// 管理员端页面组件
const AdminLayout = () => import('@/layout/AdminLayout.vue')
const CorrectList = () => import('@/views/admin/CorrectList.vue')
const CorrectDo = () => import('@/views/admin/CorrectDo.vue')
const Statistics = () => import('@/views/admin/Statistics.vue')
const UserManage = () => import('@/views/admin/UserManage.vue')
const QuestionManage = () => import('@/views/admin/QuestionManage.vue')
const ExamManage = () => import('@/views/admin/ExamManage.vue')
const LogManage = () => import('@/views/admin/LogManage.vue')

// 超级管理员页面组件
const SuperAdminLayout = () => import('@/layout/SuperAdminLayout.vue')
const SuperAdminHome = () => import('@/views/super-admin/Home.vue')
const Inquire = () => import('@/views/super-admin/Inquire.vue')
const Setexam = () => import('@/views/super-admin/Setexam.vue')
const Checkexamstate = () => import('@/views/super-admin/Checkexamstate.vue')
const ExamCheck = () => import('@/views/super-admin/ExamCheck.vue')
const AddQuestion = () => import('@/views/super-admin/AddQuestion.vue')

const ImportDatabase = () => import('@/views/super-admin/ImportDatabase.vue')

// 配置路由进度条
NProgress.configure({ showSpinner: false }) // 配置进度条不显示加载图标

// ==================== 路由配置 ====================
const routes = [
  {
    path: '/', // 根路径
    redirect: '/login', // 重定向到登录页
  },
  {
    path: '/login', // 登录页路由
    name: 'Login', // 路由名称
    component: Login, // 对应组件
    meta: { title: '登录', requiresAuth: false }, // 元信息：页面标题、不需要登录验证
  },
  {
    path: '/exam-status', // 考试状态页路由
    name: 'ExamStatus', // 路由名称
    component: ExamStatus, // 对应组件
    meta: { title: '考试状态', requiresAuth: false }, // 元信息：页面标题
  },
  {
    path: '/exam-do', // 考试答题页路由
    name: 'ExamDo', // 路由名称
    component: ExamDo, // 对应组件
    meta: { title: '答题', requiresAuth: false }, // 元信息：页面标题
  },
  {
    path: '/exam-waiting', // 考前等待页路由
    name: 'ExamWaiting', // 路由名称
    component: ExamWaiting, // 对应组件
    meta: { title: '考前等待', requiresAuth: false }, // 元信息：页面标题
  },
  {
    path: '/collection', // 收藏夹页面路由
    name: 'Collection', // 路由名称
    component: Collection, // 对应组件
    meta: { title: '收藏夹', requiresAuth: false },
  },
  {
    path: '/practice', // 练习页面路由
    name: 'Practice', // 路由名称
    component: Practice, // 对应组件
    meta: { title: '日常练习', requiresAuth: false }, // 元信息：页面标题
  },

  // ==================== 管理员端路由 ====================
  {
    path: '/admin/correct-list',
    name: 'CorrectList',
    component: CorrectList,
    meta: { title: '成绩管理', requiresAuth: true },
  },
  {
    path: '/admin/import-score',
    name: 'ImportScore',
    component: () => import('@/views/admin/ImportScore.vue'),
    meta: { title: '手动录入成绩', requiresAuth: true },
  },
  {
    path: '/admin/correct-do',
    name: 'CorrectDo',
    component: CorrectDo,
    meta: { title: '批改详情', requiresAuth: true },
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { title: '管理员', requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/admin/correct-list',
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: Statistics,
        meta: { title: '考试统计', requiresAuth: true },
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: UserManage,
        meta: { title: '用户管理', requiresAuth: true },
      },
      {
        path: 'question-manage',
        name: 'QuestionManage',
        component: QuestionManage,
        meta: { title: '题库管理', requiresAuth: true },
      },
      {
        path: 'exam-manage',
        name: 'ExamManage',
        component: ExamManage,
        meta: { title: '考试管理', requiresAuth: true },
      },
      {
        path: 'log-manage',
        name: 'LogManage',
        component: LogManage,
        meta: { title: '日志管理', requiresAuth: true },
      },
    ],
  },

  // 超级管理员路由
  {
    path: '/super-admin',
    component: SuperAdminLayout,
    meta: { title: '超级管理员', requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/super-admin/home',
      },
      {
        path: 'home',
        name: 'SuperAdminHome',
        component: SuperAdminHome,
        meta: { title: '超级管理员首页', requiresAuth: true },
      },
      {
        path: 'inquire',
        name: 'Inquire',
        component: Inquire,
        meta: { title: '查询考试信息', requiresAuth: true },
      },
      {
        path: 'setexam',
        name: 'Setexam',
        component: Setexam,
        meta: { title: '考试配置', requiresAuth: true },
      },
      {
        path: 'checkexamstate',
        name: 'Checkexamstate',
        component: Checkexamstate,
        meta: { title: '考试监控', requiresAuth: true },
      },
      {
        path: 'exam-check',
        name: 'ExamCheck',
        component: ExamCheck,
        meta: { title: '试卷检查', requiresAuth: true },
      },
      {
        path: 'question-manage',
        name: 'SuperQuestionManage',
        component: AddQuestion,
        meta: { title: '题库管理', requiresAuth: true },
      },

      {
        path: 'import-database',
        name: 'ImportDatabase',
        component: ImportDatabase,
        meta: { title: '导入数据库', requiresAuth: true },
      },
    ],
  },
]

// ==================== 创建路由实例 ====================
const router = createRouter({
  history: createWebHistory(), // 使用HTML5 History模式，URL不带#号
  routes: routes, // 路由配置
})

// ==================== 路由前置守卫 ====================
router.beforeEach((to, from, next) => {
  // 开始显示路由进度条
  NProgress.start()
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 辅导员考试系统` : '辅导员考试系统'

  // 检查是否需要登录验证
  if (to.meta.requiresAuth) {
    // 获取localStorage中的用户信息和Token
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || 'null')
    const token = localStorage.getItem('token') || ''

    // 检查是否已登录
    if (!token || !userInfo) {
      // 未登录，跳转到统一登录页
      next('/login')
      return
    }

    // 检查是否为管理员路径
    if (to.path.startsWith('/admin') && ![2, 3].includes(userInfo.role)) {
      // 不是管理员( role=2或3 )，却访问管理员页面，跳转到登录页
      ElMessage.warning('您没有权限访问管理员页面')
      next('/login')
      return
    }

    // 检查是否为超级管理员路径
    if (to.path.startsWith('/super-admin') && userInfo.role !== 3) {
      // 不是超级管理员( role!=3 )，却访问超级管理员页面，跳转到登录页
      ElMessage.warning('您没有权限访问该页面')
      next('/login')
      return
    }
  }

  // 路由放行
  next()
})

// ==================== 路由后置守卫 ====================
router.afterEach(() => {
  // 结束路由进度条
  NProgress.done()
})

// 导出路由实例
export default router
