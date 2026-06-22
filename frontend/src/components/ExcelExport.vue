/**
 * Excel导出组件
 * 提供数据导出功能，支持自定义导出参数
 * 用于导出考试成绩、用户列表、统计报表等数据
 */
<template>
  <div class="excel-export">
    <!-- ==================== 导出按钮 ==================== -->
    <el-button
      :type="buttonType"
      :icon="isExporting ? 'Loading' : 'Download'"
      :disabled="isExporting"
      @click="handleExport"
    >
      {{ buttonText }}
    </el-button>

    <!-- ==================== 导出进度提示 ==================== -->
    <el-dialog
      v-model="showProgress"
      title="导出中"
      width="300px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="export-progress">
        <el-progress :percentage="progressPercent" :status="progressStatus" />
        <p class="progress-message">{{ progressMessage }}</p>
      </div>
    </el-dialog>

    <!-- ==================== 导出结果提示 ==================== -->
    <el-dialog
      v-model="showResult"
      title="导出结果"
      width="400px"
    >
      <div class="export-result">
        <el-result
          v-if="exportSuccess"
          icon="success"
          title="导出成功"
          sub-title="文件已开始下载，请注意查收"
        />
        <el-result
          v-else
          icon="error"
          title="导出失败"
          :sub-title="errorMessage"
        >
          <template #extra>
            <el-button type="primary" @click="handleRetry">重试</el-button>
          </template>
        </el-result>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * Excel导出组件逻辑
 * 处理导出请求、进度显示、结果反馈等功能
 */
import { ref, computed } from 'vue'; // 引入Vue响应式API
import { ElMessage } from 'element-plus'; // 引入Element Plus消息组件
import { Download } from '@element-plus/icons-vue'; // 引入Element Plus图标

// ==================== Props定义 ====================
const props = defineProps({
  exportUrl: {
    type: String,
    required: true, // 导出请求地址必填
  },
  fileName: {
    type: String,
    default: '导出数据', // 默认文件名
  },
  buttonText: {
    type: String,
    default: '导出Excel', // 默认按钮文本
  },
  buttonType: {
    type: String,
    default: 'primary', // 默认按钮类型
  },
  queryParams: {
    type: Object,
    default: () => ({}), // 导出时携带的查询参数
  },
  method: {
    type: String,
    default: 'get', // 请求方法，默认GET
  },
});

// ==================== 事件定义 ====================
const emit = defineEmits(['success', 'error', 'complete']); // 定义导出成功、失败、完成事件

// ==================== 状态定义 ====================
const isExporting = ref(false); // 导出中状态
const showProgress = ref(false); // 显示进度对话框
const showResult = ref(false); // 显示结果对话框
const progressPercent = ref(0); // 进度百分比
const progressStatus = ref(''); // 进度状态
const progressMessage = ref('正在准备导出...'); // 进度消息
const exportSuccess = ref(false); // 导出是否成功
const errorMessage = ref(''); // 错误消息

// ==================== 方法定义 ====================
/**
 * 处理导出按钮点击
 */
async function handleExport() {
  try {
    await performExport();
  } catch (error) {
    console.error('导出失败', error);
  }
}

/**
 * 执行导出操作
 */
async function performExport() {
  // 防止重复导出
  if (isExporting.value) {
    return;
  }

  // 显示进度对话框
  isExporting.value = true;
  showProgress.value = true;
  progressPercent.value = 0;
  progressStatus.value = '';
  progressMessage.value = '正在准备导出...';

  try {
    // 准备导出参数
    const params = { ...props.queryParams };

    // 使用fetch API进行导出请求（支持大文件下载）
    const token = localStorage.getItem('token');
    const url = new URL(props.exportUrl, window.location.origin);
    Object.keys(params).forEach((key) => {
      if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
        url.searchParams.append(key, params[key]);
      }
    });

    progressMessage.value = '正在请求数据...';
    progressPercent.value = 20;

    // 发起fetch请求
    const response = await fetch(url.toString(), {
      method: props.method,
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      ...(props.method.toLowerCase() === 'post' ? { body: JSON.stringify(params) } : {}),
    });

    progressMessage.value = '正在处理数据...';
    progressPercent.value = 50;

    // 检查响应状态
    if (!response.ok) {
      throw new Error(`请求失败: ${response.status} ${response.statusText}`);
    }

    // 获取文件名（从Content-Disposition头获取）
    const contentDisposition = response.headers.get('Content-Disposition');
    let downloadFileName = `${props.fileName}.xlsx`;

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        downloadFileName = decodeURIComponent(filenameMatch[1].replace(/['"]/g, ''));
      }
    }

    progressMessage.value = '正在下载文件...';
    progressPercent.value = 80;

    // 获取blob数据
    const blob = await response.blob();

    // 检查blob是否为空或错误提示
    if (blob.size === 0) {
      throw new Error('导出文件为空');
    }

    // 检查是否是JSON错误响应（有时候服务器返回JSON而不是文件）
    if (blob.type === 'application/json') {
      const text = await blob.text();
      const json = JSON.parse(text);
      throw new Error(json.message || '导出失败');
    }

    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = downloadFileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);

    // 完成导出
    progressPercent.value = 100;
    progressStatus.value = 'success';
    progressMessage.value = '导出成功！';

    exportSuccess.value = true;
    emit('success');

    // 延迟关闭进度对话框，显示结果
    setTimeout(() => {
      showProgress.value = false;
      showResult.value = true;
    }, 1000);

  } catch (error) {
    // 导出失败
    progressStatus.value = 'exception';
    progressMessage.value = '导出失败';
    exportSuccess.value = false;
    errorMessage.value = error.message || '未知错误';
    emit('error', error);

    // 延迟关闭进度对话框，显示结果
    setTimeout(() => {
      showProgress.value = false;
      showResult.value = true;
    }, 1000);

  } finally {
    // 关闭导出中状态
    setTimeout(() => {
      isExporting.value = false;
    }, 1500);

    emit('complete');
  }
}

/**
 * 处理重试
 */
function handleRetry() {
  showResult.value = false;
  performExport();
}

/**
 * 处理取消（关闭结果对话框）
 */
function handleCloseResult() {
  showResult.value = false;
  progressPercent.value = 0;
  progressStatus.value = '';
  progressMessage.value = '';
}

// 暴露方法给父组件
defineExpose({
  performExport,
  handleRetry,
});
</script>

<style scoped>
/**
 * Excel导出组件样式
 */
.excel-export {
  display: inline-block; /* 行内块级显示 */
}

/* ==================== 导出进度样式 ==================== */
.export-progress {
  padding: 20px 0; /* 上下内边距20px */
}

.progress-message {
  text-align: center; /* 居中对齐 */
  margin-top: 16px; /* 顶部外边距16px */
  font-size: 14px; /* 字号14px */
  color: #606266; /* 中灰色 */
}

/* ==================== 导出结果样式 ==================== */
.export-result {
  padding: 20px 0; /* 上下内边距20px */
}
</style>
