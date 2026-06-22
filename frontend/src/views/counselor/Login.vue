/** * 登录页面组件 * 提供用户登录功能 */
<template>
  <div class="login-page">
    <!-- 登录框 -->
    <div class="login-container">
      <!-- 顶部标题区 -->
      <div class="login-header">
        <img src="@/assets/标题.png" alt="生情熟知" class="logo" />
      </div>

      <!-- 登录表单 -->
      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
        <!-- 用户名输入框 -->
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            clearable
            @keyup.enter="handleLogin"
            size="large"
          >
            <template #prefix>
              <img src="@/assets/默认头像.png" alt="用户" class="input-icon" />
            </template>
          </el-input>
        </el-form-item>

        <!-- 密码输入框 -->
        <el-form-item prop="password" class="password-item">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            clearable
            @keyup.enter="handleLogin"
            size="large"
          >
            <template #prefix>
              <img src="@/assets/锁定.png" alt="锁定" class="input-icon" />
            </template>
          </el-input>
        </el-form-item>

        <!-- 角色选择 -->
        <el-form-item prop="role">
          <div class="role-selector">
            <el-radio-group v-model="loginForm.role" class="role-radio-group">
              <el-radio value="counselor" class="role-radio">辅导员</el-radio>
              <el-radio value="admin" class="role-radio">管理员</el-radio>
            </el-radio-group>
          </div>
        </el-form-item>

        <!-- 登录按钮 -->
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-button" @click="handleLogin">
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部链接 -->
      <div class="login-footer"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue' // 引入Vue响应式API
import { useRouter } from 'vue-router' // 引入Vue Router
import { ElMessage } from 'element-plus' // 引入Element Plus消息组件
import { counselorLogin, adminLogin } from '@/api/auth' // 引入登录API

const router = useRouter() // 获取路由导航实例
const loading = ref(false) // 登录按钮加载状态
const loginFormRef = ref(null) // 表单引用

// 登录表单数据
const loginForm = reactive({
  username: '', // 用户名/账号
  password: '', // 密码
  role: '', // 角色，默认为空
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }, // 用户名必填验证
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }, // 密码必填验证
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }, // 角色必填验证
  ],
}

/**
 * 处理登录按钮点击
 * 根据V1.5接口文档实现登录逻辑
 * 支持后端不可用时使用模拟数据登录
 */
async function handleLogin() {
  // 表单验证
  try {
    await loginFormRef.value.validate()
  } catch (error) {
    return // 验证失败，不提交
  }

  // 执行登录
  loading.value = true

  try {
    // 调用后端接口登录
    const loginData = {
      username: loginForm.username,
      password: loginForm.password,
    }

    let response
    if (loginForm.role === 'counselor') {
      response = await counselorLogin(loginData)
    } else {
      response = await adminLogin(loginData)
    }

      // 检查响应是否成功（响应拦截器已将数据扁平化）
      if (response.code === 200 && response.token) {
        // 登录成功
        // 保存token和用户信息到localStorage
        localStorage.setItem('token', response.token)
        localStorage.setItem('userInfo', JSON.stringify(response))

        ElMessage.success(`${response.msg}，欢迎 ${response.name || '用户'}！`)

        // 根据用户角色跳转到不同页面
        if (response.role === 3) {
          // 超级管理员
          router.push('/super-admin')
        } else if (loginForm.role === 'counselor' || response.role === 1) {
          router.push('/exam-status') // 辅导员跳转到考试状态页
        } else {
          router.push('/admin') // 管理员跳转到管理后台
        }
      } else {
        // 登录失败
        ElMessage.error(response.msg || '登录失败，请稍后重试')
      }
  } catch (error) {
    console.error('登录失败', error)
    // 错误信息已经在响应拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/**
 * 登录页面样式
 */
.login-page {
  display: flex; /* 弹性布局 */
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  min-height: 100vh; /* 占满整个视口高度 */
  background: url('@/assets/登录背景.png') no-repeat center center; /* 设置背景图片并居中 */
  background-size: cover; /* 背景图片覆盖整个容器 */
  padding: 10px; /* 内边距20px */
}

/* ==================== 登录框样式 ==================== */
.login-container {
  width: 400px; /* 登录框宽度400px，放大1.25倍 */
  padding: 50px; /* 内边距放大1.25倍 */
  background-color: #f0f8ff; /* 浅蓝色背景，与标题背景颜色相同 */
  border-radius: 15px; /* 圆角放大1.25倍 */
  box-shadow: 0 12.5px 50px rgba(0, 0, 0, 0.15); /* 阴影效果放大1.25倍 */
  max-width: 90%; /* 最大宽度90%，响应式 */
  margin-left: 600px; /* 向右移动50px，可根据需要调整此值 */

  height: 500px; /* 高度放大1.25倍 */
}

/* ==================== 登录头部样式 ==================== */
.login-header {
  text-align: center; /* 居中对齐 */
  margin-bottom: 37.5px; /* 底部外边距放大1.25倍 */
}

.logo {
  width: 120%; /* 图片宽度比登录框宽10% */
  height: auto; /* 高度自动，保持比例 */
  margin-left: -10%; /* 向左偏移5%，使图片居中 */
}

/* ==================== 登录表单样式 ==================== */
.login-form {
  margin-bottom: 20px; /* 底部外边距放大1.25倍 */
}

.login-button {
  width: 100%; /* 按钮宽度100% */
  height: 40px; /* 按钮高度放大1.25倍 */
  font-size: 20px; /* 字号放大1.25倍 */
  border-radius: 10px; /* 圆角放大1.25倍 */
}

/* ==================== 输入框图标样式 ==================== */
.input-icon {
  width: 25px; /* 图标宽度放大1.25倍 */
  height: 25px; /* 图标高度放大1.25倍 */
  margin-right: 12.5px; /* 图标与输入文本间距放大1.25倍 */
  vertical-align: middle; /* 垂直居中对齐 */
}
/* ==================== 角色选择样式 ==================== */
.role-selector {
  width: 100%; /* 宽度100%，与登录按钮对齐 */
}

.role-radio-group {
  display: flex; /* 弹性布局 */
  justify-content: space-between; /* 两端对齐 */
  width: 100%; /* 宽度100% */
}

.role-radio {
  font-size: 17.5px; /* 字号放大1.25倍 */
}

.role-radio .el-radio__input {
  transform: scale(1.4); /* 单选框放大1.4倍 */
}

/* ==================== 底部链接样式 ==================== */
.login-footer {
  display: flex; /* 弹性布局 */
  justify-content: space-between; /* 两端对齐 */
  align-items: center; /* 垂直居中 */
  margin-top: 25px; /* 顶部外边距放大1.25倍 */
}

.footer-link {
  font-size: 17.5px; /* 字号放大1.25倍 */
  color: #409eff; /* 蓝色 */
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 768px) {
  .login-container {
    width: 100%; /* 宽度100% */
    padding: 37.5px 25px; /* 内边距放大1.25倍 */
    height: auto; /* 高度自适应 */
  }

  .logo {
    max-width: 187.5px; /* 图片最大宽度放大1.25倍 */
  }
}
</style>
