from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Teacher
from students.models import Student
from results.models import SemesterResult, SubjectMarks
from courses.models import Subject

def is_teacher(user):
    return user.role == 'teacher'


@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    teacher = request.user.teacher_profile
    
    # Get assigned subjects
    subjects = teacher.subjects.all()
    
    # Count students
    total_students = Student.objects.filter(is_active=True).count()
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'total_students': total_students,
    }
    
    return render(request, 'teachers/dashboard.html', context)


@login_required
@user_passes_test(is_teacher)
def marks_entry_subject_list(request):
    teacher = request.user.teacher_profile
    subjects = teacher.subjects.all()
    
    return render(request, 'teachers/subject_list.html', {
        'subjects': subjects
    })


@login_required
@user_passes_test(is_teacher)
def marks_entry(request, subject_id):
    teacher = request.user.teacher_profile
    subject = get_object_or_404(Subject, pk=subject_id)
    
    # Get students enrolled in this subject's program
    students = Student.objects.filter(
        program=subject.program,
        current_semester=subject.semester,
        is_active=True
    )
    
    if request.method == 'POST':
        for student in students:
            internal_marks = request.POST.get(f'internal_{student.id}', 0)
            external_marks = request.POST.get(f'external_{student.id}', 0)
            
            # Get or create semester result
            sem_result, created = SemesterResult.objects.get_or_create(
                student=student,
                semester=subject.semester,
                academic_year='2024-25'  # Set dynamically
            )
            
            # Create or update subject marks
            SubjectMarks.objects.update_or_create(
                semester_result=sem_result,
                subject=subject,
                defaults={
                    'teacher': teacher,
                    'internal_marks': int(internal_marks),
                    'external_marks': int(external_marks)
                }
            )
        
        messages.success(request, 'Marks entered successfully')
        return redirect('marks_entry_subject_list')
    
    # Get existing marks
    marks_data = []
    for student in students:
        sem_result = SemesterResult.objects.filter(
            student=student,
            semester=subject.semester
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
    
    return render(request, 'teachers/marks_entry.html', {
        'subject': subject,
        'marks_data': marks_data
    })