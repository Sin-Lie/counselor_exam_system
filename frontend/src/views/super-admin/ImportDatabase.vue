<template>
  <div class="import-database-page">
    <div class="page-header">
      <div class="header-left">
        <h1>数据导入</h1>
        <p>导入辅导员或学生信息到系统</p>
      </div>
      <div class="header-right">
        <el-button @click="handleBack" class="back-button">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
    </div>

    <div class="content-section">
      <el-card class="upload-card">
        <template #header>
          <div class="card-header">
            <span>导入数据</span>
          </div>
        </template>

        <!-- 导入类型选择 -->
        <div class="import-tabs">
          <el-radio-group v-model="importType">
            <el-radio label="users">导入辅导员</el-radio>
            <el-radio label="students">导入学生信息</el-radio>
          </el-radio-group>
        </div>

        <!-- 导入说明 -->
        <div class="import-tips">
          <el-alert
            :title="importType === 'users' ? '辅导员导入说明' : '学生信息导入说明'"
            :description="importType === 'users' ? counselorTips : studentTips"
            type="info"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 文件上传 -->
        <div class="file-upload">
          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx"
            :on-change="handleFileChange"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">
              <span>将文件拖到此处，或<em>点击上传</em></span>
              <span class="upload-tip">仅支持 .xlsx 格式</span>
            </div>
          </el-upload>

          <div v-if="selectedFile" class="file-info">
            <el-icon><Document /></el-icon>
            <span>{{ selectedFile.name }}</span>
            <el-button type="danger" text @click="handleRemoveFile">移除</el-button>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" @click="handlePreview" :disabled="!selectedFile">预览数据</el-button>
          <el-button type="success" @click="handleImport" :disabled="!selectedFile" :loading="importing">开始导入</el-button>
        </div>
      </el-card>

      <!-- 导入结果 -->
      <el-card v-if="importResult" class="result-card">
        <template #header>
          <div class="card-header">
            <span>导入结果</span>
          </div>
        </template>
        <div class="result-summary">
          <div class="result-item success">
            <el-icon><Check /></el-icon>
            <span>成功导入 <strong>{{ importResult.success_num }}</strong> 条</span>
          </div>
          <div class="result-item fail">
            <el-icon><Close /></el-icon>
            <span>导入失败 <strong>{{ importResult.fail_num }}</strong> 条</span>
          </div>
        </div>
        <div v-if="importResult.fail_reason && importResult.fail_reason.length > 0" class="fail-reasons">
          <h4>失败详情：</h4>
          <el-table :data="importResult.fail_reason" border size="small">
            <el-table-column prop="row" label="行号" width="80" />
            <el-table-column prop="msg" label="失败原因" />
          </el-table>
        </div>
      </el-card>

      <!-- 导入历史 -->
      <el-card v-if="importHistory.length > 0" class="history-card">
        <template #header>
          <div class="card-header">
            <span>导入历史</span>
          </div>
        </template>
        <el-table :data="importHistory" border>
          <el-table-column prop="time" label="导入时间" />
          <el-table-column prop="type" label="导入类型">
            <template #default="scope">
              <span>{{ scope.row.type === 'users' ? '辅导员' : '学生信息' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="success_num" label="成功条数" />
          <el-table-column prop="fail_num" label="失败条数" />
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-tag :type="scope.row.status === '成功' ? 'success' : 'danger'">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 预览弹窗 -->
    <el-dialog v-model="showPreview" title="数据预览" width="800px">
      <el-table :data="previewData" border max-height="400">
        <el-table-column v-for="col in previewColumns" :key="col" :prop="col" :label="col" />
      </el-table>
      <template #footer>
        <el-button @click="showPreview = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, UploadFilled, Document, Check, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { importCounselors, importStudents } from '@/api/system'

const router = useRouter()
const importType = ref('users')
const selectedFile = ref(null)
const uploadRef = ref(null)
const showPreview = ref(false)
const previewData = ref([])
const previewColumns = ref([])
const importing = ref(false)
const importResult = ref(null)

// 辅导员导入说明
const counselorTips = 'Excel文件需包含以下5列（顺序固定）：\n' +
  '1. username - 工号（必填，不可重复）\n' +
  '2. name - 姓名（必填）\n' +
  '3. password - 密码（必填，明文存储）\n' +
  '4. role - 角色（选填，1=辅导员(默认)，2=批改员，3=超级管理员）\n' +
  '5. phone - 联系电话（选填）'

// 学生信息导入说明
const studentTips = 'Excel文件通过表头名称匹配列位置，不依赖固定列顺序。\n' +
  '【必填列】\n' +
  '• 学号 / 学生编号 / student_id / id（学生学号，已存在时更新，不存在时新增）\n' +
  '• 姓名 / 学生姓名 / name（学生姓名）\n' +
  '• 辅导员姓名 / 辅导员 / advisor_name（无工号时需填写）\n' +
  '\n【选填列】\n' +
  '• 辅导员工号 / 工号 / advisor_username（有则直接精确匹配，不存在重名问题）\n' +
  '• 辅导员电话 / 辅导员手机 / advisor_phone（无工号时可作为辅助匹配条件）\n' +
  '• 性别 / gender\n' +
  '• 年级 / grade\n' +
  '• 学院 / 院系 / college\n' +
  '• 班级 / 班 / class_name / class\n' +
  '• 专业 / major\n' +
  '• 民族 / ethnicity / ethnic\n' +
  '• 籍贯 / native_place\n' +
  '• 生源地 / origin_place\n' +
  '• 家庭所在地 / 家庭住址 / family_address\n' +
  '• 户籍所在地 / 户籍地址 / household_address\n' +
  '• 住宿地址 / 宿舍地址 / 宿舍 / dorm_address\n' +
  '• 校外住宿地址 / 校外地址 / off_campus_address\n' +
  '• 是否经济困难 / 经济困难 / is_financial_difficulty（填"是"/"1"表示是）\n' +
  '• 是否学业困难 / 学业困难 / is_academic_difficulty（填"是"/"1"表示是）\n' +
  '• 宗教信仰 / religion\n' +
  '• 学籍状态 / enrollment_status\n' +
  '• 照片 / 照片路径 / photo_url / photo（留空默认使用学号）\n' +
  '\n【辅导员匹配逻辑】\n' +
  '1. 有辅导员工号 → 直接用工号精确匹配\n' +
  '2. 有辅导员电话 → 用姓名+电话组合匹配（解决重名）\n' +
  '3. 仅姓名 → 按姓名模糊匹配'

// 导入历史（模拟数据）
const importHistory = ref([
  { time: '2026-04-29 10:30', type: 'users', success_num: 48, fail_num: 2, status: '成功' },
  { time: '2026-04-28 14:20', type: 'students', success_num: 196, fail_num: 4, status: '成功' },
  { time: '2026-04-25 09:15', type: 'users', success_num: 10, fail_num: 0, status: '成功' }
])

function handleBack() {
  router.push('/super-admin/home')
}

function handleFileChange(file) {
  selectedFile.value = file.raw
  importResult.value = null // 清除上次导入结果
}

function handleRemoveFile() {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
  importResult.value = null
}

function handlePreview() {
  // 简单预览，实际项目中可以解析Excel展示
  if (importType.value === 'users') {
    previewColumns.value = ['工号', '姓名', '密码', '角色', '联系电话']
    previewData.value = [
      { '工号': 'T202401', '姓名': '张三', '密码': '******', '角色': '辅导员', '联系电话': '13800000001' },
      { '工号': 'T202402', '姓名': '李四', '密码': '******', '角色': '辅导员', '联系电话': '13800000002' },
      { '工号': 'admin01', '姓名': '管理员', '密码': '******', '角色': '批改员', '联系电话': '13800000003' }
    ]
  } else {
    previewColumns.value = ['学号', '姓名', '辅导员姓名', '辅导员工号', '辅导员电话', '性别', '年级', '学院', '班级', '专业']
    previewData.value = [
      { '学号': '2021001', '姓名': '王五', '辅导员姓名': '张三', '辅导员工号': 'T202401', '辅导员电话': '13800000001', '性别': '男', '年级': '2021级', '学院': '计算机学院', '班级': '计科2101', '专业': '计算机科学' },
      { '学号': '2021002', '姓名': '赵六', '辅导员姓名': '李四', '辅导员工号': 'T202402', '辅导员电话': '13800000002', '性别': '女', '年级': '2021级', '学院': '信息学院', '班级': '信管2101', '专业': '信息管理' },
      { '学号': '2021003', '姓名': '钱七', '辅导员姓名': '张三', '辅导员工号': '', '辅导员电话': '', '性别': '男', '年级': '2021级', '学院': '计算机学院', '班级': '计科2102', '专业': '软件工程' }
    ]
  }
  showPreview.value = true
}

async function handleImport() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }

  importing.value = true

  try {
    // 创建FormData
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    // 调用对应接口
    let response
    if (importType.value === 'users') {
      response = await importCounselors(formData)
    } else {
      response = await importStudents(formData)
    }

    // 处理响应
    if (response.code === 200) {
      // response 已经被拦截器扁平化了，直接使用
      importResult.value = response
      ElMessage.success(`${response.msg}，成功导入 ${response.success_num} 条数据`)
      
      // 添加到历史记录
      importHistory.value.unshift({
        time: new Date().toLocaleString('zh-CN'),
        type: importType.value,
        success_num: response.success_num,
        fail_num: response.fail_num,
        status: response.fail_num === 0 ? '成功' : '部分成功'
      })

      // 清空选择
      selectedFile.value = null
      uploadRef.value?.clearFiles()
    } else {
      ElMessage.error(response.msg || '导入失败')
    }
  } catch (error) {
    console.error('导入失败', error)
    ElMessage.error('导入失败，请稍后重试')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.import-database-page {
  padding: 20px;
  min-height: 100%;
  background: #f5f7fa;
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.header-left p {
  font-size: 14px;
  color: #999;
  margin: 8px 0 0;
}

.back-button {
  padding: 8px 16px;
}

.content-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  font-weight: 600;
}

.import-tabs {
  margin-bottom: 20px;
}

.import-tips {
  margin-bottom: 20px;
}

.upload-area {
  width: 100%;
  margin-bottom: 20px;
}

.upload-area :deep(.el-upload-dragger) {
  padding: 40px 20px;
  width: 100%;
}

.upload-icon {
  font-size: 67px;
  color: #409eff;
  margin-bottom: 16px;
}

.upload-text {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.file-info span {
  flex: 1;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.result-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.result-summary {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.result-item.success {
  color: #67c23a;
}

.result-item.fail {
  color: #f56c6c;
}

.fail-reasons h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
}

.history-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
</style>