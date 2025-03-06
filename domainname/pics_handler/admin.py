from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Docs, UsersToDocs

@admin.register(Docs)
class DocsAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at', 'file_path', 'size', 'file_original_name')
    ordering = ('id',)
    list_per_page = 2
    search_fields = ('file_original_name',)
    list_filter = ('size', 'file_original_name')

@admin.register(UsersToDocs)
class UsersToDocsAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at', 'username', 'docs_id')
    ordering = ('id',)
    list_per_page = 3


# admin.site.register(UsersToDocs)

# ToDo