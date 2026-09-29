import os
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from django.http import FileResponse, Http404
from django.conf import settings

FRONTEND_DIR = settings.BASE_DIR.parent

def serve_frontend(request, page='index.html'):
    path_to_file = FRONTEND_DIR / page
    if os.path.exists(path_to_file):
        return FileResponse(open(path_to_file, 'rb'))
    raise Http404("File not found")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    
    # Static files for frontend (css, js)
    re_path(r'^css/(?P<path>.*)$', serve, {'document_root': str(FRONTEND_DIR / 'css')}),
    re_path(r'^js/(?P<path>.*)$', serve, {'document_root': str(FRONTEND_DIR / 'js')}),

    # Direct pages
    path('', lambda req: serve_frontend(req, 'index.html'), name='home'),
    path('index.html', lambda req: serve_frontend(req, 'index.html'), name='index'),
    path('login.html', lambda req: serve_frontend(req, 'login.html'), name='login'),
    path('dashboard.html', lambda req: serve_frontend(req, 'dashboard.html'), name='dashboard'),
]

