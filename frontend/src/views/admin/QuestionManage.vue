/**
 * 题库管理页面组件（管理员端）
 */
<template>
  <div class="question-manage-container">
    <div class="page-header">
      <h2 class="page-title">题库管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleImport">导入题目</el-button>
        <el-button type="success" @click="handleAdd">添加题目</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="题型">
          <el-select v-model="filterForm.type" placeholder="选择题型" clearable @change="handleSearch" style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="单选" value="single" />
            <el-option label="多选" value="multiple" />
            <el-option label="判断" value="judge" />
            <el-option label="简答" value="short" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filterForm.keyword" placeholder="搜索题目内容" clearable @change="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="questions" v-loading="loading" style="width: 100%">
        <el-table-column prop="type" label="题型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)" size="small">{{ getTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="题目内容" min-width="300">
          <template #default="{ row }">
            <span class="question-content">{{ row.content }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="分值" width="80" />
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
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
import { getQuestionList, deleteQuestion } from '@/api/system';

const loading = ref(false);
const questions = ref([]);

const filterForm = reactive({ type: '', keyword: '' });

const pagination = reactive({ page: 1, pageSize: 10, total: 0 });

onMounted(() => { loadQuestions(); });

async function loadQuestions() {
  loading.value = true;
  try {
    const params = { page: pagination.page, pageSize: pagination.pageSize, ...filterForm };
    const res = await getQuestionList(params);
    questions.value = res.data || res.list || [];
    pagination.total = res.total || 0;
  } catch (error) { console.error('加载题目列表失败', error); }
  finally { loading.value = false; }
}

function handleSearch() { pagination.page = 1; loadQuestions(); }

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除该题目吗？', '警告', { type: 'warning' });
    await deleteQuestion(row.id);
    ElMessage.success('删除成功');
    loadQuestions();
  } catch (error) { if (error !== 'cancel') console.error('删除失败', error); }
}

function handleAdd() { ElMessage.info('添加题目功能开发中'); }
function handleEdit(row) { ElMessage.info('编辑题目功能开发中'); }
function handleImport() { ElMessage.info('导入题目功能开发中'); }
function handleSizeChange() { pagination.page = 1; loadQuestions(); }
function handlePageChange() { loadQuestions(); }

function getTypeTagType(type) {
  return { single: 'primary', multiple: 'success', judge: 'warning', short: 'info' }[type] || 'info';
}

function getTypeText(type) {
  return { single: '单选', multiple: '多选', judge: '判断', short: '简答' }[type] || type;
}
</script>

<style scoped>
.question-manage-container { padding: 20px; background-color: #fff; border-radius: 8px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; margin: 0; }
.header-actions { display: flex; gap: 10px; }
.question-content { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pagination { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
