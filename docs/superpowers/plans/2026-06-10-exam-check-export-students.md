# 试卷检查页导出学生信息 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an "导出学生信息" button on `/super-admin/exam-check` that exports all students referenced across all counselors' papers for a selected exam, and add the corresponding backend API.

**Architecture:** Backend exposes a new Excel-download endpoint that queries `ExamQuestion` → `student_id` → `Student` (all 23 fields) across all `ExamPaper` records for a given exam. Frontend calls it as a blob download on button click.

**Tech Stack:** Django + DRF (backend), Vue 3 + Element Plus + Axios (frontend), openpyxl (Excel generation)

---

### Task 1: Backend — export service logic

**Files:**
- Modify: `backend/apps/exam/services.py`
- Reuse: `backend/utils/excel.py` (`create_excel_response`)

- [ ] **Step 1: Add `export_exam_students` function to services.py**

  Add the following function at the end of `backend/apps/exam/services.py`:

```python
import io
from collections import OrderedDict
from openpyxl import Workbook
from urllib.parse import quote
from django.http import HttpResponse
from apps.system.models import Student
from .models import ExamQuestion


def export_exam_students(exam_id):
    """
    导出一次考试中所有辅导员试卷抽取到的所有学生信息
    收集所有 ExamQuestion.student_id → Student 全字段 → Excel
    """
    # 查询该考试所有题目关联的学生ID（去重）
    student_ids = list(
        ExamQuestion.objects
        .filter(exam_id=exam_id, student__isnull=False)
        .values_list('student_id', flat=True)
        .distinct()
    )

    if not student_ids:
        return False, (404, "该考试未关联任何学生")

    # 查询学生完整信息
    students = Student.objects.filter(id__in=student_ids)

    # 准备 Excel 数据
    headers = [
        '学号', '姓名', '性别', '学院', '年级', '班级', '专业',
        '辅导员姓名', '辅导员电话', '辅导员工号',
        '民族', '籍贯', '生源地', '家庭所在地', '户籍所在地',
        '是否学业困难', '宗教信仰', '住宿地址', '校外住宿地址',
        '是否经济困难', '学籍状态', '照片地址',
    ]

    rows = []
    for s in students:
        rows.append([
            s.id, s.name, s.gender or '', s.college or '', s.grade or '',
            s.class_name or '', s.major or '',
            s.advisor_name or '', s.advisor_phone or '', s.advisor_username or '',
            s.ethnicity or '', s.native_place or '', s.origin_place or '',
            s.family_address or '', s.household_address or '',
            '是' if s.is_academic_difficulty else '否',
            s.religion or '', s.dorm_address or '', s.off_campus_address or '',
            '是' if s.is_financial_difficulty else '否',
            s.enrollment_status or '', s.photo_url or '',
        ])

    # 使用已有的 Excel 工具生成响应
    from utils.excel import create_excel_response
    response = create_excel_response(
        filename=f"考试{exam_id}_学生信息",
        sheet_title='学生信息',
        headers=headers,
        rows=rows,
    )
    return True, response
```

- [ ] **Step 2: Add import to the services.py top**

  Add `from apps.system.models import Student` to the existing imports. It's currently not imported. Place it alongside other model imports:

  Find the existing imports block around line 1-30 and add:
```python
from apps.system.models import Student
```

---

### Task 2: Backend — view layer

**Files:**
- Modify: `backend/apps/exam/views.py`

- [ ] **Step 1: Add `ExportStudentsView` class**

  Add the following view class at the end of `backend/apps/exam/views.py`:

```python
class ExportStudentsView(APIView):
    """
    导出考试学生信息接口
    GET /api/exam/export-students/{exam_id}/
    权限：仅超级管理员（role=3）
    导出该考试所有辅导员试卷抽取到的学生的全部信息（Excel）
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request, exam_id):
        from .services import export_exam_students

        try:
            success, result = export_exam_students(exam_id)
        except Exception as e:
            return ApiResponseServerError(msg=f"导出学生信息失败：{str(e)}")

        if not success:
            code, msg = result
            return ApiResponseError(code=code, msg=msg)

        # result 是 HttpResponse 文件流，直接返回
        return result
```

- [ ] **Step 2: Ensure `IsSuperAdmin` is imported**

  Verify `IsSuperAdmin` is already imported at the top of `views.py` (line 9 shows it is imported from `utils.permissions`).

---

### Task 3: Backend — routing

**Files:**
- Modify: `backend/apps/exam/urls.py`

- [ ] **Step 1: Add export-students route**

  Add the following line at the end of `urlpatterns` in `backend/apps/exam/urls.py`:

```python
    # 🆕 导出考试学生信息
    path('export-students/<int:exam_id>/', views.ExportStudentsView.as_view(), name='export_students'),
```

---

### Task 4: Frontend — API function

**Files:**
- Modify: `frontend/src/api/exam.js`

- [ ] **Step 1: Add `exportExamStudents` API function**

  Add the following function at the end of `frontend/src/api/exam.js`:

```javascript
/**
 * 导出考试学生信息Excel接口（超管）
 * @param {string} examId - 考试ID
 * @returns {Promise} 返回Excel文件blob
 */
export function exportExamStudents(examId) {
  return request({
    url: `/exam/export-students/${examId}/`,
    method: 'get',
    responseType: 'blob',
  })
}
```

---

### Task 5: Frontend — ExamCheck.vue export button

**Files:**
- Modify: `frontend/src/views/super-admin/ExamCheck.vue`

- [ ] **Step 1: Add import for the new API and Download icon**

  Find the existing import block (lines 206-213) and add the import for `exportExamStudents` and `Download` icon:

```javascript
// Change the import from:
import { ArrowLeft, Refresh, Document } from '@element-plus/icons-vue'
// To:
import { ArrowLeft, Refresh, Document, Download } from '@element-plus/icons-vue'

// Add inside the import block, after the existing exam API imports:
import { exportExamStudents } from '@/api/exam'
```

- [ ] **Step 2: Add export button in template**

  Find the `.exam-select-section` card where the refresh button is (around line 33-36). Add an export button right before or after the refresh button:

```html
<el-button type="success" @click="handleExportStudents" :disabled="!selectedExamId" class="export-btn">
  <el-icon :size="16"><Download /></el-icon>
  导出学生信息
</el-button>
```

  Place it before the refresh button in the `.select-header` div:

```html
<div class="select-header">
  <span class="select-label">选择考试：</span>
  <el-select
    v-model="selectedExamId"
    placeholder="请选择考试"
    class="exam-select"
    @change="handleExamChange"
  >
    <el-option
      v-for="exam in examList"
      :key="exam.exam_id"
      :label="exam.exam_name"
      :value="exam.exam_id"
    />
  </el-select>
  <el-button type="success" @click="handleExportStudents" :disabled="!selectedExamId" class="export-btn">
    <el-icon :size="16"><Download /></el-icon>
    导出学生信息
  </el-button>
  <el-button type="primary" @click="loadExamList" class="refresh-btn">
    <el-icon :size="16"><Refresh /></el-icon>
    刷新
  </el-button>
</div>
```

- [ ] **Step 3: Add `handleExportStudents` function**

  Add the following function in the `<script setup>` section, after the existing `loadExamList` function:

```javascript
async function handleExportStudents() {
  if (!selectedExamId.value) {
    ElMessage.warning('请先选择考试')
    return
  }
  try {
    const blob = await exportExamStudents(selectedExamId.value)
    // blob 下载
    const link = document.createElement('a')
    const url = window.URL.createObjectURL(blob)
    link.href = url
    const examName = selectedExam.value?.exam_name || selectedExamId.value
    link.download = `${examName}_学生信息.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出学生信息失败:', error)
    // Blob 错误处理：如果后端返回了 JSON 错误而非 Excel
    if (error.response?.data instanceof Blob) {
      const reader = new FileReader()
      reader.onload = () => {
        try {
          const errData = JSON.parse(reader.result)
          ElMessage.error(errData.msg || '导出失败')
        } catch {
          ElMessage.error('导出失败，请重试')
        }
      }
      reader.readAsText(error.response.data)
    } else {
      ElMessage.error(error.message || '导出失败，请重试')
    }
  }
}
```

- [ ] **Step 4: Add style for the export button (optional)**

  Add a small margin-right for the export button in the style section:

```css
.export-btn {
  margin-left: auto;
}
```

  Actually, since the refresh button already has `margin-left: auto`, we should change that. Let me modify the `.refresh-btn` style instead. Find it and change:

```css
/* Remove or change this: */
.refresh-btn {
  margin-left: auto;
}
/* To: */
.refresh-btn {
  margin-left: 8px;
}
```

---

### Task 6: Verify

**Files:** N/A

- [ ] **Step 1: Restart backend and verify API**

Run: (adjust command as needed for the project setup)
```bash
cd backend && python manage.py runserver
```
Or check the `启动服务.bat` for the actual start command.

Test: `GET /api/exam/export-students/{exam_id}/` with super admin token → should download an Excel file with all student fields.

- [ ] **Step 2: Verify frontend**

  Open the `/super-admin/exam-check` page in browser, select an exam, click "导出学生信息" → should download an xlsx file with student data.

- [ ] **Step 3: Edge cases**
  - Exam with no linked students → should return 404 error
  - Exam with papers but no questions yet → should return 404 error
  - Frontend error handling for non-Excel error responses

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: 添加考试学生信息导出功能

- 后端新增 GET /api/exam/export-students/{exam_id}/ 接口
- 收集一次考试所有试卷关联的学生信息导出为 Excel
- 前端 ExamCheck.vue 添加导出按钮和下载逻辑

Co-Authored-By: Claude <noreply@anthropic.com>"
```
