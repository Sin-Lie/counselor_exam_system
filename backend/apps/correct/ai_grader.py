# -*- coding: utf-8 -*-
# AI 批改核心服务
# 负责构造 prompt、调用大模型 API、解析返回 JSON
# 支持所有兼容 OpenAI chat/completions 接口的大模型服务

import json
import re
import time
import logging

import httpx

from django.utils import timezone

# 主观题类型常量
SUBJECTIVE_TYPE = 'essay'

# 学生信息字段中文映射 — 学生信息表字段名到中文标签的映射（services.py 从此处导入）
STUDENT_FIELD_LABELS = {
    'id': '学号',
    'name': '姓名',
    'gender': '性别',
    'college': '学院',
    'grade': '年级',
    'class_name': '班级',
    'ethnicity': '民族',
    'native_place': '籍贯',
    'origin_place': '生源地',
    'family_address': '家庭所在地',
    'household_address': '户籍所在地',
    'is_academic_difficulty': '是否学业困难',
    'religion': '宗教信仰',
    'dorm_address': '住宿地址',
    'off_campus_address': '校外住宿地址',
    'is_financial_difficulty': '是否经济困难',
    'enrollment_status': '学籍状态',
}

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = (
    "你是一个专业的高校辅导员业务考试主观题批改助手。"
    "请根据标准答案和题目要求，对学生的作答进行客观公正的评分。"
    "评分时请重点关注：关键信息点是否完整、表述是否准确、逻辑是否清晰。"
)

logger = logging.getLogger('correct')


def _get_standard_answer_for_ai(question_item):
    """
    获取简答题的标准答案，格式化为 AI 可读的键值对
    参数：
        question_item: ExamQuestion 实例
    返回：标准答案字典（中文字段名 → 值）
    """
    student = question_item.student
    if not student:
        return {}

    result = {}
    for field, label in STUDENT_FIELD_LABELS.items():
        value = getattr(student, field, None)
        if field in ('is_academic_difficulty', 'is_financial_difficulty'):
            value = '是' if value else '否'
        elif value is None:
            value = ''
        else:
            value = str(value)
            if field == 'native_place':
                from apps.exam.services import _normalize_native_place
                value = _normalize_native_place(value)
        result[label] = value
    return result


def _build_prompt(question_item, answer_content, config):
    """
    构造发送给大模型的完整 prompt
    参数：
        question_item: ExamQuestion 实例
        answer_content: 考生作答内容
        config: AIGradeConfig 实例
    返回：系统提示词、用户消息
    """
    # 获取标准答案
    standard_answer = _get_standard_answer_for_ai(question_item)

    # 构造用户消息
    user_message_parts = [
        f"题目：{question_item.question_text}",
        f"满分：{question_item.score} 分",
        f"标准答案（学生真实信息）：",
        json.dumps(standard_answer, ensure_ascii=False, indent=2),
        f"学生答案：{answer_content or '（未作答）'}",
        "",
        "请对以上作答进行评分，返回严格 JSON 格式（不要包含 markdown 代码块标记，只返回纯 JSON）：",
        '{"score": <整数, 0到满分之间>, "remark": "<评分理由, 50字以内>"}',
    ]

    system_prompt = config.system_prompt or DEFAULT_SYSTEM_PROMPT
    user_message = "\n".join(user_message_parts)

    return system_prompt, user_message


def _call_llm_api(config, system_prompt, user_message):
    """
    调用大模型 API
    使用 httpx 发送 HTTP 请求，兼容 OpenAI chat/completions 格式
    参数：
        config: AIGradeConfig 实例
        system_prompt: 系统提示词
        user_message: 用户消息
    返回：(success, data_or_error_str)
        success=True 时 data 为 {"score": int, "remark": str}
        success=False 时返回错误字符串
    """
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json',
    }

    payload = {
        'model': config.model_name,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ],
        'temperature': config.temperature,
        'max_tokens': config.max_tokens,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                config.api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            response_data = response.json()

            # 解析 OpenAI 格式的返回
            content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')

            # 尝试从 content 中提取 JSON，同时保留原始返回文本
            success, result = _parse_ai_response(content)
            if success:
                return True, {
                    'score': result['score'],
                    'remark': result['remark'],
                    'raw_response': content,
                }
            else:
                return False, f"AI 解析失败: {result}"

    except httpx.HTTPStatusError as e:
        error_body = ''
        try:
            error_body = e.response.text
        except Exception:
            pass
        return False, f"API 调用失败 (HTTP {e.response.status_code}): {error_body[:500]}"
    except httpx.RequestError as e:
        return False, f"网络请求失败: {str(e)}"
    except Exception as e:
        return False, f"调用 AI 异常: {str(e)}"


def _parse_ai_response(content):
    """
    解析 AI 返回的内容，提取 JSON
    兼容 AI 可能包裹 markdown 代码块的情况
    参数：
        content: AI 返回的文本内容
    返回：(success, data_or_error_str)
    """
    if not content:
        return False, "AI 返回内容为空"

    # 尝试直接解析 JSON
    try:
        data = json.loads(content.strip())
        score = data.get('score')
        remark = data.get('remark', '')
        if score is None:
            return False, f"AI 返回缺少 score 字段，原始内容: {content[:200]}"
        if not isinstance(score, (int, float)):
            return False, f"AI 返回的 score 不是数字，原始内容: {content[:200]}"
        return True, {'score': int(score), 'remark': str(remark)[:500]}
    except json.JSONDecodeError:
        pass

    # 尝试从 markdown 代码块中提取 JSON
    json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', content)
    if json_match:
        try:
            data = json.loads(json_match.group(1).strip())
            score = data.get('score')
            remark = data.get('remark', '')
            if score is not None and isinstance(score, (int, float)):
                return True, {'score': int(score), 'remark': str(remark)[:500]}
        except json.JSONDecodeError:
            pass

    # 尝试用正则提取 {score: xxx, remark: "xxx"}
    score_match = re.search(r'"score"\s*:\s*(\d+)', content)
    remark_match = re.search(r'"remark"\s*:\s*"([^"]*)"', content)
    if score_match:
        score = int(score_match.group(1))
        remark = remark_match.group(1) if remark_match else ''
        return True, {'score': score, 'remark': remark[:500]}

    return False, f"无法解析 AI 返回，原始内容: {content[:500]}"


def ai_grade_one_answer(answer, config):
    """
    对单个答案执行 AI 批改
    参数：
        answer: ExamAnswer 实例（subject_type=essay, score IS NULL）
        config: AIGradeConfig 实例
    返回：
        (success, result_dict)
        success=True: result_dict 包含 score, remark, latency_ms
        success=False: result_dict 包含 error_msg
    """
    import time as time_module
    start_time = time_module.time()

    from apps.exam.models import ExamQuestion

    # 获取题目信息
    try:
        question_item = ExamQuestion.objects.select_related('student').get(id=answer.question_id)
    except ExamQuestion.DoesNotExist:
        return False, {'error_msg': f"题目不存在 (question_id={answer.question_id})"}

    # 构造 prompt
    system_prompt, user_message = _build_prompt(question_item, answer.content, config)

    # 调用 API
    success, result = _call_llm_api(config, system_prompt, user_message)
    latency_ms = int((time_module.time() - start_time) * 1000)

    if success:
        return True, {
            'score': result['score'],
            'remark': result['remark'],
            'latency_ms': latency_ms,
            'system_prompt': system_prompt,
            'user_message': user_message,
            'raw_response': result.get('raw_response', ''),
        }
    else:
        return False, {
            'error_msg': result,
            'latency_ms': latency_ms,
            'system_prompt': system_prompt,
            'user_message': user_message,
            'raw_response': result.get('raw_response', ''),
        }


def ai_grade_batch_for_exam(exam_id):
    """
    对某考试的所有已交卷试卷中未批改的主观题执行 AI 批改
    参数：
        exam_id: 考试 ID
    返回：
        (total_count, success_count, failed_count)
    """
    from apps.exam.models import Exam, ExamQuestion, ExamAnswer, ExamPaper
    from apps.correct.models import AIGradeLog
    from django.db.models import Sum

    # 获取 AI 配置
    config = AIGradeConfig.objects.first()
    if not config or not config.is_active:
        return 0, 0, 0

    # 检查考试是否开启了 AI 批改
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return 0, 0, 0

    if not exam.ai_grade_enabled:
        return 0, 0, 0

    # 查询该考试所有已交卷试卷
    paper_pairs = list(
        ExamPaper.objects.filter(exam_id=exam_id, status=2)
        .values_list('exam_id', 'user_id')
    )
    if not paper_pairs:
        return 0, 0, 0

    from functools import reduce
    from operator import or_
    from django.db.models import Q

    # 构建 OR 条件查询所有主观题
    pair_conditions = reduce(or_, (
        Q(exam_id=eid, user_id=uid) for eid, uid in paper_pairs
    ))
    essay_question_ids = ExamQuestion.objects.filter(
        pair_conditions,
        question_type=SUBJECTIVE_TYPE,
    ).values_list('id', flat=True)

    # 只批改未评分（score IS NULL）的答案
    ungraded_answers = ExamAnswer.objects.filter(
        question_id__in=essay_question_ids,
        score__isnull=True,
    ).select_related('question__student')

    total_count = ungraded_answers.count()
    success_count = 0
    failed_count = 0

    for answer in ungraded_answers:
        # 执行 AI 批改
        success, result = ai_grade_one_answer(answer, config)

        # 写入 AI 日志
        AIGradeLog.objects.create(
            answer_id=answer.id,
            model_name=config.model_name,
            prompt_sent=result.get('system_prompt', '') + '\n\n' + result.get('user_message', ''),
            response_raw=result.get('raw_response', ''),
            score_returned=result.get('score') if success else None,
            remark_returned=result.get('remark', '') if success else '',
            latency_ms=result.get('latency_ms'),
            status='success' if success else 'failed',
            error_msg=result.get('error_msg', '') if not success else '',
        )

        if success:
            # 校验 AI 返回的分数范围
            try:
                question_item = ExamQuestion.objects.get(id=answer.question_id)
                max_score = question_item.score
                ai_score = result['score']
                if ai_score < 0:
                    ai_score = 0
                if ai_score > max_score:
                    ai_score = max_score
            except ExamQuestion.DoesNotExist:
                continue

            # 更新作答记录的批改信息
            answer.score = ai_score
            answer.graded_by = None  # AI 批改无批改员
            answer.graded_at = timezone.now()
            answer.remark = f"[AI批改] {result['remark']}"
            answer.save(update_fields=['score', 'graded_by', 'graded_at', 'remark'])
            success_count += 1
        else:
            failed_count += 1

    # 全部答完题后，重新计算每张试卷的主观题总分和总成绩
    _recalc_exam_papers(exam_id, paper_pairs)

    return total_count, success_count, failed_count


def _recalc_exam_papers(exam_id, paper_pairs):
    """
    重算指定试卷的主观题总分和总成绩
    参数：
        exam_id: 考试 ID
        paper_pairs: [(exam_id, user_id), ...]
    """
    from apps.exam.models import ExamQuestion, ExamAnswer, ExamPaper
    from django.db.models import Sum

    for eid, uid in paper_pairs:
        try:
            paper = ExamPaper.objects.get(exam_id=eid, user_id=uid)
        except ExamPaper.DoesNotExist:
            continue

        # 统计主观题已批改总分
        essay_question_ids = ExamQuestion.objects.filter(
            exam_id=eid,
            user_id=uid,
            question_type=SUBJECTIVE_TYPE,
        ).values_list('id', flat=True)

        subj_result = ExamAnswer.objects.filter(
            question_id__in=essay_question_ids,
            score__isnull=False,
        ).aggregate(total=Sum('score'))

        subj_total = subj_result['total'] or 0
        paper.subjective_score = subj_total
        paper.total_score = paper.objective_score + subj_total

        # 检查是否所有主观题已批改完成
        ungraded_count = ExamAnswer.objects.filter(
            question_id__in=essay_question_ids,
            score__isnull=True,
        ).count()
        paper.is_graded = 1 if ungraded_count == 0 else 0
        paper.save(update_fields=['subjective_score', 'total_score', 'is_graded'])
