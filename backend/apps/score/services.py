# -*- coding: utf-8 -*-
# 成绩与统计模块 - 业务逻辑层
# 处理我的成绩、试卷详情、考试统计、未参考清单、Excel导出等核心功能

from django.db.models import Sum, Avg, Count, Max, Min

# 新模型导入
from django.contrib.auth import get_user_model
User = get_user_model()
from apps.exam.models import Exam, ExamQuestion, ExamAnswer, ExamPaper, GradePublish
from apps.system.models import QuestionTemplate

# 主观题类型常量
SUBJECTIVE_TYPE = 'essay'


def _all_graders_published(exam_id):
    """
    检查某场考试的所有批改员是否都已发布成绩
    无主观题 → True（无需批改）
    无批改员分配 → True（旧数据兼容）
    否则：该考试所有 assigned_grader 都必须有对应的 GradePublish 记录
    """
    # 无主观题的考试无需批改，成绩直接可见
    has_essay = ExamQuestion.objects.filter(
        exam_id=exam_id,
        question_type=SUBJECTIVE_TYPE,
    ).exists()
    if not has_essay:
        return True

    # 获取该考试所有已分配的批改员ID
    grader_ids = set(
        ExamPaper.objects.filter(exam_id=exam_id)
        .exclude(assigned_grader__isnull=True)
        .values_list('assigned_grader_id', flat=True)
    )
    if not grader_ids:
        return True

    # 检查是否所有批改员都已发布
    published_ids = set(
        GradePublish.objects.filter(exam_id=exam_id)
        .values_list('grader_id', flat=True)
    )
    return grader_ids == published_ids


def _build_paper_questions(exam_id, user_id):
    """
    构建试卷题目详情列表（公共方法，供 my_paper 和 paper_detail 复用）
    参数：
        exam_id: 考试ID
        user_id: 考生用户ID
    返回 questions 列表：
        [{question_id, title, question_type, user_answer, correct_answer, score, user_score, analysis}]
    """
    # 批量查询该考生在该考试中的所有题目
    question_items = list(
        ExamQuestion.objects.filter(
            exam_id=exam_id,
            user_id=user_id,
        ).order_by('sort_order')
    )

    if not question_items:
        return []

    # 获取所有题目ID，用于批量查询答案
    question_ids = [q.id for q in question_items]

    # 批量查询答案，构建 question_id -> answer 映射
    answer_map = {}
    for ans in ExamAnswer.objects.filter(question_id__in=question_ids):
        answer_map[ans.question_id] = ans

    # 批量查询模板的解析说明，构建 id -> explanation 映射
    template_ids = [q.template_id for q in question_items if q.template_id]
    explanation_map = {}
    if template_ids:
        for t in QuestionTemplate.objects.filter(id__in=template_ids):
            explanation_map[t.id] = t.explanation or ''

    questions = []
    for q in question_items:
        ans = answer_map.get(q.id)
        # 获取用户答案内容
        user_answer = ans.content if ans else ''
        # 获取用户得分（可能为None，表示尚未批改）
        user_score = ans.score if ans and ans.score is not None else 0
        # 获取批改备注（仅主观题有）
        remark = ans.remark if ans and ans.remark else ''
        # 获取题目模板解析说明
        analysis = explanation_map.get(q.template_id, '') if q.template_id else ''

        questions.append({
            'question_id': q.id,
            'title': q.question_text,
            'question_type': q.question_type,
            'user_answer': user_answer,
            'correct_answer': q.correct_answer or '',
            'score': q.score,
            'user_score': user_score,
            'remark': remark,
            'analysis': analysis,
        })

    return questions


def get_my_score(exam_id, user_id):
    """
    查询我的成绩
    接口：GET /api/score/my/{exam_id}/
    权限：仅辅导员（role=1）
    参数：
        exam_id: 考试ID
        user_id: 考生用户ID
    返回：
        (success, data_or_error)
        data: {score, objective_score, subjective_score}
    """
    # 先校验考试是否存在
    if not Exam.objects.filter(id=exam_id).exists():
        return False, (404, "考试不存在")

    try:
        # 查询该考生在该考试中的记录
        paper = ExamPaper.objects.get(exam_id=exam_id, user_id=user_id)
    except ExamPaper.DoesNotExist:
        # 未参加考试
        return False, (403, "未参加该考试")

    # 试卷批改完成后才可查看成绩
    if not paper.is_graded:
        return False, (403, "成绩尚未发布，暂不可查看")

    # 所有批改员都发布后辅导员才能查看成绩
    if not _all_graders_published(exam_id):
        return False, (403, "成绩尚未发布，暂不可查看")

    return True, {
        'paper_id': paper.id,
        'score': paper.total_score,
        'objective_score': paper.objective_score,
        'subjective_score': paper.subjective_score,
    }


def get_my_paper_detail(paper_id, user_id):
    """
    查询我的考试试卷详情
    接口：GET /api/score/my-paper/{paper_id}/
    权限：仅辅导员（role=1），且 paper_id 必须属于当前用户
    paper_id = ExamPaper.id（原 UserExam.record_id）
    参数：
        paper_id: 考试记录ID（ExamPaper.id）
        user_id: 考生用户ID
    返回：
        (success, data_or_error)
        data: {questions: [...]}
    """
    try:
        # 根据考试记录ID获取试卷记录
        paper = ExamPaper.objects.get(id=paper_id)
    except ExamPaper.DoesNotExist:
        return False, (404, "试卷不存在")

    # 校验该试卷记录是否属于当前用户
    if paper.user_id != user_id:
        return False, (403, "无权查看他人试卷")

    # 成绩未发布（主观题未全部批改完成）时不可查看试卷详情
    if not paper.is_graded:
        return False, (403, "成绩尚未发布，暂不可查看试卷详情")

    # 所有批改员都发布后辅导员才能查看试卷详情
    if not _all_graders_published(paper.exam_id):
        return False, (403, "成绩尚未发布，暂不可查看试卷详情")

    # 构建试卷题目详情
    questions = _build_paper_questions(paper.exam_id, paper.user_id)
    return True, {'questions': questions}


def get_paper_detail(paper_id, viewer_user, query_params=None):
    """
    查看任意考生试卷详情
    接口：GET /api/score/paper-detail/{paper_id}/ 或 GET /api/score/paper-detail/?exam_id=X&user_id=Y
    权限：
        - 超级管理员（role=3）：可查看任何人
        - 批改员（role=2）：仅可查看已批改过该考生的试卷
    参数：
        paper_id: 考试记录ID（ExamPaper.id），可为None表示通过query_params查询
        viewer_user: 当前登录用户对象
        query_params: GET请求的查询参数（当paper_id为None时使用，含exam_id和user_id）
    返回：
        (success, data_or_error)
        data: {questions: [...]}
    """
    # 当 paper_id 未提供时，通过 exam_id + user_id 查找试卷
    if paper_id is None:
        if query_params is None:
            return False, (400, "请提供paper_id或同时提供exam_id和user_id")
        exam_id = query_params.get('exam_id')
        user_id = query_params.get('user_id')
        if not exam_id or not user_id:
            return False, (400, "缺少参数：请提供paper_id，或同时提供exam_id和user_id")
        try:
            exam_id = int(exam_id)
            user_id = int(user_id)
        except (ValueError, TypeError):
            return False, (400, "exam_id和user_id必须为整数")
        try:
            paper = ExamPaper.objects.get(exam_id=exam_id, user_id=user_id)
        except ExamPaper.DoesNotExist:
            return False, (404, "未找到该考生在此考试中的试卷")
    else:
        try:
            # 根据考试记录ID获取试卷记录
            paper = ExamPaper.objects.get(id=paper_id)
        except ExamPaper.DoesNotExist:
            return False, (404, "试卷不存在")

    # role=2 批改员需校验批改关系
    if viewer_user.role == 2:
        # 先找到该考生在此考试中的所有题目ID
        question_ids = ExamQuestion.objects.filter(
            exam_id=paper.exam_id,
            user_id=paper.user_id,
        ).values_list('id', flat=True)

        # 检查当前批改员是否批改过其中任意答案
        graded_count = ExamAnswer.objects.filter(
            question_id__in=question_ids,
            graded_by_id=viewer_user.id,
        ).count()

        if graded_count == 0:
            return False, (403, "无权限查看该考生试卷，未建立批改关系")

    # 构建试卷题目详情
    questions = _build_paper_questions(paper.exam_id, paper.user_id)
    return True, {'questions': questions}


def get_exam_statistics(exam_id):
    """
    考试整体统计（丰富版）
    接口：GET /api/score/statistics/{exam_id}/
    权限：仅超级管理员（role=3）
    参数：
        exam_id: 考试ID
    返回：
        (success, data_or_error)
        data: {
            # 原有字段
            avg_score, attend_rate, objective_score_rate,
            # A.成绩分布
            max_score, min_score, median_score, pass_rate, score_distribution,
            # B.考试进度
            total_counselors, submitted_count, not_started_count,
            in_progress_count, abnormal_count, graded_count, ungraded_count,
            # C.各题型得分率
            subjective_score_rate, type_breakdown,
        }
    """
    # 校验考试是否存在
    if not Exam.objects.filter(id=exam_id).exists():
        return False, (404, "考试不存在")

    # 辅导员总数（role=1，status=1的在职辅导员）
    total_counselors = User.objects.filter(role=1, status=1).count()

    if total_counselors == 0:
        return True, _empty_statistics()

    # 该考试所有试卷记录
    all_papers = ExamPaper.objects.filter(exam_id=exam_id)

    # ---- B. 考试进度统计 ----
    submitted_records = all_papers.filter(status=2)
    submitted_count = submitted_records.count()
    not_started_count = all_papers.filter(status=0).count()
    in_progress_count = all_papers.filter(status=1).count()
    abnormal_count = all_papers.filter(status=3).count()

    # 参考率 = 已交卷人数 / 辅导员总数
    attend_rate = round(submitted_count / total_counselors, 2) if total_counselors > 0 else 0.0

    # 已批改完成的记录
    graded_records = submitted_records.filter(is_graded=True)
    graded_count = graded_records.count()
    ungraded_count = submitted_count - graded_count

    # ---- 客观题/主观题满分基准（取第一个交卷考生的数据） ----
    objective_full_score = 0  # 每考生客观题满分
    subjective_full_score = 0  # 每考生主观题满分
    if submitted_count > 0:
        sample_user_id = submitted_records.first().user_id
        obj_agg = ExamQuestion.objects.filter(
            exam_id=exam_id, user_id=sample_user_id,
        ).exclude(question_type=SUBJECTIVE_TYPE).aggregate(total=Sum('score'))
        objective_full_score = obj_agg['total'] or 0

        subj_agg = ExamQuestion.objects.filter(
            exam_id=exam_id, user_id=sample_user_id, question_type=SUBJECTIVE_TYPE,
        ).aggregate(total=Sum('score'))
        subjective_full_score = subj_agg['total'] or 0

    # ---- A. 成绩分布（仅已批改完成的） ----
    if graded_count > 0:
        score_agg = graded_records.aggregate(
            avg=Avg('total_score'),
            max=Max('total_score'),
            min=Min('total_score'),
        )
        avg_score = round(float(score_agg['avg'] or 0), 1)
        max_score = round(float(score_agg['max'] or 0), 1)
        min_score = round(float(score_agg['min'] or 0), 1)

        # 中位数：取出所有已批改成绩排序后取中位
        score_list = list(
            graded_records.values_list('total_score', flat=True).order_by('total_score')
        )
        n = len(score_list)
        if n % 2 == 0:
            median_score = round((score_list[n // 2 - 1] + score_list[n // 2]) / 2, 1)
        else:
            median_score = round(float(score_list[n // 2]), 1)

        # 分数段分布
        distribution = {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
        pass_count = 0
        for s in score_list:
            if s < 60:
                distribution["0-59"] += 1
            elif s < 70:
                distribution["60-69"] += 1
            elif s < 80:
                distribution["70-79"] += 1
            elif s < 90:
                distribution["80-89"] += 1
            else:
                distribution["90-100"] += 1
            if s >= 60:
                pass_count += 1
        pass_rate = round(pass_count / graded_count, 2)
    else:
        avg_score = 0.0
        max_score = 0.0
        min_score = 0.0
        median_score = 0.0
        pass_rate = 0.0
        distribution = {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}

    # ---- 客观题得分率 ----
    if submitted_count > 0 and objective_full_score > 0:
        obj_sum = submitted_records.aggregate(total=Sum('objective_score'))['total'] or 0
        objective_score_rate = round(float(obj_sum) / (objective_full_score * submitted_count), 2)
    else:
        objective_score_rate = 0.0

    # ---- 主观题得分率 ----
    if submitted_count > 0 and subjective_full_score > 0:
        subj_sum = submitted_records.aggregate(total=Sum('subjective_score'))['total'] or 0
        subjective_score_rate = round(float(subj_sum) / (subjective_full_score * submitted_count), 2)
    else:
        subjective_score_rate = 0.0

    # ---- C. 各题型得分率 ----
    type_breakdown = _get_type_breakdown(exam_id, submitted_records)

    return True, {
        # 原有
        'avg_score': avg_score,
        'attend_rate': attend_rate,
        'objective_score_rate': objective_score_rate,
        # A.成绩分布
        'max_score': max_score,
        'min_score': min_score,
        'median_score': median_score,
        'pass_rate': pass_rate,
        'score_distribution': distribution,
        # B.考试进度
        'total_counselors': total_counselors,
        'submitted_count': submitted_count,
        'not_started_count': not_started_count,
        'in_progress_count': in_progress_count,
        'abnormal_count': abnormal_count,
        'graded_count': graded_count,
        'ungraded_count': ungraded_count,
        # C.各题型得分率
        'subjective_score_rate': subjective_score_rate,
        'type_breakdown': type_breakdown,
    }


def _empty_statistics():
    """
    无辅导员时的空统计数据
    """
    return {
        'avg_score': 0,
        'attend_rate': 0.0,
        'objective_score_rate': 0.0,
        'max_score': 0.0,
        'min_score': 0.0,
        'median_score': 0.0,
        'pass_rate': 0.0,
        'score_distribution': {"0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0},
        'total_counselors': 0,
        'submitted_count': 0,
        'not_started_count': 0,
        'in_progress_count': 0,
        'abnormal_count': 0,
        'graded_count': 0,
        'ungraded_count': 0,
        'subjective_score_rate': 0.0,
        'type_breakdown': {},
    }


def _get_type_breakdown(exam_id, submitted_records):
    """
    计算各题型得分率明细
    参数：
        exam_id: 考试ID
        submitted_records: 已交卷的 ExamPaper QuerySet
    返回：
        {question_type: {total: 满分, avg: 平均实得分, rate: 得分率}}
    """
    # 按题型分组统计每题型的每考生满分
    sample_user_id = submitted_records.first().user_id if submitted_records.exists() else None
    if not sample_user_id:
        return {}

    # 取一份试卷按题型统计满分
    type_full_scores = {}
    for qt in ExamQuestion.objects.filter(exam_id=exam_id, user_id=sample_user_id).values('question_type').annotate(full=Sum('score')):
        type_full_scores[qt['question_type']] = qt['full']

    if not type_full_scores:
        return {}

    submitted_count = submitted_records.count()

    breakdown = {}
    for qtype, full_score in type_full_scores.items():
        # 获取该题型所有题目的ID
        question_ids = ExamQuestion.objects.filter(
            exam_id=exam_id, question_type=qtype,
        ).values_list('id', flat=True)

        # 统计所有已交卷考生在该题型上的实际得分总和
        total_actual = ExamAnswer.objects.filter(
            question_id__in=question_ids,
            score__isnull=False,
        ).aggregate(total=Sum('score'))['total'] or 0

        # 平均每考生实得分
        avg = round(float(total_actual) / submitted_count, 1) if submitted_count > 0 else 0
        # 得分率
        rate = round(avg / full_score, 2) if full_score > 0 else 0

        breakdown[qtype] = {
            'total': full_score,
            'avg': avg,
            'rate': rate,
        }

    return breakdown


def get_unattended_list(exam_id):
    """
    未参考人员清单
    接口：GET /api/score/unattended/{exam_id}/
    权限：仅超级管理员（role=3）
    参数：
        exam_id: 考试ID
    返回：
        (success, data_or_error)
        data: {list: [{name, username}]}
    """
    # 校验考试是否存在
    if not Exam.objects.filter(id=exam_id).exists():
        return False, (404, "考试不存在")

    # 已参加该考试的用户ID集合（排除status=0未开始，即预生成试卷但从未进入的考生）
    attended_user_ids = set(
        ExamPaper.objects.filter(exam_id=exam_id).exclude(status=0).values_list('user_id', flat=True)
    )

    # 所有在职辅导员
    all_counselors = User.objects.filter(role=1, status=1)

    # 构建未参考人员列表
    unattended = []
    for counselor in all_counselors.order_by('username'):
        if counselor.id not in attended_user_ids:
            unattended.append({
                'name': counselor.display_name or counselor.username,
                'username': counselor.username,
            })

    return True, {'list': unattended}


def export_exam_scores(exam_id, export_scope='all'):
    """
    导出成绩Excel
    接口：GET /api/score/export/{exam_id}/
    权限：仅超级管理员（role=3）
    参数：
        exam_id: 考试ID
        export_scope: all=全部，graded_only=仅已出成绩
    返回：
        (success, data_or_file_response)
    """
    # 校验考试是否存在
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, (404, "考试不存在")

    # 查询考试记录（已交卷的）
    records = ExamPaper.objects.filter(exam_id=exam_id, status=2)

    # 根据导出范围过滤
    if export_scope == 'graded_only':
        records = records.filter(is_graded=True)

    # 批量查询用户信息，构建 user_id -> (username, display_name) 映射
    user_ids = list(records.values_list('user_id', flat=True))
    user_info_map = {}  # user_id -> (username, display_name)
    if user_ids:
        for u in User.objects.filter(id__in=user_ids):
            user_info_map[u.id] = (u.username, u.display_name or u.username)

    # 使用公共Excel工具类创建文件响应
    from utils.excel import create_excel_response

    headers = ['序号', '辅导员工号', '辅导员姓名', '客观题得分', '主观题得分', '总成绩', '是否批改完成', '交卷时间']
    data_rows = []

    row_num = 1
    for record in records.order_by('user_id'):
        row_num += 1
        user_info = user_info_map.get(record.user_id, (str(record.user_id), str(record.user_id)))
        username, teacher_name = user_info
        is_graded_str = '是' if record.is_graded else '否'
        submitted_at_str = record.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if record.submitted_at else ''

        data_rows.append([
            row_num - 1,
            username,
            teacher_name,
            record.objective_score,
            record.subjective_score,
            record.total_score,
            is_graded_str,
            submitted_at_str,
        ])

    response = create_excel_response(
        filename=f"{exam.name}考试成绩",
        sheet_title='考试成绩',
        headers=headers,
        rows=data_rows,
    )

    return True, response
