# -*- coding: utf-8 -*-
"""
一次性修复历史试卷中 correct_answer 为空的多选题。

默认只做 dry-run；确认输出无误后加 --apply 才会写库。
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q, Sum

from apps.exam.models import ExamAnswer, ExamPaper, ExamQuestion
from apps.exam.services import (
    OBJECTIVE_TYPES,
    _build_none_of_above_options,
    _build_true_multi_option_text,
    _generate_dynamic_options,
    _judge_objective_answer,
    _normalize_special_match_value,
    _resolve_generated_question_type,
)
from apps.system.models import Student


OPTION_LABELS = ('A', 'B', 'C', 'D')


class Command(BaseCommand):
    help = '修复 exam_questions 中 correct_answer 为空的多选题'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='实际写入数据库；不加时只预览将要修复的题目',
        )
        parser.add_argument(
            '--exam-id',
            type=int,
            help='只修复指定考试 ID 的题目',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='最多处理多少道空答案多选题，便于小批量验证',
        )
        parser.add_argument(
            '--regrade-submitted',
            action='store_true',
            help='修复标准答案后，重算已交卷试卷中对应客观题得分',
        )
        parser.add_argument(
            '--show-skipped',
            action='store_true',
            help='输出无法自动修复的题目明细',
        )

    def handle(self, *args, **options):
        should_apply = options['apply']
        regrade_submitted = options['regrade_submitted']

        questions = self._get_target_questions(
            exam_id=options.get('exam_id'),
            limit=options.get('limit'),
        )

        if not questions:
            self.stdout.write(self.style.SUCCESS('未发现 correct_answer 为空的多选题。'))
            return

        self.stdout.write(
            f"发现 {len(questions)} 道 correct_answer 为空的多选题。"
            f" 当前模式：{'写入数据库' if should_apply else 'dry-run 预览'}"
        )

        fixed_count = 0
        skipped_count = 0
        regraded_answer_count = 0
        affected_paper_keys = set()

        context = transaction.atomic() if should_apply else _NoopContext()
        with context:
            for question in questions:
                fix = self._build_fix(question)
                if not fix['correct_answer']:
                    skipped_count += 1
                    if options['show_skipped']:
                        self.stdout.write(
                            self.style.WARNING(
                                f"跳过 question_id={question.id}: {fix['reason']}"
                            )
                        )
                    continue

                fixed_count += 1
                self.stdout.write(
                    f"[{'APPLY' if should_apply else 'DRY'}] "
                    f"question_id={question.id}, exam_id={question.exam_id}, "
                    f"user_id={question.user_id}, answer={fix['correct_answer']}, "
                    f"reason={fix['reason']}"
                )

                if not should_apply:
                    continue

                question.options = fix['options']
                question.correct_answer = fix['correct_answer']
                update_fields = ['options', 'correct_answer']
                if fix.get('question_text'):
                    question.question_text = fix['question_text']
                    update_fields.append('question_text')
                if fix.get('question_type') and question.question_type != fix['question_type']:
                    question.question_type = fix['question_type']
                    update_fields.append('question_type')
                question.save(update_fields=update_fields)

                if regrade_submitted:
                    changed = self._regrade_question_answers(question)
                    regraded_answer_count += changed
                    affected_paper_keys.add((question.exam_id, question.user_id))

            updated_paper_count = 0
            if should_apply and regrade_submitted and affected_paper_keys:
                updated_paper_count = self._refresh_paper_scores(affected_paper_keys)
            else:
                updated_paper_count = 0

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f"处理完成：可修复 {fixed_count} 道，跳过 {skipped_count} 道。"
            )
        )
        if should_apply and regrade_submitted:
            self.stdout.write(
                self.style.SUCCESS(
                    f"重算答案 {regraded_answer_count} 条，刷新试卷成绩 {updated_paper_count} 份。"
                )
            )
        if not should_apply:
            self.stdout.write('当前为 dry-run，未写入数据库；确认无误后加 --apply 执行。')

    def _get_target_questions(self, exam_id=None, limit=None):
        queryset = (
            ExamQuestion.objects
            .filter(question_type='multi')
            .filter(Q(correct_answer__isnull=True) | Q(correct_answer=''))
            .select_related('exam', 'user', 'student', 'template')
            .order_by('id')
        )
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)
        if limit:
            queryset = queryset[:limit]
        return list(queryset)

    def _build_fix(self, question):
        if not question.template_id:
            return self._empty_fix('题目没有关联模板，无法判断正确答案')
        if not question.student_id:
            return self._empty_fix('题目没有关联学生，无法判断正确答案')

        all_students = list(Student.objects.filter(advisor_id=question.user_id))
        if not all_students:
            all_students = [question.student]

        options, correct_answer = _generate_dynamic_options(
            question.template,
            question.student,
            all_students,
        )
        if self._is_valid_answer(options, correct_answer):
            return {
                'options': options,
                'correct_answer': correct_answer,
                'question_type': _resolve_generated_question_type(question.template),
                'reason': '重新生成后得到有效答案',
            }

        param_field = (question.template.param_field or '').strip()
        if param_field in ('roommates', 'classmates'):
            return self._fix_special_multi(question, all_students, param_field)

        return self._fix_field_multi(question, options)

    def _fix_special_multi(self, question, all_students, keyword):
        match_field = 'dorm_address' if keyword == 'roommates' else 'class_name'
        student_value = _normalize_special_match_value(question.student, match_field)
        candidates = all_students
        if keyword == 'roommates':
            student_gender = (question.student.gender or '').strip()
            if student_gender:
                candidates = [
                    student for student in candidates
                    if (student.gender or '').strip() == student_gender
                ]

        known_students = [
            student for student in candidates
            if student.id != question.student_id
            and _normalize_special_match_value(student, match_field)
        ]
        matches = [
            student for student in known_students
            if _normalize_special_match_value(student, match_field) == student_value
        ]
        non_matches = [
            student for student in known_students
            if _normalize_special_match_value(student, match_field) != student_value
        ]

        if student_value and matches:
            options, correct_answer = _generate_dynamic_options(
                question.template,
                question.student,
                all_students,
            )
            if self._is_valid_answer(options, correct_answer):
                return {
                    'options': options,
                    'correct_answer': correct_answer,
                    'question_type': _resolve_generated_question_type(question.template),
                    'reason': '特殊多选重新生成后得到有效答案',
                }

        random_names = [student.name for student in non_matches]
        options, label = _build_none_of_above_options(random_names)
        return {
            'options': options,
            'correct_answer': label,
            'reason': f'{keyword} 无匹配学生，加入“以上都不是”兜底答案',
        }

    def _fix_field_multi(self, question, generated_options):
        options = self._normalize_options(question.options or generated_options)
        label = self._pick_label_for_fallback(options)
        entries = [
            entry.strip()
            for entry in (question.template.param_field or '').split(',')
            if entry.strip()
        ]
        option_text = _build_true_multi_option_text(question.student, entries)
        if option_text:
            reason = '普通多选无匹配项，替换一个选项为学生真实信息'
        else:
            option_text = '以上都不正确'
            reason = '普通多选无匹配项，加入“以上都不正确”兜底答案'

        options[label] = option_text
        return {
            'options': options,
            'correct_answer': label,
            'reason': reason,
        }

    def _normalize_options(self, options):
        normalized = {}
        if isinstance(options, dict):
            for label in OPTION_LABELS:
                value = options.get(label)
                normalized[label] = '' if value is None else str(value)

        for label in OPTION_LABELS:
            if label not in normalized or normalized[label] == '':
                normalized[label] = f'选项{label}'
        return normalized

    def _pick_label_for_fallback(self, options):
        for label in reversed(OPTION_LABELS):
            if not options.get(label) or options.get(label, '').startswith('选项'):
                return label
        return OPTION_LABELS[-1]

    def _is_valid_answer(self, options, correct_answer):
        if not isinstance(options, dict) or not correct_answer:
            return False
        labels = {
            item.strip().upper()
            for item in str(correct_answer).replace('，', ',').split(',')
            if item.strip()
        }
        if not labels:
            return False
        return labels.issubset(set(options.keys()))

    def _regrade_question_answers(self, question):
        if not ExamPaper.objects.filter(
            exam_id=question.exam_id,
            user_id=question.user_id,
            status=ExamPaper.Status.SUBMITTED,
        ).exists():
            return 0

        changed_count = 0
        answers = ExamAnswer.objects.filter(question_id=question.id)
        for answer in answers:
            is_correct = _judge_objective_answer(
                answer.content or '',
                question.correct_answer,
                question.question_type,
            )
            score = question.score if is_correct else 0
            if answer.is_correct != is_correct or answer.score != score:
                answer.is_correct = is_correct
                answer.score = score
                answer.save(update_fields=['is_correct', 'score'])
                changed_count += 1
        return changed_count

    def _refresh_paper_scores(self, paper_keys):
        updated_count = 0
        for exam_id, user_id in paper_keys:
            try:
                paper = ExamPaper.objects.get(
                    exam_id=exam_id,
                    user_id=user_id,
                    status=ExamPaper.Status.SUBMITTED,
                )
            except ExamPaper.DoesNotExist:
                continue

            objective_score = (
                ExamAnswer.objects
                .filter(
                    question__exam_id=exam_id,
                    question__user_id=user_id,
                    question__question_type__in=OBJECTIVE_TYPES,
                )
                .aggregate(total=Sum('score'))
                .get('total')
                or 0
            )
            paper.objective_score = objective_score
            paper.total_score = objective_score + (paper.subjective_score or 0)
            paper.save(update_fields=['objective_score', 'total_score'])
            updated_count += 1
        return updated_count

    def _empty_fix(self, reason):
        return {
            'options': None,
            'correct_answer': '',
            'reason': reason,
        }


class _NoopContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False
