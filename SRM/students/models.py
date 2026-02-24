from django.db import models
from accounts.models import User
from courses.models import Program
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator


class Student(models.Model):
    """Student profile model"""
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    # User relationship
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_profile'
    )
    
    # Academic Information
    enrollment_number = models.CharField(
        max_length=20, 
        unique=True,
        help_text='Unique enrollment number'
    )
    program = models.ForeignKey(
        Program, 
        on_delete=models.PROTECT,
        related_name='students'
    )
    batch_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        help_text='Year of admission'
    )
    current_semester = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    # Personal Information
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_group = models.CharField(
        max_length=3, 
        choices=BLOOD_GROUP_CHOICES, 
        blank=True, 
        null=True
    )
    nationality = models.CharField(max_length=50, default='Indian')
    category = models.CharField(
        max_length=20,
        choices=(
            ('General', 'General'),
            ('OBC', 'OBC'),
            ('SC', 'SC'),
            ('ST', 'ST'),
            ('Other', 'Other'),
        ),
        default='General'
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'."
    )
    personal_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17,
        help_text='Student\'s personal phone number'
    )
    personal_email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Guardian Information
    guardian_name = models.CharField(max_length=100)
    guardian_relation = models.CharField(
        max_length=50,
        default='Father',
        choices=(
            ('Father', 'Father'),
            ('Mother', 'Mother'),
            ('Guardian', 'Guardian'),
            ('Other', 'Other'),
        )
    )
    guardian_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17
    )
    guardian_email = models.EmailField(blank=True, null=True)
    guardian_occupation = models.CharField(max_length=100, blank=True)
    
    # Academic Details
    admission_date = models.DateField()
    admission_type = models.CharField(
        max_length=50,
        choices=(
            ('Regular', 'Regular'),
            ('Lateral Entry', 'Lateral Entry'),
            ('Management Quota', 'Management Quota'),
            ('NRI', 'NRI'),
        ),
        default='Regular'
    )
    
    # Previous Education
    previous_institution = models.CharField(max_length=200, blank=True)
    previous_degree = models.CharField(max_length=100, blank=True)
    previous_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    previous_passing_year = models.IntegerField(blank=True, null=True)
    
    # Documents
    photo = models.ImageField(
        upload_to='student_photos/', 
        blank=True, 
        null=True
    )
    id_proof = models.FileField(
        upload_to='student_documents/', 
        blank=True, 
        null=True,
        help_text='Aadhar/Passport/Driving License'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_hostel_resident = models.BooleanField(default=False)
    is_scholarship_holder = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        ordering = ['-batch_year', 'enrollment_number']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['enrollment_number']),
            models.Index(fields=['batch_year', 'program']),
        ]
    
    def __str__(self):
        return f"{self.enrollment_number} - {self.user.get_full_name()}"
    
    def get_full_name(self):
        return self.user.get_full_name()
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def cgpa(self):
        """Get current CGPA"""
        from results.utils import calculate_cgpa
        return calculate_cgpa(self)
    
    @property
    def total_credits_earned(self):
        """Calculate total credits earned"""
        from results.models import SemesterResult
        results = SemesterResult.objects.filter(
            student=self, 
            is_published=True
        )
        return sum(result.credits_earned for result in results)
    
    @property
    def current_semester_sgpa(self):
        """Get current semester SGPA"""
        from results.models import SemesterResult
        try:
            result = SemesterResult.objects.get(
                student=self,
                semester=self.current_semester,
                is_published=True
            )
            return result.sgpa
        except SemesterResult.DoesNotExist:
            return None
    
    def get_attendance_percentage(self):
        """Get overall attendance percentage"""
        from results.models import Attendance
        attendance_records = Attendance.objects.filter(
            student=self,
            semester=self.current_semester
        )
        
        if not attendance_records.exists():
            return 0
        
        total_classes = sum(att.total_classes for att in attendance_records)
        attended_classes = sum(att.attended_classes for att in attendance_records)
        
        if total_classes == 0:
            return 0
        
        return round((attended_classes / total_classes) * 100, 2)


class StudentDocument(models.Model):
    """Additional documents for students"""
    DOCUMENT_TYPES = (
        ('marksheet', 'Marksheet'),
        ('certificate', 'Certificate'),
        ('transfer_certificate', 'Transfer Certificate'),
        ('character_certificate', 'Character Certificate'),
        ('migration_certificate', 'Migration Certificate'),
        ('other', 'Other'),
    )
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=200)
    document_file = models.FileField(upload_to='student_documents/')
    uploaded_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'student_documents'
        ordering = ['-uploaded_date']
    
    def __str__(self):
        return f"{self.student.enrollment_number} - {self.document_name}"


class StudentFee(models.Model):
    """Student fee records"""
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
    )
    
    PAYMENT_MODE = (
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
        ('dd', 'Demand Draft'),
    )
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='fee_records'
    )
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=20)
    fee_type = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS, 
        default='pending'
    )
    payment_date = models.DateField(blank=True, null=True)
    payment_mode = models.CharField(
        max_length=20, 
        choices=PAYMENT_MODE, 
        blank=True, 
        null=True
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'student_fees'
        ordering = ['-academic_year', '-semester']
    
    def __str__(self):
        return f"{self.student.enrollment_number} - {self.fee_type} ({self.academic_year})"
    
    @property
    def balance_amount(self):
        return self.total_amount - self.paid_amount