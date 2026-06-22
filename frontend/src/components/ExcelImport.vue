/**
 * Excel导入组件
 * 提供Excel文件导入功能，支持上传、预览、确认导入
 * 用于批量导入辅导员用户或题目数据
 */
<template>
  <div class="excel-import">
    <!-- ==================== 上传区域 ==================== -->
    <el-upload
      ref="uploadRef"
      class="upload-area"
      drag
      :action="uploadUrl"
      :headers="uploadHeaders"
      :data="uploadData"
      :before-upload="handleBeforeUpload"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      :on-progress="handleUploadProgress"
      :disabled="uploading"
      accept=".xlsx,.xls"
      :show-file-list="false"
    >
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="upload-text">
        <span class="main-text">将Excel文件拖到此处，或<em>点击上传</em></span>
        <span class="sub-text">只能上传xlsx/xls文件</span>
      </div>
    </el-upload>

    <!-- ==================== 导入说明 ==================== -->
    <div class="import-tips">
      <el-alert type="info" :closable="false" show-icon>
        <template #title>
          <span>导入说明：</span>
        </template>
        <template #default>
          <ul class="tips-list">
            <li v-for="(tip, index) in tips" :key="index">{{ tip }}</li>
          </ul>
        </template>
      </el-alert>
    </div>

    <!-- ==================== 下载模板按钮 ==================== -->
    <div class="template-section">
      <el-button type="text" @click="handleDownloadTemplate">
        <el-icon><Download /></el-icon>
        下载{{ templateName }}模板
      </el-button>
    </div>

    <!-- ==================== 上传进度 ==================== -->
    <div v-if="uploading" class="upload-progress">
      <el-progress :percentage="uploadPercentage" :status="uploadStatus" />
      <span class="progress-text">{{ uploadMessage }}</span>
    </div>

    <!-- ==================== 导入结果 ==================== -->
    <div v-if="importResult" class="import-result">
      <el-divider content-position="left">导入结果</el-divider>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="总记录数">{{ importResult.total }}</el-descriptions-item>
        <el-descriptions-item label="成功数量">
          <el-tag type="success">{{ importResult.success }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="失败数量">
          <el-tag type="danger">{{ importResult.failed }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="跳过数量">
          <el-tag type="warning">{{ importResult.skipped }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 失败记录预览 -->
      <div v-if="importResult.errors && importResult.errors.length > 0" class="error-preview">
        <h4>失败记录预览：</h4>
        <el-table :data="importResult.errors" size="small" max-height="200">
          <el-table-column prop="row" label="行号" width="60" />
          <el-table-column prop="field" label="字段" width="100" />
          <el-table-column prop="error" label="错误信息" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Excel导入组件逻辑
 * 处理文件上传、进度显示、结果展示等功能
 */
import { ref, computed } from 'vue'; // 引入Vue响应式API
import { ElMessage } from 'element-plus'; // 引入Element Plus消息组件
import { UploadFilled, Download } from '@element-plus/icons-vue'; // 引入Element Plus图标

// ==================== Props定义 ====================
const props = defineProps({
  uploadUrl: {
    type: String,
    required: true, // 上传地址必填
  },
  templateName: {
    type: String,
    default: '数据', // 默认模板名称
  },
  tips: {
    type: Array,
    default: () => [], // 默认提示列表
  },
  uploadData: {
    type: Object,
    default: () => ({}), // 上传时携带的额外数据
  },
});

// ==================== 事件定义 ====================
const emit = defineEmits(['success', 'error', 'complete']); // 定义上传成功、失败、完成事件

// ==================== 状态定义 ====================
const uploadRef = ref(null); // 上传组件引用
const uploading = ref(false); // 上传中状态
const uploadPercentage = ref(0); // 上传进度百分比
const uploadStatus = ref(''); // 上传进度状态
const uploadMessage = ref(''); // 上传消息文本
const importResult = ref(null); // 导入结果数据

// ==================== 计算属性 ====================
// 上传请求头
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token');
  return {
    Authorization: token ? `Bearer ${token}` : '',
  };
});

// ==================== 方法定义 ====================
/**
 * 上传前校验
 * @param {File} file - 上传的文件对象
 * @returns {boolean} 返回是否继续上传
 */
function handleBeforeUpload(file) {
  // 检查文件类型
  const fileName = file.name.toLowerCase();
  if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
    ElMessage.error('只能上传Excel文件(.xlsx, .xls)');
    return false;
  }

  // 检查文件大小（限制10MB）
  const fileSize = file.size / 1024 / 1024;
  if (fileSize > 10) {
    ElMessage.error('文件大小不能超过10MB');
    return false;
  }

  // 开始上传
  uploading.value = true;
  uploadPercentage.value = 0;
  uploadStatus.value = '';
  uploadMessage.value = '正在上传...';
  importResult.value = null;

  return true;
}

/**
 * 上传成功处理
 * @param {Object} response - 服务器响应数据
 * @param {Object} file - 上传的文件对象
 */
function handleUploadSuccess(response, file) {
  uploading.value = false;
  uploadPercentage.value = 100;
  uploadStatus.value = 'success';
  uploadMessage.value = '上传成功！';

  if (response.code === 200) {
    // 保存导入结果
    importResult.value = response.data || {
      total: response.total || 0,
      success: response.success || 0,
      failed: response.failed || 0,
      skipped: response.skipped || 0,
      errors: response.errors || [],
    };

    ElMessage.success(`导入成功！成功${importResult.value.success}条，失败${importResult.value.failed}条`);
    emit('success', importResult.value);
  } else {
    // 上传成功但处理失败
    ElMessage.error(response.message || '导入处理失败');
    uploadStatus.value = 'exception';
    uploadMessage.value = '导入处理失败';
    emit('error', response);
  }

  emit('complete', response);
}

/**
 * 上传失败处理
 * @param {Error} error - 错误对象
 * @param {Object} file - 上传的文件对象
 */
function handleUploadError(error) {
  uploading.value = false;
  uploadPercentage.value = 0;
  uploadStatus.value = 'exception';
  uploadMessage.value = '上传失败';

  ElMessage.error('文件上传失败，请重试');
  emit('error', error);
  emit('complete', null);
}

/**
 * 上传进度处理
 * @param {Object} event - 进度事件对象
 * @param {Object} file - 上传的文件对象
 */
function handleUploadProgress(event, file) {
  if (event.percent) {
    uploadPercentage.value = Math.round(event.percent);
    uploadMessage.value = `正在上传...${uploadPercentage.value}%`;
  }
}

/**
 * 下载模板
 */
function handleDownloadTemplate() {
  ElMessage.info('模板下载功能开发中，请联系管理员获取模板');
  // 实际项目中，这里应该调用模板下载接口或直接提供模板文件URL
}

/**
 * 清除导入结果（外部调用）
 */
function clearResult() {
  importResult.value = null;
  uploadPercentage.value = 0;
  uploadStatus.value = '';
  uploadMessage.value = '';
}

/**
 * 触发文件选择（外部调用）
 */
function triggerUpload() {
  uploadRef.value?.handleClick();
}

// 暴露方法和属性给父组件
defineExpose({
  clearResult,
  triggerUpload,
});
</script>

<style scoped>
/**
 * Excel导入组件样式
 */
.excel-import {
  padding: 20px; /* 内边距20px */
}

/* ==================== 上传区域样式 ==================== */
.upload-area {
  width: 100%; /* 占满宽度 */
}

.upload-icon {
  font-size: 67px; /* 图标尺寸67px */
  color: #409eff; /* 蓝色 */
  margin-bottom: 16px; /* 底部外边距16px */
}

.upload-text {
  display: flex; /* 弹性布局 */
  flex-direction: column; /* 垂直排列 */
  align-items: center; /* 水平居中 */
}

.main-text {
  font-size: 14px; /* 字号14px */
  color: #606266; /* 中灰色 */
}

.main-text em {
  color: #409eff; /* 蓝色强调 */
  font-style: normal; /* 正常字体样式 */
}

.sub-text {
  font-size: 12px; /* 字号12px */
  color: #909399; /* 灰色 */
  margin-top: 8px; /* 顶部外边距8px */
}

/* ==================== 导入说明样式 ==================== */
.import-tips {
  margin-top: 20px; /* 顶部外边距20px */
}

.tips-list {
  margin: 8px 0 0 0; /* 上方外边距8px */
  padding-left: 20px; /* 左侧内边距20px */
  font-size: 13px; /* 字号13px */
}

.tips-list li {
  margin-bottom: 4px; /* 底部外边距4px */
  color: #606266; /* 中灰色 */
}

/* ==================== 模板下载样式 ==================== */
.template-section {
  margin-top: 16px; /* 顶部外边距16px */
  text-align: center; /* 居中对齐 */
}

/* ==================== 上传进度样式 ==================== */
.upload-progress {
  margin-top: 20px; /* 顶部外边距20px */
}

.progress-text {
  display: block; /* 块级显示 */
  text-align: center; /* 居中对齐 */
  margin-top: 8px; /* 顶部外边距8px */
  font-size: 14px; /* 字号14px */
  color: #606266; /* 中灰色 */
}

/* ==================== 导入结果样式 ==================== */
.import-result {
  margin-top: 20px; /* 顶部外边距20px */
}

.error-preview {
  margin-top: 16px; /* 顶部外边距16px */
}

.error-preview h4 {
  font-size: 14px; /* 字号14px */
  color: #f56c6c; /* 红色 */
  margin-bottom: 8px; /* 底部外边距8px */
}
</style>
