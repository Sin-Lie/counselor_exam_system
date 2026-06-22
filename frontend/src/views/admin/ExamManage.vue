/**
 * 考试管理页面组件（管理员端）
 */
<template>
  <div class="exam-manage-container">
    <div class="page-header">
      <h2 class="page-title">考试管理</h2>
      <el-button type="primary" @click="handleCreate">创建考试</el-button>
    </div>

    <el-card shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="选择状态" clearable @change="handleSearch" style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="未发布" value="draft" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="已结束" value="ended" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table :data="exams" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="考试名称" min-width="200" />
        <el-table-column prop="duration" label="时长" width="100" />
        <el-table-column prop="totalScore" label="总分" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="startTime" label="开始时间" width="180" />
        <el-table-column prop="endTime" label="结束时间" width="180" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="success" @click="handlePublish(row)">发布</el-button>
            <el-button v-if="row.status === 'ongoing'" size="small" type="warning" @click="handleClose(row)">关闭</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getExamManageList, publishExam, closeExam, deleteExam } from '@/api/system';

const loading = ref(false);
const exams = ref([]);

const filterForm = reactive({ status: '' });

const pagination = reactive({ page: 1, pageSize: 10, total: 0 });

onMounted(() => { loadExams(); });

async function loadExams() {
  loading.value = true;
  try {
    const params = { page: pagination.page, pageSize: pagination.pageSize, ...filterForm };
    const res = await getExamManageList(params);
    exams.value = res.data || res.list || [];
    pagination.total = res.total || 0;
  } catch (error) { console.error('加载考试列表失败', error); }
  finally { loading.value = false; }
}

function handleSearch() { pagination.page = 1; loadExams(); }

async function handlePublish(row) {
  try {
    await publishExam(row.id);
    ElMessage.success('发布成功');
    loadExams();
  } catch (error) { console.error('发布失败', error); }
}

async function handleClose(row) {
  try {
    await closeExam(row.id);
    ElMessage.success('已关闭');
    loadExams();
  } catch (error) { console.error('关闭失败', error); }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除该考试吗？', '警告', { type: 'warning' });
    await deleteExam(row.id);
    ElMessage.success('删除成功');
    loadExams();
  } catch (error) { if (error !== 'cancel') console.error('删除失败', error); }
}

function handleCreate() { ElMessage.info('创建考试功能开发中'); }
function handleEdit(row) { ElMessage.info('编辑考试功能开发中'); }
function handleSizeChange() { pagination.page = 1; loadExams(); }
function handlePageChange() { loadExams(); }

function getStatusTagType(status) {
  return { draft: 'info', ongoing: 'success', ended: 'warning' }[status] || 'info';
}

function getStatusText(status) {
  return { draft: '未发布', ongoing: '进行中', ended: '已结束' }[status] || status;
}
</script>

<style scoped>
.exam-manage-container { padding: 20px; background-color: #fff; border-radius: 8px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; margin: 0; }
.pagination { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
