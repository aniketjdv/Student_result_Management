

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from .models import Program, Subject
from .forms import ProgramForm, SubjectForm

def is_admin(user):
    """Check if user is admin"""
    return user.role == 'admin'


# ============= PROGRAM VIEWS =============

@login_required
@user_passes_test(is_admin)
def program_list(request):
    """List all programs with statistics"""
    programs = Program.objects.annotate(
        subject_count=Count('subjects'),
        active_subject_count=Count('subjects', filter=Q(subjects__is_active=True))
    ).order_by('name')
    
    context = {
        'programs': programs,
        'total_programs': programs.count(),
        'active_programs': programs.filter(is_active=True).count(),
    }
    
    return render(request, 'courses/program_list.html', context)


@login_required
@user_passes_test(is_admin)
def program_add(request):
    """Add new program"""
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            messages.success(request, f'Program "{program.name}" added successfully!')
            return redirect('program_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProgramForm()
    
    return render(request, 'courses/program_form.html', {
        'form': form,
        'title': 'Add New Program',
        'button_text': 'Add Program'
    })


@login_required
@user_passes_test(is_admin)
def program_edit(request, pk):
    """Edit existing program"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            program = form.save()
            messages.success(request, f'Program "{program.name}" updated successfully!')
            return redirect('program_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProgramForm(instance=program)
    
    return render(request, 'courses/program_form.html', {
        'form': form,
        'program': program,
        'title': 'Edit Program',
        'button_text': 'Update Program'
    })


@login_required
@user_passes_test(is_admin)
def program_detail(request, pk):
    """View program details with all subjects"""
    program = get_object_or_404(Program, pk=pk)
    
    # Get subjects grouped by semester
    subjects_by_semester = {}
    for sem in range(1, program.total_semesters + 1):
        subjects_by_semester[sem] = program.subjects.filter(
            semester=sem
        ).order_by('code')
    
    # Calculate statistics
    total_subjects = program.subjects.count()
    active_subjects = program.subjects.filter(is_active=True).count()
    total_credits = sum(subject.credits for subject in program.subjects.all())
    
    context = {
        'program': program,
        'subjects_by_semester': subjects_by_semester,
        'total_subjects': total_subjects,
        'active_subjects': active_subjects,
        'total_credits': total_credits,
    }
    
    return render(request, 'courses/program_detail.html', context)


@login_required
@user_passes_test(is_admin)
def program_delete(request, pk):
    """Delete program"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        program_name = program.name
        try:
            program.delete()
            messages.success(request, f'Program "{program_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Cannot delete program: {str(e)}')
        return redirect('program_list')
    
    return render(request, 'courses/program_confirm_delete.html', {
        'program': program
    })


@login_required
@user_passes_test(is_admin)
def program_toggle_status(request, pk):
    """Toggle program active status"""
    program = get_object_or_404(Program, pk=pk)
    program.is_active = not program.is_active
    program.save()
    
    status = "activated" if program.is_active else "deactivated"
    messages.success(request, f'Program "{program.name}" {status} successfully!')
    
    return redirect('program_list')


# ============= SUBJECT VIEWS =============

@login_required
@user_passes_test(is_admin)
def subject_list(request):
    """List all subjects with filtering"""
    subjects = Subject.objects.select_related('program').all()
    
    # Filtering
    program_filter = request.GET.get('program')
    semester_filter = request.GET.get('semester')
    status_filter = request.GET.get('status')
    
    if program_filter:
        subjects = subjects.filter(program_id=program_filter)
    
    if semester_filter:
        subjects = subjects.filter(semester=semester_filter)
    
    if status_filter == 'active':
        subjects = subjects.filter(is_active=True)
    elif status_filter == 'inactive':
        subjects = subjects.filter(is_active=False)
    
    subjects = subjects.order_by('program', 'semester', 'code')
    
    # Get all programs for filter dropdown
    programs = Program.objects.filter(is_active=True).order_by('name')
    
    # Get all semesters (1-8)
    semesters = range(1, 9)
    
    context = {
        'subjects': subjects,
        'programs': programs,
        'semesters': semesters,
        'total_subjects': subjects.count(),
        'active_subjects': subjects.filter(is_active=True).count(),
        'selected_program': program_filter,
        'selected_semester': semester_filter,
        'selected_status': status_filter,
    }
    
    return render(request, 'courses/subject_list.html', context)


@login_required
@user_passes_test(is_admin)
def subject_add(request):
    """Add new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" added successfully!')
            return redirect('subject_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm()
    
    return render(request, 'courses/subject_form.html', {
        'form': form,
        'title': 'Add New Subject',
        'button_text': 'Add Subject'
    })


@login_required
@user_passes_test(is_admin)
def subject_edit(request, pk):
    """Edit existing subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" updated successfully!')
            return redirect('subject_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'courses/subject_form.html', {
        'form': form,
        'subject': subject,
        'title': 'Edit Subject',
        'button_text': 'Update Subject'
    })


@login_required
@user_passes_test(is_admin)
def subject_detail(request, pk):
    """View subject details"""
    subject = get_object_or_404(Subject.objects.select_related('program'), pk=pk)
    
    # Get teachers assigned to this subject
    from teachers.models import Teacher
    assigned_teachers = Teacher.objects.filter(
        subjects=subject,
        is_active=True
    ).select_related('user')
    
    # Get student count for this subject
    from students.models import Student
    student_count = Student.objects.filter(
        program=subject.program,
        current_semester=subject.semester,
        is_active=True
    ).count()
    
    context = {
        'subject': subject,
        'assigned_teachers': assigned_teachers,
        'student_count': student_count,
    }
    
    return render(request, 'courses/subject_detail.html', context)


@login_required
@user_passes_test(is_admin)
def subject_delete(request, pk):
    """Delete subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        subject_name = subject.name
        try:
            subject.delete()
            messages.success(request, f'Subject "{subject_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Cannot delete subject: {str(e)}')
        return redirect('subject_list')
    
    return render(request, 'courses/subject_confirm_delete.html', {
        'subject': subject
    })


@login_required
@user_passes_test(is_admin)
def subject_toggle_status(request, pk):
    """Toggle subject active status"""
    subject = get_object_or_404(Subject, pk=pk)
    subject.is_active = not subject.is_active
    subject.save()
    
    status = "activated" if subject.is_active else "deactivated"
    messages.success(request, f'Subject "{subject.name}" {status} successfully!')
    
    return redirect('subject_list')


@login_required
@user_passes_test(is_admin)
def subject_bulk_add(request, program_id):
    """Add multiple subjects at once for a program"""
    program = get_object_or_404(Program, pk=program_id)
    
    if request.method == 'POST':
        # Get form data
        num_subjects = int(request.POST.get('num_subjects', 0))
        
        subjects_added = 0
        for i in range(num_subjects):
            code = request.POST.get(f'code_{i}')
            name = request.POST.get(f'name_{i}')
            semester = request.POST.get(f'semester_{i}')
            credits = request.POST.get(f'credits_{i}')
            max_marks = request.POST.get(f'max_marks_{i}', 100)
            passing_marks = request.POST.get(f'passing_marks_{i}', 40)
            
            if code and name and semester and credits:
                Subject.objects.create(
                    program=program,
                    code=code,
                    name=name,
                    semester=int(semester),
                    credits=int(credits),
                    max_marks=int(max_marks),
                    passing_marks=int(passing_marks)
                )
                subjects_added += 1
        
        messages.success(request, f'{subjects_added} subjects added successfully!')
        return redirect('program_detail', pk=program_id)
    
    context = {
        'program': program,
        'semesters': range(1, program.total_semesters + 1),
    }
    
    return render(request, 'courses/subject_bulk_add.html', context)


# ============= DASHBOARD VIEW =============

@login_required
@user_passes_test(is_admin)
def courses_dashboard(request):
    """Dashboard showing overview of courses and subjects"""
    from students.models import Student
    
    # Program statistics
    programs = Program.objects.annotate(
        subject_count=Count('subjects'),
        student_count=Count('student')
    ).filter(is_active=True)
    
    # Subject statistics
    total_subjects = Subject.objects.count()
    active_subjects = Subject.objects.filter(is_active=True).count()
    
    # Recent additions
    recent_programs = Program.objects.order_by('-created_at')[:5]
    recent_subjects = Subject.objects.select_related('program').order_by('-id')[:10]
    
    context = {
        'programs': programs,
        'total_programs': programs.count(),
        'total_subjects': total_subjects,
        'active_subjects': active_subjects,
        'recent_programs': recent_programs,
        'recent_subjects': recent_subjects,
    }
    
    return render(request, 'courses/dashboard.html', context)