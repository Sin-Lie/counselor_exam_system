# 辅导员考试系统 - 总路由配置

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.auth.urls import admin_urlpatterns
from apps.practice.urls import collection_urlpatterns

# 总路由列表
urlpatterns = [
    path('api/auth/', include('apps.auth.urls')),
    path('api/admin/', include(admin_urlpatterns)),
    path('api/practice/', include('apps.practice.urls')),
    path('api/collection/', include(collection_urlpatterns)),
    path('api/exam/', include('apps.exam.urls')),
    path('api/correct/', include('apps.correct.urls')),
    path('api/score/', include('apps.score.urls')),
    path('api/system/', include('apps.system.urls')),
]

# 开发环境添加媒体文件访问和Django Admin支持
if settings.DEBUG:
    from django.contrib import admin
    from django.views.static import serve
    urlpatterns.insert(0, path('admin/', admin.site.urls))
    # 学生照片专用路由 — 从 STUDENT_PHOTO_DIR 提供服务（优先级高于 MEDIA_URL）
    urlpatterns += [
        path('media/students_photo/<path:path>', serve, {
            'document_root': str(settings.STUDENT_PHOTO_DIR),
        }),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
