from django.conf.urls.static import static
from django.urls import path, register_converter

from app_domainname import settings
from . import views, converters

urlpatterns = [
    path('', views.homepage, name='homepage'),                                     # http://127.0.0.1:8000/
    path('upload_file/', views.upload_file, name='upload_file'),                   # http://127.0.0.1:8000/upload_file
    path('delete_doc/', views.delete_doc, name='delete_doc'),                      # http://127.0.0.1:8000/delete_doc
    path('doc_analyze/', views.doc_analyze, name='doc_analyze'),                   # http://127.0.0.1:8000/doc_analyze
    path('get_text/', views.get_text, name='get_text'),                            # http://127.0.0.1:8000/get_text
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)