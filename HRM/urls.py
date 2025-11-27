from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('emp.urls')),
    path('api/', include('hr.urls')),
    path('api/', include('tl.urls')),
    path('api/', include('intern.urls')),
    path('api/', include('login.urls')),
    path('api/', include('management.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
