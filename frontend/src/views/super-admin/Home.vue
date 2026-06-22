/**
 * 超级管理员首页组件
 * 展示6个功能入口
 */
<template>
  <div class="super-admin-home">
    <!-- 功能入口网格 -->
    <div class="function-grid">
      <!-- 查询 -->
      <div class="function-card" @click="handleFunction('query')">
        <div class="card-icon">
          <el-icon :size="48"><Search /></el-icon>
        </div>
        <div class="card-title">查询</div>
        <div class="card-desc">查询考试信息和成绩</div>
      </div>

      <!-- 考试配置 -->
      <div class="function-card" @click="handleFunction('exam')">
        <div class="card-icon">
          <el-icon :size="48"><Setting /></el-icon>
        </div>
        <div class="card-title">考试配置</div>
        <div class="card-desc">创建和配置考试</div>
      </div>

      <!-- 考试监控 -->
      <div class="function-card" @click="handleFunction('status')">
        <div class="card-icon">
          <el-icon :size="48"><Monitor /></el-icon>
        </div>
        <div class="card-title">考试监控</div>
        <div class="card-desc">实时监控考试状态</div>
      </div>

      <!-- 试卷检查 -->
      <div class="function-card" @click="handleFunction('examCheck')">
        <div class="card-icon">
          <el-icon :size="48"><Document /></el-icon>
        </div>
        <div class="card-title">试卷检查</div>
        <div class="card-desc">查看试卷批改情况</div>
      </div>

      <!-- 题库管理 -->
      <div class="function-card" @click="handleFunction('question')">
        <div class="card-icon">
          <el-icon :size="48"><DocumentAdd /></el-icon>
        </div>
        <div class="card-title">题库管理</div>
        <div class="card-desc">管理题库中的题目</div>
      </div>

      <!-- 导入数据库 -->
      <div class="function-card" @click="handleFunction('database')">
        <div class="card-icon">
          <el-icon :size="48"><Connection /></el-icon>
        </div>
        <div class="card-title">导入数据库</div>
        <div class="card-desc">导入外部数据到系统</div>
      </div>
    </div>

    <!-- 功能开发中提示弹窗 -->
    <el-dialog
      v-model="showTipDialog"
      title="提示"
      width="400px"
    >
      <div class="tip-content">
        <el-icon :size="48" color="#909399"><InfoFilled /></el-icon>
        <p>该功能正在开发中，敬请期待！</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="showTipDialog = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 超级管理员首页逻辑
 */
import { ref } from 'vue'; // 引入Vue的响应式API
import { useRouter } from 'vue-router'; // 引入Vue Router
import { ElMessage } from 'element-plus'; // 引入Element Plus消息组件
import { Search, Setting, Monitor, Document, DocumentAdd, Connection, InfoFilled } from '@element-plus/icons-vue'; // 引入Element Plus图标

// ==================== 状态定义 ====================
const router = useRouter(); // 获取路由实例
const showTipDialog = ref(false); // 提示弹窗显示状态

// ==================== 方法定义 ====================
/**
 * 处理功能入口点击
 * @param {string} functionName - 功能名称
 */
function handleFunction(functionName) {
  // 根据功能名称执行对应操作
  switch (functionName) {
    case 'query':
      router.push('/super-admin/inquire');
      break;
    case 'exam':
      router.push('/super-admin/setexam');
      break;
    case 'status':
      router.push('/super-admin/checkexamstate');
      break;
    case 'examCheck':
      router.push('/super-admin/exam-check');
      break;
    case 'question':
      router.push('/super-admin/question-manage');
      break;

    case 'database':
      router.push('/super-admin/import-database');
      break;
    default:
      ElMessage.info('功能开发中');
  }
}
</script>

<style scoped>
/**
 * 超级管理员首页样式
 */

/* 页面容器 */
.super-admin-home {
  height: 100%; /* 占满父容器高度 */
}

/* ==================== 功能网格布局 ==================== */
.function-grid {
  display: grid; /* 网格布局 */
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); /* 自动填充列，最小280px */
  gap: 30px; /* 网格间距30px */
  padding: 20px; /* 内边距 */
}

/* ==================== 功能卡片样式 ==================== */
.function-card {
  background: linear-gradient(145deg, #ffffff 0%, #f8f9ff 100%); /* 白色到淡紫色渐变 */
  border-radius: 16px; /* 圆角16px */
  padding: 40px 30px; /* 内边距 */
  text-align: center; /* 文字居中 */
  cursor: pointer; /* 鼠标指针 */
  transition: all 0.3s ease; /* 过渡效果 */
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); /* 阴影效果 */
  border: 1px solid rgba(118, 75, 162, 0.1); /* 淡紫色边框 */
}

/* 卡片悬停效果 */
.function-card:hover {
  transform: translateY(-8px); /* 向上移动8px */
  box-shadow: 0 12px 30px rgba(118, 75, 162, 0.2); /* 加深阴影 */
  border-color: rgba(118, 75, 162, 0.4); /* 加深边框颜色 */
}

/* 卡片图标容器 */
.card-icon {
  width: 80px; /* 图标容器宽度 */
  height: 80px; /* 图标容器高度 */
  margin: 0 auto 20px; /* 居中，底部间距20px */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* 紫色渐变背景 */
  border-radius: 50%; /* 圆形 */
  display: flex; /* 弹性布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  color: #fff; /* 白色图标 */
}

/* 卡片标题 */
.card-title {
  font-size: 20px; /* 标题字号 */
  font-weight: 600; /* 粗体 */
  color: #333; /* 深灰色文字 */
  margin-bottom: 10px; /* 底部间距 */
}

/* 卡片描述 */
.card-desc {
  font-size: 14px; /* 描述字号 */
  color: #999; /* 浅灰色文字 */
}

/* ==================== 提示弹窗内容 ==================== */
.tip-content {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  align-items: center; /* 居中 */
  gap: 15px; /* 间距 */
  padding: 20px 0; /* 上下内边距 */
}

.tip-content p {
  font-size: 16px; /* 字号 */
  color: #666; /* 灰色文字 */
  margin: 0; /* 清除默认外边距 */
}
</style>
