from django.contrib import admin
from .models import Program, Subject

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_years', 'total_semesters', 'is_active', 'created_at']
    list_filter = ['is_active', 'duration_years']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'duration_years', 'total_semesters')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'program', 'semester', 'credits', 'max_marks', 'passing_marks', 'is_active']
    list_filter = ['program', 'semester', 'is_active', 'credits']
    search_fields = ['code', 'name']
    ordering = ['program', 'semester', 'code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('program', 'code', 'name', 'semester')
        }),
        ('Credits & Marks', {
            'fields': ('credits', 'max_marks', 'passing_marks')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )