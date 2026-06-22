/**
 * 日志管理页面组件（管理员端）
 */
<template>
  <div class="log-manage-container">
    <div class="page-header">
      <h2 class="page-title">日志管理</h2>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="登录日志" name="login">
        <el-table :data="loginLogs" v-loading="loading" style="width: 100%">
          <el-table-column prop="username" label="用户名" width="150" />
          <el-table-column prop="role" label="角色" width="120" />
          <el-table-column prop="ip" label="IP地址" width="150" />
          <el-table-column prop="userAgent" label="浏览器" min-width="200" />
          <el-table-column prop="loginTime" label="登录时间" width="180" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="异常日志" name="exception">
        <el-table :data="exceptionLogs" v-loading="loading" style="width: 100%">
          <el-table-column prop="examTitle" label="考试名称" width="150" />
          <el-table-column prop="studentName" label="学生姓名" width="120" />
          <el-table-column prop="exceptionType" label="异常类型" width="120" />
          <el-table-column prop="detail" label="异常详情" min-width="200" />
          <el-table-column prop="createTime" label="发生时间" width="180" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="切屏记录" name="focus">
        <el-table :data="focusLogs" v-loading="loading" style="width: 100%">
          <el-table-column prop="examTitle" label="考试名称" width="150" />
          <el-table-column prop="studentName" label="学生姓名" width="120" />
          <el-table-column prop="leaveCount" label="切屏次数" width="100" />
          <el-table-column prop="firstLeaveTime" label="首次切屏时间" width="180" />
          <el-table-column prop="lastLeaveTime" label="最后切屏时间" width="180" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="批改日志" name="correct">
        <el-table :data="correctLogs" v-loading="loading" style="width: 100%">
          <el-table-column prop="adminName" label="管理员" width="120" />
          <el-table-column prop="studentName" label="学生姓名" width="120" />
          <el-table-column prop="score" label="评分" width="80" />
          <el-table-column prop="comment" label="评语" min-width="200" />
          <el-table-column prop="createTime" label="批改时间" width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { getLoginLogs, getExamExceptionLogs, getFocusLeaveLogs, getCorrectLogs } from '@/api/system';

const loading = ref(false);
const activeTab = ref('login');
const loginLogs = ref([]);
const exceptionLogs = ref([]);
const focusLogs = ref([]);
const correctLogs = ref([]);

const pagination = reactive({ page: 1, pageSize: 10, total: 0 });

onMounted(() => { loadLogs(); });

async function loadLogs() {
  loading.value = true;
  try {
    const params = { page: pagination.page, pageSize: pagination.pageSize };
    let res;
    switch (activeTab.value) {
      case 'login':
        res = await getLoginLogs(params);
        loginLogs.value = res.data || res.list || [];
        break;
      case 'exception':
        res = await getExamExceptionLogs(params);
        exceptionLogs.value = res.data || res.list || [];
        break;
      case 'focus':
        res = await getFocusLeaveLogs(params);
        focusLogs.value = res.data || res.list || [];
        break;
      case 'correct':
        res = await getCorrectLogs(params);
        correctLogs.value = res.data || res.list || [];
        break;
    }
    pagination.total = res.total || 0;
  } catch (error) { console.error('加载日志失败', error); }
  finally { loading.value = false; }
}

function handleTabChange() { pagination.page = 1; loadLogs(); }
function handleSizeChange() { pagination.page = 1; loadLogs(); }
function handlePageChange() { loadLogs(); }
</script>

<style scoped>
.log-manage-container { padding: 20px; background-color: #fff; border-radius: 8px; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; margin: 0; }
.pagination { display: flex; justify-content: flex-end; margin-top: 20px; }
</style>
