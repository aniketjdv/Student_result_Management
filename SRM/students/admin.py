from django.contrib import admin
from .models import Student, StudentDocument, StudentFee


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'enrollment_number', 'get_full_name', 'program', 
        'batch_year', 'current_semester', 'is_active'
    ]
    list_filter = ['program', 'batch_year', 'current_semester', 'is_active', 'gender']
    search_fields = [
        'enrollment_number', 'user__first_name', 'user__last_name', 
        'user__email', 'personal_phone'
    ]
    ordering = ['-batch_year', 'enrollment_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Academic Information', {
            'fields': (
                'enrollment_number', 'program', 'batch_year', 
                'current_semester', 'admission_date', 'admission_type'
            )
        }),
        ('Personal Information', {
            'fields': (
                'date_of_birth', 'gender', 'blood_group', 
                'nationality', 'category'
            )
        }),
        ('Contact Information', {
            'fields': (
                'personal_phone', 'personal_email', 'address', 
                'city', 'state', 'pincode'
            )
        }),
        ('Guardian Information', {
            'fields': (
                'guardian_name', 'guardian_relation', 'guardian_phone',
                'guardian_email', 'guardian_occupation'
            )
        }),
        ('Previous Education', {
            'fields': (
                'previous_institution', 'previous_degree', 
                'previous_percentage', 'previous_passing_year'
            )
        }),
        ('Documents', {
            'fields': ('photo', 'id_proof')
        }),
        ('Status', {
            'fields': (
                'is_active', 'is_hostel_resident', 'is_scholarship_holder'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'document_type', 'document_name', 'uploaded_date']
    list_filter = ['document_type', 'uploaded_date']
    search_fields = ['student__enrollment_number', 'document_name']
    ordering = ['-uploaded_date']


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'semester', 'academic_year', 'fee_type',
        'total_amount', 'paid_amount', 'payment_status', 'due_date'
    ]
    list_filter = ['payment_status', 'semester', 'academic_year']
    search_fields = ['student__enrollment_number', 'fee_type', 'receipt_number']
    ordering = ['-academic_year', '-semester', 'student__enrollment_number']
    
    fieldsets = (
        ('Student & Period', {
            'fields': ('student', 'semester', 'academic_year')
        }),
        ('Fee Details', {
            'fields': ('fee_type', 'total_amount', 'due_date')
        }),
        ('Payment Information', {
            'fields': (
                'paid_amount', 'payment_status', 'payment_date',
                'payment_mode', 'transaction_id', 'receipt_number'
            )
        }),
        ('Additional Info', {
            'fields': ('remarks',)
        }),
    )
