/** * 管理员端布局组件 * 包含顶部导航栏和左侧菜单，提供管理员端的整体页面布局结构 */
<template>
  <el-container class="admin-layout">
    <!-- 使用Element Plus的Container容器组件 -->
    <!-- ==================== 顶部导航栏 ==================== -->
    <el-header class="layout-header">
      <div class="header-left">
        <!-- 系统标题 -->
        <h1 class="system-title">考试管理系统</h1>
        <!-- 系统名称标题 -->
      </div>
      <div class="header-right">
        <!-- 欢迎信息和用户菜单 -->
        <el-dropdown @command="handleCommand">
          <!-- 下拉菜单组件 -->
          <span class="user-info">
            <!-- 用户头像，使用UI头像组件 -->
            <el-avatar :size="32" icon="UserFilled" />
            <!-- 32像素的圆形头像 -->
            <span class="username">{{ userStore.userName }}</span>
            <!-- 显示用户名 -->
            <el-tag v-if="userStore.isSuperAdmin" type="danger" size="small">超级管理员</el-tag>
            <!-- 超级管理员标签 -->
            <el-tag v-else type="warning" size="small">管理员</el-tag>
            <!-- 管理员标签 -->
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            <!-- 向下箭头图标 -->
          </span>
          <!-- 下拉菜单选项 -->
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="info">系统设置</el-dropdown-item>
              <!-- 系统设置选项 -->
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              <!-- 退出登录选项，带分隔线 -->
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <!-- ==================== 主体内容区域 ==================== -->
    <el-container class="layout-main">
      <!-- ==================== 左侧菜单 ==================== -->
      <el-aside class="layout-aside" :width="isCollapse ? '64px' : '220px'">
        <!-- 左侧菜单组件 -->
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          class="layout-menu"
        >
          <!-- 批改管理菜单组 -->
          <el-sub-menu index="correct">
            <template #title>
              <el-icon><Edit /></el-icon>
              <!-- 批改图标 -->
              <span>批改管理</span>
              <!-- 菜单标题 -->
            </template>
            <!-- 批改列表子菜单 -->
            <el-menu-item index="/admin/correct-list">待批改列表</el-menu-item>
            <!-- 待批改列表选项 -->
          </el-sub-menu>

          <!-- 考试统计菜单项 -->
          <el-menu-item index="/admin/statistics">
            <el-icon><DataAnalysis /></el-icon>
            <!-- 统计图标 -->
            <template #title>考试统计</template>
            <!-- 菜单标题 -->
          </el-menu-item>

          <!-- 用户管理菜单项 -->
          <el-menu-item index="/admin/user-manage">
            <el-icon><User /></el-icon>
            <!-- 用户图标 -->
            <template #title>用户管理</template>
            <!-- 菜单标题 -->
          </el-menu-item>

          <!-- 题库管理菜单项 -->
          <el-menu-item index="/admin/question-manage">
            <el-icon><Document /></el-icon>
            <!-- 题库图标 -->
            <template #title>题库管理</template>
            <!-- 菜单标题 -->
          </el-menu-item>

          <!-- 考试管理菜单项 -->
          <el-menu-item index="/admin/exam-manage">
            <el-icon><Files /></el-icon>
            <!-- 考试图标 -->
            <template #title>考试管理</template>
            <!-- 菜单标题 -->
          </el-menu-item>

          <!-- 日志管理菜单项 -->
          <el-menu-item index="/admin/log-manage">
            <el-icon><Clock /></el-icon>
            <!-- 日志图标 -->
            <template #title>日志管理</template>
            <!-- 菜单标题 -->
          </el-menu-item>
        </el-menu>

        <!-- 菜单折叠按钮 -->
        <div class="collapse-btn" @click="toggleCollapse">
          <el-icon v-if="isCollapse"><DArrowRight /></el-icon>
          <!-- 展开时显示右箭头 -->
          <el-icon v-else><DArrowLeft /></el-icon>
          <!-- 折叠时显示左箭头 -->
        </div>
      </el-aside>

      <!-- ==================== 内容区域 ==================== -->
      <el-main class="layout-content">
        <!-- 面包屑导航 -->
        <el-breadcrumb separator="/" class="breadcrumb">
          <el-breadcrumb-item :to="{ path: '/admin' }">首页</el-breadcrumb-item>
          <!-- 首页面包屑 -->
          <el-breadcrumb-item v-if="route.meta.title !== '首页'">{{
            route.meta.title
          }}</el-breadcrumb-item>
          <!-- 当前页面面包屑 -->
        </el-breadcrumb>

        <!-- 路由视图，显示当前路由对应的页面组件 -->
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
/**
 * 管理员布局组件逻辑
 * 管理菜单状态、用户信息和退出登录等功能
 */
import { ref, computed } from 'vue' // 引入Vue的响应式API
import { useRoute, useRouter } from 'vue-router' // 引入Vue Router
import { ElMessage, ElMessageBox } from 'element-plus' // 引入Element Plus消息和确认框组件
import {
  Edit,
  DataAnalysis,
  User,
  Document,
  Files,
  Clock,
  ArrowDown,
  DArrowLeft,
  DArrowRight,
} from '@element-plus/icons-vue' // 引入Element Plus图标
import { useUserStore } from '@/stores/user' // 引入用户状态管理

// ==================== 路由和状态管理 ====================
const route = useRoute() // 获取当前路由实例
const router = useRouter() // 获取路由导航实例
const userStore = useUserStore() // 获取用户状态管理实例

// ==================== 菜单状态 ====================
// 菜单折叠状态
const isCollapse = ref(false) // 默认展开状态

/**
 * 切换菜单折叠状态
 */
function toggleCollapse() {
  isCollapse.value = !isCollapse.value // 取反当前折叠状态
}

// ==================== 计算属性 ====================
// 当前激活的菜单项，根据当前路由路径计算
const activeMenu = computed(() => {
  return route.path // 直接返回当前路由路径
})

// ==================== 用户操作处理 ====================
/**
 * 处理下拉菜单命令
 * @param {string} command - 菜单命令标识
 */
async function handleCommand(command) {
  if (command === 'logout') {
    // 退出登录命令
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
  } else if (command === 'info') {
    // 系统设置命令，使用消息提示
    ElMessage.info('功能开发中')
  }
}
</script>

<style scoped>
/**
 * 管理员布局组件样式
 * 使用 scoped 限定样式作用域，避免污染全局样式
 */

/* 整体布局容器样式 */
.admin-layout {
  height: 100vh; /* 占满整个视口高度 */
}

/* ==================== 顶部导航栏样式 ==================== */
.layout-header {
  display: flex; /* 使用弹性布局 */
  justify-content: space-between; /* 左右两侧分散对齐 */
  align-items: center; /* 垂直居中对齐 */
  background-color: #303133; /* 深灰色背景色 */
  color: #fff; /* 白色文字颜色 */
  padding: 0 20px; /* 左右内边距20px */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* 底部阴影效果 */
}

/* 系统标题样式 */
.system-title {
  margin: 0; /* 清除默认外边距 */
  font-size: 20px; /* 标题字号 */
  font-weight: 600; /* 标题字重 */
}

/* 用户信息区域样式 */
.user-info {
  display: flex; /* 使用弹性布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 10px; /* 子元素之间10px间距 */
  cursor: pointer; /* 鼠标指针样式 */
  color: #fff; /* 白色文字 */
}

/* 用户名样式 */
.username {
  font-size: 14px; /* 用户名字号 */
}

/* ==================== 主体区域样式 ==================== */
.layout-main {
  height: calc(100vh - 60px); /* 计算高度，减去顶部导航栏高度 */
}

/* ==================== 左侧菜单样式 ==================== */
.layout-aside {
  background-color: #304156; /* 深蓝灰色背景 */
  position: relative; /* 相对定位，用于内部元素定位 */
  transition: width 0.3s; /* 宽度过渡动画0.3秒 */
}

/* 菜单样式 */
.layout-menu {
  border-right: none; /* 移除右边框 */
  background-color: transparent; /* 透明背景 */
}

/* ==================== 折叠按钮样式 ==================== */
.collapse-btn {
  position: absolute; /* 绝对定位 */
  bottom: 20px; /* 距离底部20px */
  left: 50%; /* 水平居中 */
  transform: translateX(-50%); /* 向左偏移自身宽度的一半 */
  width: 32px; /* 按钮宽度32px */
  height: 32px; /* 按钮高度32px */
  background-color: #fff; /* 白色背景 */
  border-radius: 4px; /* 圆角4px */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  cursor: pointer; /* 鼠标指针样式 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* 阴影效果 */
  color: #409eff; /* 图标颜色 */
}

/* 折叠按钮悬停效果 */
.collapse-btn:hover {
  background-color: #ecf5ff; /* 悬停时浅蓝色背景 */
}

/* ==================== 内容区域样式 ==================== */
.layout-content {
  background-color: #f0f2f5; /* 浅灰蓝色背景 */
  padding: 20px; /* 内边距20px */
  overflow-y: auto; /* 内容溢出时显示垂直滚动条 */
}

/* ==================== 面包屑导航样式 ==================== */
.breadcrumb {
  margin-bottom: 20px; /* 底部外边距20px */
}

/* ==================== 路由过渡动画 ==================== */
/* 淡入淡出过渡效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease; /* 透明度过渡动画0.2秒 */
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0; /* 开始和结束时的透明度为0 */
}
</style>
