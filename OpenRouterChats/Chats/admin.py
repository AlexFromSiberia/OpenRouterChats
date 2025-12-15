from django.contrib import admin

# Register your models here.

from .models import Users, Teachers


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'login', 'type', 'is_active')
    search_fields = ('login','type', 'is_active',)


@admin.register(Teachers)
class TeachersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'prompt',)
    search_fields = ('name',)


