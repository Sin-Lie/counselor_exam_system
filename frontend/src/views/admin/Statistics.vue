/**
 * 考试统计页面组件（管理员端）
 * 对接后端 GET /api/score/statistics/{exam_id}/
 * 注意：该接口需要超级管理员(role=3)权限，普通管理员(role=2)无法访问
 */
<template>
  <div class="statistics-container">
    <div class="page-header">
      <h2 class="page-title">考试统计</h2>
      <ExcelExport export-url="/api/score/statistics/export" file-name="成绩统计" button-text="导出Excel" />
    </div>

    <el-card shadow="never">
      <el-form :inline="true" :model="form">
        <el-form-item label="选择考试">
          <el-select v-model="form.examId" placeholder="请选择考试" @change="loadStatistics">
            <el-option v-for="exam in examList" :key="exam.exam_id" :label="exam.exam_name" :value="exam.exam_id" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计数据展示 -->
    <el-row :gutter="20" class="stats-row" v-if="stats">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.total_students ?? stats.totalStudents ?? '-' }}</div>
          <div class="stat-label">参考人数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.avg_score ?? stats.avgScore ?? '-' }}</div>
          <div class="stat-label">平均分</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.pass_rate != null ? stats.pass_rate + '%' : (stats.passRate != null ? stats.passRate + '%' : '-') }}</div>
          <div class="stat-label">及格率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ stats.unattended_count ?? stats.absentCount ?? '-' }}</div>
          <div class="stat-label">缺考人数</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 权限不足提示 -->
    <el-empty v-if="permissionDenied" description="您没有权限查看考试统计，仅超级管理员可访问" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import ExcelExport from '@/components/ExcelExport.vue';
import { getExamManageList, getExamStatistics } from '@/api/system';

const loading = ref(false);
const form = reactive({ examId: '' });
const examList = ref([]);
const stats = ref(null);
const permissionDenied = ref(false);

onMounted(async () => {
  await loadExamList();
});

async function loadExamList() {
  try {
    const res = await getExamManageList({ page: 1, size: 50 });
    examList.value = res.list || [];
  } catch (error) {
    console.error('加载考试列表失败', error);
  }
}

async function loadStatistics() {
  if (!form.examId) return;
  loading.value = true;
  permissionDenied.value = false;
  stats.value = null;
  try {
    const res = await getExamStatistics(form.examId);
    stats.value = res;
  } catch (error) {
    console.error('加载统计数据失败', error);
    // 如果是权限错误，显示友好提示（后端统一返回HTTP 200，权限错误由响应拦截器转为Error）
    const msg = error?.message || '';
    if (msg.includes('权限') || msg.includes('Permission')) {
      permissionDenied.value = true;
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.statistics-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.stats-row {
  margin-top: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}
</style>
