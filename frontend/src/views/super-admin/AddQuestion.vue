<template>
  <div class="question-manage-page">
    <div class="page-header">
      <div class="header-left">
        <h1>题库管理</h1>
        <p>管理题库中的题目</p>
      </div>
      <div class="header-right">
        <el-button @click="handleAdd" type="primary">
          <el-icon :size="18"><Plus /></el-icon>
          新增题目
        </el-button>
        <el-button @click="handleBack" class="back-button">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
    </div>

    <div class="filter-section">
      <el-card class="filter-card">
        <div class="filter-row">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入题干关键词搜索"
            class="search-input"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch"><el-icon><Search /></el-icon></el-button>
            </template>
          </el-input>
          <el-select v-model="searchType" placeholder="题目类型" clearable>
            <el-option label="全部" value="" />
            <el-option label="单选题" value="single" />
            <el-option label="多选题" value="multi" />
            <el-option label="判断题" value="judge" />
            <el-option label="简答题" value="essay" />
          </el-select>
          <el-button @click="handleSearch" type="primary">查询</el-button>
          <el-button @click="handleResetFilter">重置</el-button>
        </div>
      </el-card>
    </div>

    <div class="list-section">
      <el-card class="list-card" v-loading="listLoading">
        <el-table :data="questionList" style="width: 100%">
          <el-table-column prop="template_id" label="题目ID" width="100" />
          <el-table-column prop="title" label="题干" min-width="300">
            <template #default="{ row }">
              <span class="title-text">{{ row.title }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="题型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)">
                {{ getTypeText(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="param_field" label="参数字段" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-switch
                :value="row.status === 1"
                @change="(val) => handleStatusChange(row.template_id, val ? 1 : 0)"
                :disabled="listLoading"
              />
            </template>
          </el-table-column>
          <el-table-column prop="analysis" label="解析" min-width="200">
            <template #default="{ row }">
              <span class="analysis-text">{{ row.analysis || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" :type="row.status === 1 ? 'danger' : 'success'" @click="handleStatusChange(row.template_id, row.status === 1 ? 0 : 1)">
                {{ row.status === 1 ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>

    <el-dialog v-model="showModal" :title="isEdit ? '编辑题目' : '新增题目'" width="600px">
      <el-form :model="questionForm" :rules="questionRules" ref="questionFormRef" label-width="100px">
        <el-form-item label="题目类型" prop="type">
          <el-radio-group v-model="questionForm.type">
            <el-radio label="single">单选题</el-radio>
            <el-radio label="multi">多选题</el-radio>
            <el-radio label="judge">判断题</el-radio>
            <el-radio label="essay">简答题</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="题干模板" prop="title">
          <el-input
            v-model="questionForm.title"
            type="textarea"
            :rows="3"
            placeholder="请输入题干模板，使用 {name} 占位学生姓名"
          />
          <div class="tip-text">提示：{name} 会在考试/练习时自动替换为学生姓名</div>
        </el-form-item>

        <el-form-item label="参数字段" prop="param_field">
          <el-select v-model="questionForm.param_field" placeholder="请选择参数字段">
            <el-option label="请选择" value="" />
            <el-option label="学院 (college)" value="college" />
            <el-option label="班级 (class_name)" value="class_name" />
            <el-option label="民族 (ethnicity)" value="ethnicity" />
            <el-option label="性别 (gender)" value="gender" />
            <el-option label="年级 (grade)" value="grade" />
            <el-option label="籍贯 (native_place)" value="native_place" />
            <el-option label="宿舍地址 (dorm_address)" value="dorm_address" />
            <el-option label="家庭所在地 (family_address)" value="family_address" />
            <el-option label="生源地 (origin_place)" value="origin_place" />
            <el-option label="户籍所在地 (household_address)" value="household_address" />
            <el-option label="是否经济困难 (is_financial_difficulty)" value="is_financial_difficulty" />
            <el-option label="是否学业困难 (is_academic_difficulty)" value="is_academic_difficulty" />
            <el-option label="室友 (roommates)" value="roommates" />
            <el-option label="同班同学 (classmates)" value="classmates" />
          </el-select>
          <div class="tip-text">
            <span v-if="questionForm.type === 'single'">单选题：选择一个字段；室友 roommates 会生成分组选项</span>
            <span v-else-if="questionForm.type === 'multi'">多选题：支持字段名、field:value 条目或 classmates</span>
            <span v-else-if="questionForm.type === 'judge'">判断题：只能选择布尔类型字段（is_financial_difficulty 或 is_academic_difficulty）</span>
            <span v-else>简答题：可以留空</span>
          </div>
        </el-form-item>

        <el-form-item label="解析说明" prop="analysis">
          <el-input
            v-model="questionForm.analysis"
            type="textarea"
            :rows="3"
            placeholder="请输入题目解析说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showModal = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowLeft, Plus, Search } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { getQuestionList, addQuestion, editQuestion, deleteQuestion, setQuestionStatus } from '@/api/system';

const router = useRouter();
const questionFormRef = ref(null);
const showModal = ref(false);
const isEdit = ref(false);
const listLoading = ref(false);

const questionList = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const totalCount = ref(0);

const searchKeyword = ref('');
const searchType = ref('');

const questionForm = reactive({
  template_id: null,
  title: '',
  type: 'single',
  param_field: '',
  analysis: ''
});

const questionRules = {
  title: [
    { required: true, message: '请输入题干模板', trigger: 'blur' }
  ],
  param_field: [
    { required: true, message: '请选择参数字段', trigger: 'blur' }
  ]
};

onMounted(() => {
  loadQuestionList();
});

watch(
  () => questionForm.param_field,
  (field) => {
    if (field === 'roommates') {
      questionForm.type = 'single';
    }
  }
);

watch(
  () => questionForm.type,
  (type) => {
    if (questionForm.param_field === 'roommates' && type !== 'single') {
      questionForm.type = 'single';
    }
  }
);

async function loadQuestionList() {
  listLoading.value = true;
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value
    };
    
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value;
    }
    if (searchType.value) {
      params.type = searchType.value;
    }
    
    const res = await getQuestionList(params);
    console.log('题库列表响应:', res);
    
    if (res && res.list) {
      questionList.value = res.list;
      totalCount.value = res.total || 0;
    }
  } catch (error) {
    console.error('加载题库列表失败', error);
    ElMessage.error('加载题库列表失败：' + (error.message || '请检查后端服务'));
  } finally {
    listLoading.value = false;
  }
}

function handleBack() {
  router.push('/super-admin/home');
}

function handleSearch() {
  currentPage.value = 1;
  loadQuestionList();
}

function handleResetFilter() {
  searchKeyword.value = '';
  searchType.value = '';
  currentPage.value = 1;
  loadQuestionList();
}

function handleAdd() {
  isEdit.value = false;
  resetForm();
  showModal.value = true;
}

function handleEdit(row) {
  isEdit.value = true;
  questionForm.template_id = row.template_id;
  questionForm.title = row.title;
  questionForm.type = row.type;
  questionForm.param_field = row.param_field;
  questionForm.analysis = row.analysis || '';
  showModal.value = true;
}

function resetForm() {
  questionForm.template_id = null;
  questionForm.title = '';
  questionForm.type = 'single';
  questionForm.param_field = '';
  questionForm.analysis = '';
}

async function handleSave() {
  if (!questionFormRef.value) return;
  
  questionFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const data = {
          title: questionForm.title,
          type: questionForm.type,
          param_field: questionForm.param_field,
          analysis: questionForm.analysis
        };

        let response;
        if (isEdit.value) {
          response = await editQuestion(questionForm.template_id, data);
          ElMessage.success('题目编辑成功');
        } else {
          response = await addQuestion(data);
          ElMessage.success('题目添加成功');
        }

        if (response) {
          showModal.value = false;
          loadQuestionList();
        }
      } catch (error) {
        console.error('保存题目失败', error);
        ElMessage.error('保存失败：' + (error.response?.data?.msg || error.message));
      }
    }
  });
}

async function handleDelete(templateId) {
  try {
    await deleteQuestion(templateId);
    ElMessage.success('操作成功');
    loadQuestionList();
  } catch (error) {
    console.error('删除题目失败', error);
    ElMessage.error('操作失败：' + (error.response?.data?.msg || error.message));
  }
}

async function handleStatusChange(templateId, status) {
  try {
    await setQuestionStatus(templateId, { status });
    ElMessage.success(status === 1 ? '题目已启用' : '题目已禁用');
    loadQuestionList();
  } catch (error) {
    console.error('状态修改失败', error);
    ElMessage.error('操作失败：' + (error.response?.data?.msg || error.message));
    loadQuestionList();
  }
}

function handleSizeChange() {
  currentPage.value = 1;
  loadQuestionList();
}

function handlePageChange() {
  loadQuestionList();
}

function getTypeText(type) {
  const texts = {
    single: '单选题',
    multi: '多选题',
    judge: '判断题',
    essay: '简答题'
  };
  return texts[type] || type;
}

function getTypeTagType(type) {
  const types = {
    single: 'primary',
    multi: 'success',
    judge: 'warning',
    essay: 'info'
  };
  return types[type] || 'default';
}
</script>

<style scoped>
.question-manage-page {
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

.header-left {
  flex: 1;
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

.header-right {
  margin-left: 20px;
  display: flex;
  gap: 10px;
}

.back-button {
  padding: 8px 16px;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.list-section {
  margin-bottom: 20px;
}

.list-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.title-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analysis-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #999;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.tip-text {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}
</style>
