/**
 * 用户管理页面组件（管理员端）
 */
<template>
  <div class="user-manage-container">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleImport">导入辅导员</el-button>
        <el-button type="success" @click="handleCreateAdmin">创建管理员</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="角色">
          <el-select v-model="filterForm.role" placeholder="选择角色" clearable @change="handleSearch" style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="辅导员" :value="1" />
            <el-option label="管理员" :value="2" />
            <el-option label="超级管理员" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filterForm.keyword" placeholder="搜索姓名/工号" clearable @change="handleSearch" />
        </el-form-item>
      </el-form>

      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="jobNumber" label="工号" width="120" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">{{ getRoleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'">{{ row.enabled ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleToggleStatus(row)">{{ row.enabled ? '禁用' : '启用' }}</el-button>
            <el-button size="small" @click="handleResetPassword(row)">重置密码</el-button>
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
import { getUserList, setUserStatus, resetUserPassword, importCounselors, createAdmin } from '@/api/system';

const loading = ref(false);
const users = ref([]);

const filterForm = reactive({ role: '', keyword: '' });

const pagination = reactive({ page: 1, pageSize: 10, total: 0 });

onMounted(() => { loadUsers(); });

async function loadUsers() {
  loading.value = true;
  try {
    const params = { page: pagination.page, pageSize: pagination.pageSize, ...filterForm };
    const res = await getUserList(params);
    users.value = res.data || res.list || [];
    pagination.total = res.total || 0;
  } catch (error) { console.error('加载用户列表失败', error); }
  finally { loading.value = false; }
}

function handleSearch() { pagination.page = 1; loadUsers(); }

async function handleToggleStatus(row) {
  try {
    await setUserStatus(row.id, !row.enabled);
    ElMessage.success(row.enabled ? '已禁用' : '已启用');
    loadUsers();
  } catch (error) { console.error('操作失败', error); }
}

async function handleResetPassword(row) {
  try {
    await ElMessageBox.confirm(`确定要重置 ${row.name} 的密码吗？`, '提示', { type: 'warning' });
    const res = await resetUserPassword(row.id);
    ElMessage.success(`新密码：${res.newPassword}`);
  } catch (error) { if (error !== 'cancel') console.error('重置密码失败', error); }
}

function handleImport() { ElMessage.info('导入功能开发中'); }
function handleCreateAdmin() { ElMessage.info('创建管理员功能开发中'); }

function handleSizeChange() { pagination.page = 1; loadUsers(); }
function handlePageChange() { loadUsers(); }

function getRoleTagType(role) {
  return { 1: 'info', 2: 'warning', 3: 'danger' }[role] || 'info';
}

function getRoleText(role) {
  return { 1: '辅导员', 2: '管理员', 3: '超级管理员' }[role] || role;
}
</script>

<style scoped>
.user-manage-container { padding: 20px; background-color: #fff; border-radius: 8px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; margin: 0; }
.header-actions { display: flex; gap: 10px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
