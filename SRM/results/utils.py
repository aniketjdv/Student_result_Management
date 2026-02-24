from decimal import Decimal
from django.db.models import Sum, Avg, Count, Q
from .models import SemesterResult, SubjectMarks, Attendance


def calculate_sgpa(semester_result):
    """
    Calculate SGPA (Semester Grade Point Average) for a semester
    Formula: SGPA = Σ(Grade Point × Credits) / Σ(Credits)
    """
    subject_marks = semester_result.subject_marks.all()
    
    if not subject_marks.exists():
        return Decimal('0.00')
    
    total_credits = 0
    total_grade_points = Decimal('0.00')
    
    for mark in subject_marks:
        credits = mark.subject.credits
        total_credits += credits
        total_grade_points += Decimal(str(mark.grade_point)) * credits
    
    if total_credits == 0:
        return Decimal('0.00')
    
    sgpa = total_grade_points / total_credits
    
    # Update semester result
    semester_result.total_credits = total_credits
    semester_result.credits_earned = sum(
        mark.subject.credits for mark in subject_marks if mark.is_passed
    )
    semester_result.sgpa = round(sgpa, 2)
    semester_result.save()
    
    return round(sgpa, 2)


def calculate_cgpa(student):
    """
    Calculate CGPA (Cumulative Grade Point Average) for a student
    Formula: CGPA = Σ(Grade Point × Credits) across all semesters / Σ(Credits)
    """
    semester_results = SemesterResult.objects.filter(
        student=student,
        is_published=True
    )
    
    if not semester_results.exists():
        return Decimal('0.00')
    
    total_credits = 0
    total_grade_points = Decimal('0.00')
    
    for sem_result in semester_results:
        for mark in sem_result.subject_marks.all():
            credits = mark.subject.credits
            total_credits += credits
            total_grade_points += Decimal(str(mark.grade_point)) * credits
    
    if total_credits == 0:
        return Decimal('0.00')
    
    cgpa = total_grade_points / total_credits
    return round(cgpa, 2)


def get_student_performance_data(student):
    """
    Get comprehensive performance data for charts and analytics
    """
    from results.models import SemesterResult, Attendance
    
    # Semester-wise SGPA data
    semester_results = SemesterResult.objects.filter(
        student=student,
        is_published=True
    ).order_by('semester')
    
    sgpa_data = [
        {
            'semester': f'Sem {sr.semester}',
            'sgpa': float(sr.sgpa) if sr.sgpa else 0,
            'percentage': float(sr.percentage)
        }
        for sr in semester_results
    ]
    
    # Subject-wise performance (current semester)
    current_sem_result = semester_results.filter(
        semester=student.current_semester
    ).first()
    
    subject_performance = []
    if current_sem_result:
        for mark in current_sem_result.subject_marks.all():
            subject_performance.append({
                'subject': mark.subject.code,
                'subject_name': mark.subject.name,
                'marks': mark.total_marks,
                'max_marks': mark.subject.max_marks,
                'percentage': mark.percentage,
                'grade': mark.grade,
                'grade_point': float(mark.grade_point)
            })
    
    # Attendance data
    attendance_records = Attendance.objects.filter(
        student=student,
        semester=student.current_semester
    )
    
    attendance_data = [
        {
            'subject': att.subject.code,
            'subject_name': att.subject.name,
            'percentage': float(att.percentage),
            'attended': att.attended_classes,
            'total': att.total_classes,
            'status': att.status
        }
        for att in attendance_records
    ]
    
    # Grade distribution across all semesters
    from django.db.models import Count
    
    grade_distribution = SubjectMarks.objects.filter(
        semester_result__student=student,
        semester_result__is_published=True
    ).values('grade').annotate(count=Count('grade')).order_by('grade')
    
    # Performance summary
    cgpa = calculate_cgpa(student)
    total_subjects = SubjectMarks.objects.filter(
        semester_result__student=student,
        semester_result__is_published=True
    ).count()
    
    passed_subjects = SubjectMarks.objects.filter(
        semester_result__student=student,
        semester_result__is_published=True,
        is_passed=True
    ).count()
    
    failed_subjects = total_subjects - passed_subjects
    
    return {
        'sgpa_data': sgpa_data,
        'subject_performance': subject_performance,
        'attendance_data': attendance_data,
        'grade_distribution': list(grade_distribution),
        'cgpa': float(cgpa),
        'summary': {
            'total_subjects': total_subjects,
            'passed_subjects': passed_subjects,
            'failed_subjects': failed_subjects,
            'pass_percentage': round((passed_subjects / total_subjects * 100), 2) if total_subjects > 0 else 0
        }
    }


def get_class_performance_summary(program, semester, academic_year):
    """
    Get class performance summary for teachers/admin
    """
    semester_results = SemesterResult.objects.filter(
        student__program=program,
        semester=semester,
        academic_year=academic_year,
        is_published=True
    )
    
    if not semester_results.exists():
        return None
    
    total_students = semester_results.count()
    
    # Calculate average SGPA
    avg_sgpa = semester_results.aggregate(Avg('sgpa'))['sgpa__avg'] or 0
    
    # Pass/Fail statistics
    passed_students = semester_results.filter(
        subject_marks__is_passed=True
    ).distinct().count()
    
    # Top performers
    top_performers = semester_results.order_by('-sgpa')[:5]
    
    return {
        'total_students': total_students,
        'avg_sgpa': round(avg_sgpa, 2),
        'passed_students': passed_students,
        'failed_students': total_students - passed_students,
        'pass_percentage': round((passed_students / total_students * 100), 2) if total_students > 0 else 0,
        'top_performers': [
            {
                'name': sr.student.user.get_full_name(),
                'enrollment': sr.student.enrollment_number,
                'sgpa': float(sr.sgpa)
            }
            for sr in top_performers
        ]
    }