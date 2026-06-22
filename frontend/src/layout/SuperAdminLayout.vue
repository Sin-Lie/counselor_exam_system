/** * 超级管理员布局组件 * 包含顶部用户信息和下方功能入口 */
<template>
  <div class="super-admin-layout">
    <!-- ==================== 顶部用户信息栏 ==================== -->
    <div class="top-bar">
      <div class="user-section">
        <!-- 用户头像 -->
        <el-avatar :size="40" icon="UserFilled" class="user-avatar" />
        <!-- 超级管理员信息 -->
        <div class="user-details">
          <span class="user-label">超级管理员</span>
          <span class="user-job-number"
            >工号：{{
              userStore.userInfo?.jobNumber || userStore.userInfo?.username || '未知'
            }}</span
          >
        </div>
      </div>
      <div class="action-section">
        <el-button type="danger" plain size="small" @click="handleLogout"> 退出登录 </el-button>
      </div>
    </div>

    <!-- ==================== 功能入口区域 ==================== -->
    <div class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup>
/**
 * 超级管理员布局组件逻辑
 */
import { useRouter } from 'vue-router' // 引入Vue Router
import { ElMessage, ElMessageBox } from 'element-plus' // 引入Element Plus消息和确认框组件
import { useUserStore } from '@/stores/user' // 引入用户状态管理

// ==================== 路由和状态管理 ====================
const router = useRouter() // 获取路由导航实例
const userStore = useUserStore() // 获取用户状态管理实例

// ==================== 用户操作处理 ====================
/**
 * 退出登录处理
 */
async function handleLogout() {
  try {
    // 弹出确认对话框
    await ElMessageBox.confirm(
      '确定要退出登录吗？', // 确认消息内容
      '退出登录', // 对话框标题
      {
        confirmButtonText: '确定', // 确认按钮文字
        cancelButtonText: '取消', // 取消按钮文字
        type: 'warning', // 警告类型图标
      },
    )
    // 用户确认后，执行登出
    await userStore.logout() // 调用登出方法
    ElMessage.success('已退出登录') // 显示成功提示
    router.push('/login') // 跳转到统一登录页面
  } catch (e) {
    // 用户取消操作，不做任何处理
  }
}
</script>

<style scoped>
/**
 * 超级管理员布局组件样式
 */

/* 整体布局容器 */
.super-admin-layout {
  width: 100vw; /* 占满整个视口宽度 */
  height: 100vh; /* 占满整个视口高度 */
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直方向排列 */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* 紫色渐变背景 */
}

/* ==================== 顶部用户信息栏 ==================== */
.top-bar {
  display: flex; /* 弹性布局 */
  justify-content: space-between; /* 左右分散对齐 */
  align-items: center; /* 垂直居中对齐 */
  padding: 16px 30px; /* 内边距 */
  background-color: rgba(255, 255, 255, 0.95); /* 半透明白色背景 */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1); /* 阴影效果 */
}

/* 用户信息区域 */
.user-section {
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 15px; /* 间距15px */
}

/* 用户头像 */
.user-avatar {
  background-color: #764ba2; /* 紫色背景 */
}

/* 用户详情 */
.user-details {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  gap: 4px; /* 小间距 */
}

/* 用户标签 */
.user-label {
  font-size: 14px; /* 字号 */
  color: #764ba2; /* 紫色文字 */
  font-weight: 600; /* 粗体 */
}

/* 工号信息 */
.user-job-number {
  font-size: 13px; /* 字号 */
  color: #666; /* 灰色文字 */
}

/* ==================== 主内容区域 ==================== */
.main-content {
  flex: 1; /* 占据剩余空间 */
  overflow-y: auto; /* 垂直滚动 */
  padding: 30px; /* 内边距 */
}

/* ==================== 路由过渡动画 ==================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease; /* 透明度过渡动画 */
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0; /* 开始和结束时的透明度为0 */
}
</style>
