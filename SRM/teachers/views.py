from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
import json

from .models import Teacher, TeacherLeave, TeacherDocument, TeacherAttendance, TeacherTimeTable
from .forms import (
    TeacherForm, TeacherEditForm, TeacherLeaveForm, 
    TeacherDocumentForm, SubjectAssignmentForm
)
from accounts.models import User
from courses.models import Subject, Program
from students.models import Student
from results.models import SubjectMarks, SemesterResult


# Helper functions
def is_admin(user):
    return user.role == 'admin'

def is_teacher(user):
    return user.role == 'teacher'


# ============= ADMIN VIEWS - TEACHER MANAGEMENT =============

@login_required
@user_passes_test(is_admin)
def teacher_list(request):
    """List all teachers with filtering and search"""
    teachers = Teacher.objects.select_related('user').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        teachers = teachers.filter(
            Q(employee_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    
    # Filter by department
    department_filter = request.GET.get('department')
    if department_filter:
        teachers = teachers.filter(department=department_filter)
    
    # Filter by designation
    designation_filter = request.GET.get('designation')
    if designation_filter:
        teachers = teachers.filter(designation=designation_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        teachers = teachers.filter(is_active=True)
    elif status_filter == 'inactive':
        teachers = teachers.filter(is_active=False)
    
    # Sorting
    sort_by = request.GET.get('sort', 'employee_id')
    if sort_by:
        teachers = teachers.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(teachers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    departments = Teacher.objects.values_list('department', flat=True).distinct()
    designations = Teacher.objects.values_list('designation', flat=True).distinct()
    
    # Statistics
    total_teachers = teachers.count()
    active_teachers = teachers.filter(is_active=True).count()
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'designations': designations,
        'search_query': search_query,
        'department_filter': department_filter,
        'designation_filter': designation_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
    }
    
    return render(request, 'teachers/list.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_add(request):
    """Add new teacher"""
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher {teacher.employee_id} added successfully!')
            return redirect('teacher_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherForm()
    
    context = {
        'form': form,
        'title': 'Add New Teacher',
        'button_text': 'Add Teacher'
    }
    
    return render(request, 'teachers/form.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_edit(request, pk):
    """Edit existing teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher {teacher.employee_id} updated successfully!')
            return redirect('teacher_detail', pk=teacher.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherEditForm(instance=teacher)
    
    context = {
        'form': form,
        'teacher': teacher,
        'title': 'Edit Teacher',
        'button_text': 'Update Teacher'
    }
    
    return render(request, 'teachers/form.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_detail(request, pk):
    """View teacher details"""
    teacher = get_object_or_404(
        Teacher.objects.select_related('user').prefetch_related('subjects'),
        pk=pk
    )
    
    # Get assigned subjects
    subjects = teacher.subjects.all()
    
    # Get teaching statistics
    total_students = teacher.total_students
    total_subjects = teacher.total_subjects
    current_workload = teacher.get_current_workload()
    
    # Get marks entered
    marks_entered = SubjectMarks.objects.filter(teacher=teacher).count()
    
    # Get leave records
    leave_records = teacher.leave_applications.all()[:5]
    
    # Get documents
    documents = teacher.documents.all()[:10]
    
    # Get timetable
    timetable = teacher.timetable.all()
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'current_workload': current_workload,
        'marks_entered': marks_entered,
        'leave_records': leave_records,
        'documents': documents,
        'timetable': timetable,
    }
    
    return render(request, 'teachers/detail.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_delete(request, pk):
    """Delete teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        employee_id = teacher.employee_id
        name = teacher.user.get_full_name()
        
        # Delete user (will cascade delete teacher)
        teacher.user.delete()
        
        messages.success(request, f'Teacher {employee_id} - {name} deleted successfully!')
        return redirect('teacher_list')
    
    context = {
        'teacher': teacher
    }
    
    return render(request, 'teachers/confirm_delete.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_toggle_status(request, pk):
    """Toggle teacher active status"""
    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.is_active = not teacher.is_active
    teacher.save()
    
    status = "activated" if teacher.is_active else "deactivated"
    messages.success(request, f'Teacher {teacher.employee_id} {status} successfully!')
    
    return redirect('teacher_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def teacher_assign_subjects(request, pk):
    """Assign subjects to teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        form = SubjectAssignmentForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subjects assigned successfully!')
            return redirect('teacher_detail', pk=pk)
    else:
        form = SubjectAssignmentForm(instance=teacher)
    
    context = {
        'form': form,
        'teacher': teacher,
    }
    
    return render(request, 'teachers/assign_subjects.html', context)


# ============= TEACHER LEAVE MANAGEMENT =============

@login_required
@user_passes_test(is_admin)
def teacher_leave_list(request):
    """List all leave applications"""
    leaves = TeacherLeave.objects.select_related('teacher__user').all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(leaves, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'teachers/leave_list.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_leave_approve(request, pk):
    """Approve leave application"""
    leave = get_object_or_404(TeacherLeave, pk=pk)
    
    if request.method == 'POST':
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approval_date = timezone.now()
        leave.save()
        
        messages.success(request, 'Leave application approved!')
        return redirect('teacher_leave_list')
    
    context = {
        'leave': leave
    }
    
    return render(request, 'teachers/leave_approve.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_leave_reject(request, pk):
    """Reject leave application"""
    leave = get_object_or_404(TeacherLeave, pk=pk)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        leave.status = 'rejected'
        leave.approved_by = request.user
        leave.approval_date = timezone.now()
        leave.rejection_reason = rejection_reason
        leave.save()
        
        messages.success(request, 'Leave application rejected!')
        return redirect('teacher_leave_list')
    
    context = {
        'leave': leave
    }
    
    return render(request, 'teachers/leave_reject.html', context)


# ============= TEACHER DOCUMENT MANAGEMENT =============

@login_required
@user_passes_test(is_admin)
def teacher_documents(request, teacher_id):
    """Manage teacher documents"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    documents = teacher.documents.all()
    
    if request.method == 'POST':
        form = TeacherDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.teacher = teacher
            doc.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('teacher_documents', teacher_id=teacher_id)
    else:
        form = TeacherDocumentForm()
    
    context = {
        'teacher': teacher,
        'documents': documents,
        'form': form,
    }
    
    return render(request, 'teachers/documents.html', context)


@login_required
@user_passes_test(is_admin)
def teacher_document_delete(request, pk):
    """Delete teacher document"""
    document = get_object_or_404(TeacherDocument, pk=pk)
    teacher_id = document.teacher.id
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
    
    return redirect('teacher_documents', teacher_id=teacher_id)


# ============= TEACHER DASHBOARD & PROFILE =============

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    """Teacher dashboard"""
    teacher = request.user.teacher_profile
    
    # Get assigned subjects
    subjects = teacher.subjects.filter(is_active=True)
    
    # Get statistics
    total_students = teacher.total_students
    total_subjects = teacher.total_subjects
    current_workload = teacher.get_current_workload()
    
    # Get marks entry progress
    total_marks_entries = 0
    completed_marks_entries = 0
    
    for subject in subjects:
        students_count = Student.objects.filter(
            program=subject.program,
            current_semester=subject.semester,
            is_active=True
        ).count()
        
        marks_count = SubjectMarks.objects.filter(
            subject=subject,
            teacher=teacher
        ).count()
        
        total_marks_entries += students_count
        completed_marks_entries += marks_count
    
    marks_completion_percentage = 0
    if total_marks_entries > 0:
        marks_completion_percentage = round((completed_marks_entries / total_marks_entries) * 100, 2)
    
    # Get recent leave applications
    recent_leaves = teacher.leave_applications.all()[:5]
    
    # Get today's timetable
    from datetime import datetime
    today = datetime.now().strftime('%A').lower()
    today_schedule = teacher.timetable.filter(day=today).order_by('start_time')
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'current_workload': current_workload,
        'marks_completion_percentage': marks_completion_percentage,
        'recent_leaves': recent_leaves,
        'today_schedule': today_schedule,
    }
    
    return render(request, 'teachers/dashboard.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_profile(request):
    """Teacher profile view"""
    teacher = request.user.teacher_profile
    
    context = {
        'teacher': teacher,
    }
    
    return render(request, 'teachers/profile.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_profile_edit(request):
    """Edit teacher profile (limited fields)"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        # Only allow editing certain fields
        teacher.personal_email = request.POST.get('personal_email', teacher.personal_email)
        teacher.personal_phone = request.POST.get('personal_phone', teacher.personal_phone)
        teacher.address = request.POST.get('address', teacher.address)
        teacher.city = request.POST.get('city', teacher.city)
        teacher.state = request.POST.get('state', teacher.state)
        teacher.pincode = request.POST.get('pincode', teacher.pincode)
        teacher.research_interests = request.POST.get('research_interests', teacher.research_interests)
        teacher.google_scholar_url = request.POST.get('google_scholar_url', teacher.google_scholar_url)
        teacher.linkedin_url = request.POST.get('linkedin_url', teacher.linkedin_url)
        
        # Handle photo upload
        if request.FILES.get('photo'):
            teacher.photo = request.FILES['photo']
        
        teacher.save()
        
        # Update user info
        user = request.user
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('teacher_profile')
    
    context = {
        'teacher': teacher,
    }
    
    return render(request, 'teachers/profile_edit.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_my_subjects(request):
    """View assigned subjects"""
    teacher = request.user.teacher_profile
    subjects = teacher.subjects.filter(is_active=True)
    
    # Get student count for each subject
    subjects_data = []
    for subject in subjects:
        student_count = Student.objects.filter(
            program=subject.program,
            current_semester=subject.semester,
            is_active=True
        ).count()
        
        marks_entered = SubjectMarks.objects.filter(
            subject=subject,
            teacher=teacher
        ).count()
        
        subjects_data.append({
            'subject': subject,
            'student_count': student_count,
            'marks_entered': marks_entered,
            'completion': round((marks_entered / student_count * 100), 2) if student_count > 0 else 0
        })
    
    context = {
        'teacher': teacher,
        'subjects_data': subjects_data,
    }
    
    return render(request, 'teachers/my_subjects.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_my_students(request, subject_id):
    """View students for a subject"""
    teacher = request.user.teacher_profile
    subject = get_object_or_404(Subject, pk=subject_id)
    
    # Verify teacher is assigned to this subject
    if not teacher.subjects.filter(id=subject_id).exists():
        messages.error(request, 'You are not assigned to this subject.')
        return redirect('teacher_my_subjects')
    
    # Get students
    students = Student.objects.filter(
        program=subject.program,
        current_semester=subject.semester,
        is_active=True
    ).select_related('user').order_by('enrollment_number')
    
    context = {
        'teacher': teacher,
        'subject': subject,
        'students': students,
    }
    
    return render(request, 'teachers/my_students.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_leave_apply(request):
    """Apply for leave"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        form = TeacherLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.teacher = teacher
            leave.save()
            messages.success(request, 'Leave application submitted successfully!')
            return redirect('teacher_my_leaves')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherLeaveForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'teachers/leave_apply.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_my_leaves(request):
    """View my leave applications"""
    teacher = request.user.teacher_profile
    leaves = teacher.leave_applications.all()
    
    context = {
        'teacher': teacher,
        'leaves': leaves,
    }
    
    return render(request, 'teachers/my_leaves.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_my_timetable(request):
    """View my timetable"""
    teacher = request.user.teacher_profile
    timetable = teacher.timetable.all()
    
    # Organize by day
    schedule = {}
    for entry in timetable:
        if entry.day not in schedule:
            schedule[entry.day] = []
        schedule[entry.day].append(entry)
    
    context = {
        'teacher': teacher,
        'schedule': schedule,
    }
    
    return render(request, 'teachers/my_timetable.html', context)


# ============= REPORTS & ANALYTICS =============

@login_required
@user_passes_test(is_admin)
def teacher_statistics(request):
    """View teacher statistics and analytics"""
    # Overall statistics
    total_teachers = Teacher.objects.filter(is_active=True).count()
    
    # Department-wise distribution
    department_stats = Teacher.objects.filter(is_active=True).values(
        'department'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Designation-wise distribution
    designation_stats = Teacher.objects.filter(is_active=True).values(
        'designation'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Experience distribution
    teachers = Teacher.objects.filter(is_active=True)
    exp_ranges = {
        '0-5': 0,
        '6-10': 0,
        '11-15': 0,
        '16-20': 0,
        '20+': 0
    }
    
    for teacher in teachers:
        exp = teacher.experience_years
        if exp <= 5:
            exp_ranges['0-5'] += 1
        elif exp <= 10:
            exp_ranges['6-10'] += 1
        elif exp <= 15:
            exp_ranges['11-15'] += 1
        elif exp <= 20:
            exp_ranges['16-20'] += 1
        else:
            exp_ranges['20+'] += 1
    
    # Top performers (based on student feedback or marks completion)
    top_teachers = Teacher.objects.filter(is_active=True)[:10]
    
    context = {
        'total_teachers': total_teachers,
        'department_stats': department_stats,
        'designation_stats': designation_stats,
        'exp_ranges': exp_ranges,
        'top_teachers': top_teachers,
    }
    
    return render(request, 'teachers/statistics.html', context)


# ============= API ENDPOINTS =============

@login_required
def get_teacher_data_api(request, teacher_id):
    """API endpoint to get teacher data"""
    if not (request.user.is_admin or 
            (request.user.is_teacher and request.user.teacher_profile.id == teacher_id)):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    data = {
        'employee_id': teacher.employee_id,
        'name': teacher.get_full_name(),
        'department': teacher.department,
        'designation': teacher.designation,
        'total_subjects': teacher.total_subjects,
        'total_students': teacher.total_students,
        'workload': teacher.get_current_workload(),
    }
    
    return JsonResponse(data)
