from django.contrib import admin
from .models import Teacher, TeacherLeave, TeacherDocument, TeacherAttendance, TeacherTimeTable


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 'get_full_name', 'department', 
        'designation', 'experience_years', 'is_active'
    ]
    list_filter = ['department', 'designation', 'is_active', 'employment_type']
    search_fields = [
        'employee_id', 'user__first_name', 'user__last_name', 
        'user__email', 'department'
    ]
    ordering = ['department', 'designation', 'user__first_name']
    filter_horizontal = ['subjects']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': (
                'employee_id', 'department', 'designation', 
                'qualification', 'specialization', 'experience_years',
                'previous_institution'
            )
        }),
        ('Contact Information', {
            'fields': (
                'office_phone', 'personal_phone', 'personal_email',
                'address', 'city', 'state', 'pincode'
            )
        }),
        ('Employment Details', {
            'fields': (
                'joining_date', 'employment_type', 'salary'
            )
        }),
        ('Subject Assignment', {
            'fields': ('subjects',)
        }),
        ('Personal Information', {
            'fields': (
                'date_of_birth', 'gender', 'blood_group', 'nationality'
            )
        }),
        ('Documents', {
            'fields': ('photo', 'resume', 'id_proof')
        }),
        ('Research & Publications', {
            'fields': (
                'research_interests', 'publications_count',
                'google_scholar_url', 'linkedin_url'
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_hod', 'can_approve_results')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(TeacherLeave)
class TeacherLeaveAdmin(admin.ModelAdmin):
    list_display = [
        'teacher', 'leave_type', 'start_date', 'end_date', 
        'total_days', 'status', 'applied_date'
    ]
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['teacher__employee_id', 'teacher__user__first_name']
    ordering = ['-applied_date']
    readonly_fields = ['applied_date', 'total_days']


@admin.register(TeacherDocument)
class TeacherDocumentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'document_type', 'document_name', 'uploaded_date']
    list_filter = ['document_type', 'uploaded_date']
    search_fields = ['teacher__employee_id', 'document_name']
    ordering = ['-uploaded_date']


@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['teacher__employee_id']
    ordering = ['-date']


@admin.register(TeacherTimeTable)
class TeacherTimeTableAdmin(admin.ModelAdmin):
    list_display = [
        'teacher', 'subject', 'day', 'start_time', 
        'end_time', 'room_number', 'semester'
    ]
    list_filter = ['day', 'semester', 'academic_year']
    search_fields = ['teacher__employee_id', 'subject__code', 'room_number']
    ordering = ['day', 'start_time']