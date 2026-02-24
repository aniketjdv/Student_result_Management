from django.contrib import admin
from .models import SemesterResult, SubjectMarks, Attendance, ResultPublication


@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'semester', 'academic_year', 'sgpa', 'is_published', 'published_date']
    list_filter = ['is_published', 'semester', 'academic_year', 'student__program']
    search_fields = ['student__enrollment_number', 'student__user__first_name', 'student__user__last_name']
    ordering = ['-academic_year', '-semester', 'student__enrollment_number']
    readonly_fields = ['sgpa', 'total_credits', 'credits_earned']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'semester', 'academic_year')
        }),
        ('Result Data', {
            'fields': ('sgpa', 'total_credits', 'credits_earned', 'remarks')
        }),
        ('Publication Status', {
            'fields': ('is_published', 'published_date')
        }),
    )


@admin.register(SubjectMarks)
class SubjectMarksAdmin(admin.ModelAdmin):
    list_display = ['semester_result', 'subject', 'internal_marks', 'external_marks', 'total_marks', 'grade', 'is_passed']
    list_filter = ['grade', 'is_passed', 'subject__program', 'semester_result__semester']
    search_fields = [
        'semester_result__student__enrollment_number',
        'semester_result__student__user__first_name',
        'subject__code',
        'subject__name'
    ]
    ordering = ['-semester_result__semester', 'semester_result__student__enrollment_number']
    readonly_fields = ['total_marks', 'grade', 'grade_point', 'is_passed']
    
    fieldsets = (
        ('Subject Information', {
            'fields': ('semester_result', 'subject', 'teacher')
        }),
        ('Marks', {
            'fields': ('internal_marks', 'external_marks', 'total_marks')
        }),
        ('Grade', {
            'fields': ('grade', 'grade_point', 'is_passed')
        }),
        ('Additional Info', {
            'fields': ('remarks',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'semester', 'total_classes', 'attended_classes', 'percentage', 'status']
    list_filter = ['semester', 'academic_year', 'subject__program']
    search_fields = ['student__enrollment_number', 'student__user__first_name', 'subject__code']
    ordering = ['-semester', 'student__enrollment_number']
    readonly_fields = ['percentage']


@admin.register(ResultPublication)
class ResultPublicationAdmin(admin.ModelAdmin):
    list_display = ['semester', 'academic_year', 'program', 'published_by', 'published_date', 'total_students']
    list_filter = ['semester', 'academic_year', 'program', 'published_date']
    search_fields = ['semester', 'academic_year', 'published_by__username']
    ordering = ['-published_date']
    readonly_fields = ['published_date']