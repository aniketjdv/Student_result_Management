from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import json

from .models import Student, StudentDocument, StudentFee
from .forms import StudentForm, StudentEditForm, StudentDocumentForm, StudentFeeForm
from accounts.models import User
from courses.models import Program
from results.models import SemesterResult
from results.utils import calculate_cgpa


# Helper functions
def is_admin(user):
    return user.role == 'admin'

def is_student(user):
    return user.role == 'student'


# ============= ADMIN VIEWS - STUDENT MANAGEMENT =============

@login_required
@user_passes_test(is_admin)
def student_list(request):
    """List all students with filtering and search"""
    students = Student.objects.select_related('user', 'program').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(enrollment_number__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Filter by program
    program_filter = request.GET.get('program')
    if program_filter:
        students = students.filter(program_id=program_filter)
    
    # Filter by batch year
    batch_filter = request.GET.get('batch')
    if batch_filter:
        students = students.filter(batch_year=batch_filter)
    
    # Filter by semester
    semester_filter = request.GET.get('semester')
    if semester_filter:
        students = students.filter(current_semester=semester_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        students = students.filter(is_active=True)
    elif status_filter == 'inactive':
        students = students.filter(is_active=False)
    
    # Sorting
    sort_by = request.GET.get('sort', 'enrollment_number')
    if sort_by:
        students = students.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    programs = Program.objects.filter(is_active=True)
    batch_years = Student.objects.values_list('batch_year', flat=True).distinct().order_by('-batch_year')
    
    # Statistics
    total_students = students.count()
    active_students = students.filter(is_active=True).count()
    
    context = {
        'page_obj': page_obj,
        'programs': programs,
        'batch_years': batch_years,
        'search_query': search_query,
        'program_filter': program_filter,
        'batch_filter': batch_filter,
        'semester_filter': semester_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'total_students': total_students,
        'active_students': active_students,
    }
    
    return render(request, 'students/list.html', context)


@login_required
@user_passes_test(is_admin)
def student_add(request):
    """Add new student"""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.enrollment_number} added successfully!')
            return redirect('student_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm()
    
    context = {
        'form': form,
        'title': 'Add New Student',
        'button_text': 'Add Student'
    }
    
    return render(request, 'students/form.html', context)


@login_required
@user_passes_test(is_admin)
def student_edit(request, pk):
    """Edit existing student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentEditForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.enrollment_number} updated successfully!')
            return redirect('student_detail', pk=student.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentEditForm(instance=student)
    
    context = {
        'form': form,
        'student': student,
        'title': 'Edit Student',
        'button_text': 'Update Student'
    }
    
    return render(request, 'students/form.html', context)


@login_required
@user_passes_test(is_admin)
def student_detail(request, pk):
    """View student details"""
    student = get_object_or_404(
        Student.objects.select_related('user', 'program'),
        pk=pk
    )
    
    # Get academic records
    semester_results = SemesterResult.objects.filter(
        student=student,
        is_published=True
    ).order_by('semester')
    
    # Get documents
    documents = student.documents.all()[:10]
    
    # Get fee records
    fee_records = student.fee_records.all()[:10]
    
    # Calculate statistics
    cgpa = calculate_cgpa(student)
    attendance_percentage = student.get_attendance_percentage()
    total_credits = student.total_credits_earned
    
    context = {
        'student': student,
        'semester_results': semester_results,
        'documents': documents,
        'fee_records': fee_records,
        'cgpa': cgpa,
        'attendance_percentage': attendance_percentage,
        'total_credits': total_credits,
    }
    
    return render(request, 'students/detail.html', context)


@login_required
@user_passes_test(is_admin)
def student_delete(request, pk):
    """Delete student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        enrollment = student.enrollment_number
        name = student.user.get_full_name()
        
        # Delete user (will cascade delete student)
        student.user.delete()
        
        messages.success(request, f'Student {enrollment} - {name} deleted successfully!')
        return redirect('student_list')
    
    context = {
        'student': student
    }
    
    return render(request, 'students/confirm_delete.html', context)


@login_required
@user_passes_test(is_admin)
def student_toggle_status(request, pk):
    """Toggle student active status"""
    student = get_object_or_404(Student, pk=pk)
    student.is_active = not student.is_active
    student.save()
    
    status = "activated" if student.is_active else "deactivated"
    messages.success(request, f'Student {student.enrollment_number} {status} successfully!')
    
    return redirect('student_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def student_promote(request, pk):
    """Promote student to next semester"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        if student.current_semester < student.program.total_semesters:
            student.current_semester += 1
            student.save()
            messages.success(request, f'Student {student.enrollment_number} promoted to Semester {student.current_semester}!')
        else:
            messages.warning(request, 'Student is already in the final semester!')
        
        return redirect('student_detail', pk=pk)
    
    context = {
        'student': student
    }
    
    return render(request, 'students/confirm_promote.html', context)


@login_required
@user_passes_test(is_admin)
def student_bulk_upload(request):
    """Bulk upload students via CSV"""
    if request.method == 'POST':
        # Handle CSV upload
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file.')
            return redirect('student_bulk_upload')
        
        # Process CSV (simplified version)
        import csv
        from io import TextIOWrapper
        
        try:
            csv_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(csv_data)
            
            success_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    # Create user
                    user = User.objects.create_user(
                        username=row['username'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        password=row.get('password', 'student@123'),
                        role='student'
                    )
                    
                    # Create student
                    Student.objects.create(
                        user=user,
                        enrollment_number=row['enrollment_number'],
                        program_id=row['program_id'],
                        batch_year=row['batch_year'],
                        date_of_birth=row['date_of_birth'],
                        gender=row['gender'],
                        personal_phone=row['phone'],
                        address=row['address'],
                        city=row['city'],
                        state=row['state'],
                        pincode=row['pincode'],
                        guardian_name=row['guardian_name'],
                        guardian_phone=row['guardian_phone'],
                        admission_date=row['admission_date']
                    )
                    
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    continue
            
            messages.success(request, f'Successfully imported {success_count} students. {error_count} errors.')
            return redirect('student_list')
            
        except Exception as e:
            messages.error(request, f'Error processing CSV: {str(e)}')
    
    return render(request, 'students/bulk_upload.html')


# ============= STUDENT DOCUMENT MANAGEMENT =============

@login_required
@user_passes_test(is_admin)
def student_documents(request, student_id):
    """Manage student documents"""
    student = get_object_or_404(Student, pk=student_id)
    documents = student.documents.all()
    
    if request.method == 'POST':
        form = StudentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.student = student
            doc.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('student_documents', student_id=student_id)
    else:
        form = StudentDocumentForm()
    
    context = {
        'student': student,
        'documents': documents,
        'form': form,
    }
    
    return render(request, 'students/documents.html', context)


@login_required
@user_passes_test(is_admin)
def student_document_delete(request, pk):
    """Delete student document"""
    document = get_object_or_404(StudentDocument, pk=pk)
    student_id = document.student.id
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
    
    return redirect('student_documents', student_id=student_id)


# ============= STUDENT FEE MANAGEMENT =============

@login_required
@user_passes_test(is_admin)
def student_fees(request, student_id):
    """Manage student fees"""
    student = get_object_or_404(Student, pk=student_id)
    fee_records = student.fee_records.all()
    
    # Calculate statistics
    total_payable = sum(fee.total_amount for fee in fee_records)
    total_paid = sum(fee.paid_amount for fee in fee_records)
    total_due = total_payable - total_paid
    
    if request.method == 'POST':
        form = StudentFeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.student = student
            fee.save()
            messages.success(request, 'Fee record added successfully!')
            return redirect('student_fees', student_id=student_id)
    else:
        form = StudentFeeForm()
    
    context = {
        'student': student,
        'fee_records': fee_records,
        'form': form,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'total_due': total_due,
    }
    
    return render(request, 'students/fees.html', context)


@login_required
@user_passes_test(is_admin)
def student_fee_payment(request, pk):
    """Record fee payment"""
    fee = get_object_or_404(StudentFee, pk=pk)
    
    if request.method == 'POST':
        paid_amount = float(request.POST.get('paid_amount', 0))
        payment_mode = request.POST.get('payment_mode')
        transaction_id = request.POST.get('transaction_id', '')
        receipt_number = request.POST.get('receipt_number', '')
        
        fee.paid_amount += paid_amount
        fee.payment_date = timezone.now().date()
        fee.payment_mode = payment_mode
        fee.transaction_id = transaction_id
        fee.receipt_number = receipt_number
        
        # Update status
        if fee.paid_amount >= fee.total_amount:
            fee.payment_status = 'paid'
        elif fee.paid_amount > 0:
            fee.payment_status = 'partial'
        
        fee.save()
        
        messages.success(request, 'Payment recorded successfully!')
        return redirect('student_fees', student_id=fee.student.id)
    
    context = {
        'fee': fee
    }
    
    return render(request, 'students/fee_payment.html', context)


# ============= STUDENT DASHBOARD & PROFILE =============

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    """Student dashboard"""
    student = request.user.student_profile
    
    # Get latest semester result
    latest_result = SemesterResult.objects.filter(
        student=student,
        is_published=True
    ).order_by('-semester').first()
    
    # Get attendance
    from results.models import Attendance
    attendance_records = Attendance.objects.filter(
        student=student,
        semester=student.current_semester
    )
    
    overall_attendance = student.get_attendance_percentage()
    
    # Get fee status
    pending_fees = StudentFee.objects.filter(
        student=student,
        payment_status__in=['pending', 'partial', 'overdue']
    ).count()
    
    # Statistics
    cgpa = calculate_cgpa(student)
    total_credits = student.total_credits_earned
    
    context = {
        'student': student,
        'latest_result': latest_result,
        'cgpa': cgpa,
        'current_sgpa': student.current_semester_sgpa,
        'total_credits': total_credits,
        'overall_attendance': overall_attendance,
        'attendance_records': attendance_records,
        'pending_fees': pending_fees,
    }
    
    return render(request, 'students/dashboard.html', context)


@login_required
@user_passes_test(is_student)
def student_profile(request):
    """Student profile view"""
    student = request.user.student_profile
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/profile.html', context)


@login_required
@user_passes_test(is_student)
def student_profile_edit(request):
    """Edit student profile (limited fields)"""
    student = request.user.student_profile
    
    if request.method == 'POST':
        # Only allow editing certain fields
        student.personal_email = request.POST.get('personal_email', student.personal_email)
        student.personal_phone = request.POST.get('personal_phone', student.personal_phone)
        student.address = request.POST.get('address', student.address)
        student.city = request.POST.get('city', student.city)
        student.state = request.POST.get('state', student.state)
        student.pincode = request.POST.get('pincode', student.pincode)
        
        # Handle photo upload
        if request.FILES.get('photo'):
            student.photo = request.FILES['photo']
        
        student.save()
        
        # Update user info
        user = request.user
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('student_profile')
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/profile_edit.html', context)


@login_required
@user_passes_test(is_student)
def student_documents_view(request):
    """View student documents"""
    student = request.user.student_profile
    documents = student.documents.all()
    
    context = {
        'student': student,
        'documents': documents,
    }
    
    return render(request, 'students/my_documents.html', context)


@login_required
@user_passes_test(is_student)
def student_fees_view(request):
    """View student fee records"""
    student = request.user.student_profile
    fee_records = student.fee_records.all()
    
    # Calculate statistics
    total_payable = sum(fee.total_amount for fee in fee_records)
    total_paid = sum(fee.paid_amount for fee in fee_records)
    total_due = total_payable - total_paid
    
    context = {
        'student': student,
        'fee_records': fee_records,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'total_due': total_due,
    }
    
    return render(request, 'students/my_fees.html', context)


# ============= REPORTS & ANALYTICS =============

@login_required
@user_passes_test(is_admin)
def student_statistics(request):
    """View student statistics and analytics"""
    # Overall statistics
    total_students = Student.objects.filter(is_active=True).count()
    
    # Program-wise distribution
    program_stats = Student.objects.filter(is_active=True).values(
        'program__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Batch-wise distribution
    batch_stats = Student.objects.filter(is_active=True).values(
        'batch_year'
    ).annotate(count=Count('id')).order_by('-batch_year')
    
    # Gender distribution
    gender_stats = Student.objects.filter(is_active=True).values(
        'gender'
    ).annotate(count=Count('id'))
    
    # Top performers
    top_students = Student.objects.filter(is_active=True)[:10]
    top_students_data = []
    for student in top_students:
        cgpa = calculate_cgpa(student)
        if cgpa > 0:
            top_students_data.append({
                'student': student,
                'cgpa': cgpa
            })
    
    top_students_data.sort(key=lambda x: x['cgpa'], reverse=True)
    top_students_data = top_students_data[:10]
    
    context = {
        'total_students': total_students,
        'program_stats': program_stats,
        'batch_stats': batch_stats,
        'gender_stats': gender_stats,
        'top_students': top_students_data,
    }
    
    return render(request, 'students/statistics.html', context)


# ============= API ENDPOINTS =============

@login_required
def get_student_data_api(request, student_id):
    """API endpoint to get student data"""
    if not (request.user.is_admin or 
            (request.user.is_student and request.user.student_profile.id == student_id)):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    student = get_object_or_404(Student, pk=student_id)
    
    data = {
        'enrollment_number': student.enrollment_number,
        'name': student.get_full_name(),
        'program': student.program.name,
        'semester': student.current_semester,
        'batch_year': student.batch_year,
        'cgpa': float(calculate_cgpa(student)),
        'attendance': student.get_attendance_percentage(),
    }
    
    return JsonResponse(data)