from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
import json

from .models import SemesterResult, SubjectMarks, Attendance, ResultPublication
from students.models import Student
from courses.models import Subject, Program
from teachers.models import Teacher
from .forms import MarksEntryForm, AttendanceForm, ResultPublishForm
from .utils import calculate_sgpa, calculate_cgpa, get_student_performance_data, get_class_performance_summary


# Helper functions
def is_admin(user):
    return user.role == 'admin'

def is_teacher(user):
    return user.role == 'teacher'

def is_student(user):
    return user.role == 'student'


# ============= ADMIN VIEWS =============

@login_required
@user_passes_test(is_admin)
def results_dashboard(request):
    """Results management dashboard for admin"""
    # Get statistics
    total_results = SemesterResult.objects.count()
    published_results = SemesterResult.objects.filter(is_published=True).count()
    pending_results = total_results - published_results
    
    # Recent publications
    recent_publications = ResultPublication.objects.all()[:10]
    
    # Get programs for filtering
    programs = Program.objects.filter(is_active=True)
    
    context = {
        'total_results': total_results,
        'published_results': published_results,
        'pending_results': pending_results,
        'recent_publications': recent_publications,
        'programs': programs,
    }
    
    return render(request, 'results/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def publish_results(request):
    """Publish results for a semester"""
    if request.method == 'POST':
        form = ResultPublishForm(request.POST)
        if form.is_valid():
            semester = form.cleaned_data['semester']
            academic_year = form.cleaned_data['academic_year']
            program = form.cleaned_data.get('program')
            
            # Build query
            query = Q(semester=semester, academic_year=academic_year, is_published=False)
            if program:
                query &= Q(student__program=program)
            
            # Get unpublished results
            results = SemesterResult.objects.filter(query)
            
            if not results.exists():
                messages.warning(request, 'No unpublished results found for the selected criteria.')
                return redirect('publish_results')
            
            # Calculate SGPA and publish
            published_count = 0
            for result in results:
                calculate_sgpa(result)
                result.is_published = True
                result.published_date = timezone.now()
                result.save()
                published_count += 1
            
            # Create publication record
            ResultPublication.objects.create(
                semester=semester,
                academic_year=academic_year,
                program=program,
                published_by=request.user,
                total_students=published_count,
                remarks=form.cleaned_data.get('remarks', '')
            )
            
            messages.success(request, f'Successfully published results for {published_count} students!')
            return redirect('results_dashboard')
    else:
        form = ResultPublishForm()
    
    # Get unpublished semester/year combinations
    unpublished = SemesterResult.objects.filter(
        is_published=False
    ).values('semester', 'academic_year', 'student__program__name').annotate(
        count=Count('id')
    ).order_by('semester', 'academic_year')
    
    context = {
        'form': form,
        'unpublished': unpublished,
    }
    
    return render(request, 'results/publish.html', context)


@login_required
@user_passes_test(is_admin)
def unpublish_results(request, semester, academic_year):
    """Unpublish results (for corrections)"""
    if request.method == 'POST':
        results = SemesterResult.objects.filter(
            semester=semester,
            academic_year=academic_year,
            is_published=True
        )
        
        count = results.update(is_published=False, published_date=None)
        messages.success(request, f'Successfully unpublished {count} results.')
    
    return redirect('results_dashboard')


@login_required
@user_passes_test(is_admin)
def result_list(request):
    """List all results with filtering"""
    results = SemesterResult.objects.select_related(
        'student__user', 'student__program'
    ).all()
    
    # Filters
    program_filter = request.GET.get('program')
    semester_filter = request.GET.get('semester')
    academic_year_filter = request.GET.get('academic_year')
    status_filter = request.GET.get('status')
    
    if program_filter:
        results = results.filter(student__program_id=program_filter)
    
    if semester_filter:
        results = results.filter(semester=semester_filter)
    
    if academic_year_filter:
        results = results.filter(academic_year=academic_year_filter)
    
    if status_filter == 'published':
        results = results.filter(is_published=True)
    elif status_filter == 'unpublished':
        results = results.filter(is_published=False)
    
    # Pagination
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    programs = Program.objects.filter(is_active=True)
    academic_years = SemesterResult.objects.values_list(
        'academic_year', flat=True
    ).distinct()
    
    context = {
        'page_obj': page_obj,
        'programs': programs,
        'academic_years': academic_years,
        'program_filter': program_filter,
        'semester_filter': semester_filter,
        'academic_year_filter': academic_year_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'results/result_list.html', context)


@login_required
@user_passes_test(is_admin)
def result_detail(request, pk):
    """View detailed result"""
    result = get_object_or_404(
        SemesterResult.objects.select_related('student__user', 'student__program'),
        pk=pk
    )
    
    subject_marks = result.subject_marks.select_related('subject', 'teacher__user').all()
    
    context = {
        'result': result,
        'subject_marks': subject_marks,
        'cgpa': calculate_cgpa(result.student),
    }
    
    return render(request, 'results/result_detail.html', context)


# ============= TEACHER VIEWS =============

@login_required
@user_passes_test(is_teacher)
def teacher_marks_entry_subjects(request):
    """List subjects assigned to teacher for marks entry"""
    teacher = request.user.teacher_profile
    subjects = teacher.subjects.filter(is_active=True).select_related('program')
    
    context = {
        'subjects': subjects,
    }
    
    return render(request, 'results/teacher_subjects.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_marks_entry(request, subject_id):
    """Enter marks for students in a subject"""
    teacher = request.user.teacher_profile
    subject = get_object_or_404(Subject, pk=subject_id)
    
    # Verify teacher is assigned to this subject
    if not teacher.subjects.filter(id=subject_id).exists():
        messages.error(request, 'You are not assigned to this subject.')
        return redirect('teacher_marks_entry_subjects')
    
    # Get current academic year (you might want to make this dynamic)
    current_academic_year = '2024-25'
    
    # Get students enrolled in this subject's program and semester
    students = Student.objects.filter(
        program=subject.program,
        current_semester=subject.semester,
        is_active=True
    ).select_related('user').order_by('enrollment_number')
    
    if request.method == 'POST':
        success_count = 0
        error_count = 0
        
        for student in students:
            internal_marks = request.POST.get(f'internal_{student.id}')
            external_marks = request.POST.get(f'external_{student.id}')
            remarks = request.POST.get(f'remarks_{student.id}', '')
            
            if internal_marks is not None and external_marks is not None:
                try:
                    internal_marks = int(internal_marks)
                    external_marks = int(external_marks)
                    
                    # Validate marks
                    if internal_marks < 0 or external_marks < 0:
                        error_count += 1
                        continue
                    
                    # Get or create semester result
                    sem_result, created = SemesterResult.objects.get_or_create(
                        student=student,
                        semester=subject.semester,
                        academic_year=current_academic_year
                    )
                    
                    # Create or update subject marks
                    SubjectMarks.objects.update_or_create(
                        semester_result=sem_result,
                        subject=subject,
                        defaults={
                            'teacher': teacher,
                            'internal_marks': internal_marks,
                            'external_marks': external_marks,
                            'remarks': remarks
                        }
                    )
                    
                    success_count += 1
                except (ValueError, Exception) as e:
                    error_count += 1
                    continue
        
        if success_count > 0:
            messages.success(request, f'Successfully saved marks for {success_count} students.')
        if error_count > 0:
            messages.warning(request, f'Failed to save marks for {error_count} students.')
        
        return redirect('teacher_marks_entry', subject_id=subject_id)
    
    # Get existing marks
    marks_data = []
    for student in students:
        sem_result = SemesterResult.objects.filter(
            student=student,
            semester=subject.semester,
            academic_year=current_academic_year
        ).first()
        
        marks = None
        if sem_result:
            marks = SubjectMarks.objects.filter(
                semester_result=sem_result,
                subject=subject
            ).first()
        
        marks_data.append({
            'student': student,
            'marks': marks
        })
    
    context = {
        'subject': subject,
        'marks_data': marks_data,
        'academic_year': current_academic_year,
    }
    
    return render(request, 'results/marks_entry.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_attendance_entry(request, subject_id):
    """Enter attendance for students"""
    teacher = request.user.teacher_profile
    subject = get_object_or_404(Subject, pk=subject_id)
    
    # Verify teacher is assigned to this subject
    if not teacher.subjects.filter(id=subject_id).exists():
        messages.error(request, 'You are not assigned to this subject.')
        return redirect('teacher_marks_entry_subjects')
    
    current_academic_year = '2024-25'
    
    # Get students
    students = Student.objects.filter(
        program=subject.program,
        current_semester=subject.semester,
        is_active=True
    ).select_related('user').order_by('enrollment_number')
    
    if request.method == 'POST':
        success_count = 0
        
        for student in students:
            total_classes = request.POST.get(f'total_{student.id}')
            attended_classes = request.POST.get(f'attended_{student.id}')
            
            if total_classes and attended_classes:
                try:
                    Attendance.objects.update_or_create(
                        student=student,
                        subject=subject,
                        semester=subject.semester,
                        academic_year=current_academic_year,
                        defaults={
                            'total_classes': int(total_classes),
                            'attended_classes': int(attended_classes)
                        }
                    )
                    success_count += 1
                except Exception:
                    continue
        
        messages.success(request, f'Attendance updated for {success_count} students.')
        return redirect('teacher_attendance_entry', subject_id=subject_id)
    
    # Get existing attendance
    attendance_data = []
    for student in students:
        attendance = Attendance.objects.filter(
            student=student,
            subject=subject,
            semester=subject.semester,
            academic_year=current_academic_year
        ).first()
        
        attendance_data.append({
            'student': student,
            'attendance': attendance
        })
    
    context = {
        'subject': subject,
        'attendance_data': attendance_data,
    }
    
    return render(request, 'results/attendance_entry.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_view_results(request, subject_id):
    """View results for a subject"""
    teacher = request.user.teacher_profile
    subject = get_object_or_404(Subject, pk=subject_id)
    
    if not teacher.subjects.filter(id=subject_id).exists():
        messages.error(request, 'You are not assigned to this subject.')
        return redirect('teacher_marks_entry_subjects')
    
    # Get marks for this subject
    marks = SubjectMarks.objects.filter(
        subject=subject,
        teacher=teacher
    ).select_related('semester_result__student__user').order_by(
        '-semester_result__semester', 'semester_result__student__enrollment_number'
    )
    
    # Calculate statistics
    if marks.exists():
        total_students = marks.count()
        passed = marks.filter(is_passed=True).count()
        failed = marks.filter(is_passed=False).count()
        avg_marks = marks.aggregate(Avg('total_marks'))['total_marks__avg'] or 0
    else:
        total_students = passed = failed = avg_marks = 0
    
    context = {
        'subject': subject,
        'marks': marks,
        'stats': {
            'total': total_students,
            'passed': passed,
            'failed': failed,
            'avg_marks': round(avg_marks, 2),
            'pass_percentage': round((passed / total_students * 100), 2) if total_students > 0 else 0
        }
    }
    
    return render(request, 'results/teacher_view_results.html', context)


# ============= STUDENT VIEWS =============

@login_required
@user_passes_test(is_student)
def student_view_results(request):
    """View all results for logged-in student"""
    student = request.user.student_profile
    
    # Get all published semester results
    semester_results = SemesterResult.objects.filter(
        student=student,
        is_published=True
    ).prefetch_related('subject_marks__subject').order_by('semester')
    
    # Calculate CGPA
    cgpa = calculate_cgpa(student)
    
    # Calculate overall statistics
    total_subjects = 0
    passed_subjects = 0
    failed_subjects = 0
    
    for sem_result in semester_results:
        total_subjects += sem_result.total_subjects
        passed_subjects += sem_result.passed_subjects
        failed_subjects += sem_result.failed_subjects
    
    context = {
        'student': student,
        'semester_results': semester_results,
        'cgpa': cgpa,
        'stats': {
            'total_subjects': total_subjects,
            'passed_subjects': passed_subjects,
            'failed_subjects': failed_subjects,
            'total_semesters': semester_results.count()
        }
    }
    
    return render(request, 'results/student_results.html', context)


@login_required
@user_passes_test(is_student)
def student_semester_detail(request, semester):
    """View detailed marks for a specific semester"""
    student = request.user.student_profile
    
    semester_result = get_object_or_404(
        SemesterResult,
        student=student,
        semester=semester,
        is_published=True
    )
    
    subject_marks = semester_result.subject_marks.select_related('subject').all()
    
    context = {
        'student': student,
        'semester_result': semester_result,
        'subject_marks': subject_marks,
        'cgpa': calculate_cgpa(student),
    }
    
    return render(request, 'results/semester_detail.html', context)


@login_required
@user_passes_test(is_student)
def student_performance_analytics(request):
    """View performance analytics with charts"""
    student = request.user.student_profile
    
    # Get comprehensive performance data
    performance_data = get_student_performance_data(student)
    
    context = {
        'student': student,
        'performance_data': json.dumps(performance_data),
    }
    
    return render(request, 'results/performance_analytics.html', context)


@login_required
@user_passes_test(is_student)
def student_attendance_view(request):
    """View attendance records"""
    student = request.user.student_profile
    
    # Get current semester attendance
    attendance_records = Attendance.objects.filter(
        student=student,
        semester=student.current_semester
    ).select_related('subject')
    
    # Calculate overall attendance
    if attendance_records.exists():
        total_classes = sum(att.total_classes for att in attendance_records)
        attended_classes = sum(att.attended_classes for att in attendance_records)
        overall_percentage = round((attended_classes / total_classes * 100), 2) if total_classes > 0 else 0
    else:
        overall_percentage = 0
    
    context = {
        'student': student,
        'attendance_records': attendance_records,
        'overall_percentage': overall_percentage,
    }
    
    return render(request, 'results/student_attendance.html', context)


# ============= API ENDPOINTS =============

@login_required
def get_performance_data_api(request, student_id):
    """API endpoint to get performance data (for AJAX)"""
    if not (request.user.is_admin or 
            (request.user.is_student and request.user.student_profile.id == student_id)):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    student = get_object_or_404(Student, pk=student_id)
    performance_data = get_student_performance_data(student)
    
    return JsonResponse(performance_data)