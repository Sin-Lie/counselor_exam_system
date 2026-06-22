<template>
  <div class="import-score-page">
    <!-- 表单容器 -->
    <div class="form-container">
      <!-- 表单标题 -->
      <div class="form-header">
        <h2>{{ isEditMode ? '修改成绩' : '录入成绩' }}</h2>
      </div>

      <!-- 表单内容 -->
      <el-form
        ref="importFormRef"
        :model="importForm"
        :rules="formRules"
        class="import-form"
        label-width="120px"
      >
        <!-- 答题ID -->
        <el-form-item label="答题ID" prop="answerId">
          <el-input v-model="importForm.answerId" disabled />
        </el-form-item>

        <!-- 考生姓名 -->
        <el-form-item label="考生姓名" prop="name">
          <el-input v-model="importForm.name" disabled />
        </el-form-item>

        <!-- 分数 -->
        <el-form-item label="分数" prop="score">
          <el-input-number
            v-model="importForm.score"
            :min="0"
            :max="100"
            :step="1"
            class="score-input"
          />
          <span class="score-unit">分</span>
        </el-form-item>

        <!-- 批注 -->
        <el-form-item label="批注" prop="remark">
          <el-input
            v-model="importForm.remark"
            type="textarea"
            :rows="3"
            placeholder="可选，输入批改评语"
          />
        </el-form-item>

        <!-- 底部按钮区域 -->
        <div class="bottom-buttons">
          <el-button type="default" @click="handleBack">返回</el-button>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            {{ loading ? '提交中...' : '确定' }}
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
/**
 * 录入/修改成绩页面
 * 对接后端 PUT /api/correct/score/{answer_id}/
 */
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { submitScore } from '@/api/correct';

const router = useRouter();
const route = useRoute();

// ==================== 状态定义 ====================
const loading = ref(false);
const importFormRef = ref(null);
const isEditMode = ref(false);

// 表单数据
const importForm = reactive({
  answerId: '',
  name: '',
  score: 0,
  remark: '',
});

// 表单验证规则
const formRules = {
  score: [
    { required: true, message: '请输入分数', trigger: 'blur' },
    { type: 'number', min: 0, max: 100, message: '分数必须在0-100之间', trigger: 'blur' },
  ],
};

// ==================== 方法定义 ====================
function handleBack() {
  router.back();
}

async function handleSubmit() {
  try {
    await importFormRef.value.validate();
  } catch (error) {
    return;
  }

  if (!importForm.answerId) {
    ElMessage.error('缺少答题ID');
    return;
  }

  loading.value = true;
  try {
    await submitScore(importForm.answerId, {
      score: importForm.score,
      remark: importForm.remark,
    });

    ElMessage.success(isEditMode.value ? '成绩修改成功' : '成绩录入成功');
    setTimeout(() => router.back(), 500);
  } catch (error) {
    console.error('提交失败', error);
    ElMessage.error('提交失败，请重试');
  } finally {
    loading.value = false;
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  importForm.answerId = route.query.answerId || '';
  importForm.name = route.query.name || '';
  importForm.score = parseInt(route.query.score) || 0;
  importForm.remark = route.query.remark || '';
  isEditMode.value = !!route.query.answerId;
});
</script>

<style scoped>
.import-score-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #e6f7ff;
  padding: 20px;
}

.form-container {
  width: 450px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.form-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.form-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.import-form {
  width: 100%;
}

.score-input {
  width: 150px;
}

.score-unit {
  margin-left: 8px;
  color: #666;
  font-size: 14px;
}

.bottom-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
}
</style>