# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0004_add_ai_grade_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='examquestion',
            name='student_sort_order',
            field=models.IntegerField(blank=True, null=True, verbose_name='学生组内题号'),
        ),
    ]
