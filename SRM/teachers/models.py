from django.db import models
from accounts.models import User
from courses.models import Subject
from django.core.validators import RegexValidator, MinValueValidator


class Teacher(models.Model):
    """Teacher profile model"""
    
    DESIGNATION_CHOICES = (
        ('Professor', 'Professor'),
        ('Associate Professor', 'Associate Professor'),
        ('Assistant Professor', 'Assistant Professor'),
        ('Lecturer', 'Lecturer'),
        ('Guest Faculty', 'Guest Faculty'),
        ('Visiting Faculty', 'Visiting Faculty'),
    )
    
    EMPLOYMENT_TYPE_CHOICES = (
        ('Full Time', 'Full Time'),
        ('Part Time', 'Part Time'),
        ('Contract', 'Contract'),
        ('Guest', 'Guest'),
    )
    
    # User relationship
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='teacher_profile'
    )
    
    # Professional Information
    employee_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text='Unique employee identification number'
    )
    department = models.CharField(max_length=100)
    designation = models.CharField(
        max_length=50, 
        choices=DESIGNATION_CHOICES,
        default='Assistant Professor'
    )
    qualification = models.CharField(
        max_length=200,
        help_text='Highest qualification (e.g., Ph.D. in Computer Science)'
    )
    specialization = models.CharField(
        max_length=200,
        blank=True,
        help_text='Area of specialization'
    )
    
    # Experience
    experience_years = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Total years of teaching experience'
    )
    previous_institution = models.CharField(
        max_length=200, 
        blank=True,
        help_text='Previous institution/company'
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'."
    )
    office_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17,
        blank=True,
        null=True,
        help_text='Office phone extension'
    )
    personal_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17,
        help_text='Personal phone number'
    )
    personal_email = models.EmailField(blank=True, null=True)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Employment Details
    joining_date = models.DateField()
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='Full Time'
    )
    salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Monthly salary'
    )
    
    # Subject Assignment
    subjects = models.ManyToManyField(
        Subject, 
        related_name='teachers', 
        blank=True,
        help_text='Subjects assigned to this teacher'
    )
    
    # Additional Information
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=(
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other'),
        ),
        blank=True
    )
    blood_group = models.CharField(
        max_length=3,
        choices=(
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
        ),
        blank=True,
        null=True
    )
    nationality = models.CharField(max_length=50, default='Indian')
    
    # Documents
    photo = models.ImageField(
        upload_to='teacher_photos/', 
        blank=True, 
        null=True
    )
    resume = models.FileField(
        upload_to='teacher_documents/', 
        blank=True, 
        null=True,
        help_text='CV/Resume'
    )
    id_proof = models.FileField(
        upload_to='teacher_documents/', 
        blank=True, 
        null=True
    )
    
    # Research & Publications
    research_interests = models.TextField(blank=True)
    publications_count = models.IntegerField(default=0)
    google_scholar_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_hod = models.BooleanField(
        default=False,
        help_text='Is Head of Department'
    )
    can_approve_results = models.BooleanField(
        default=False,
        help_text='Can approve/publish results'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teachers'
        ordering = ['department', 'designation', 'user__first_name']
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['department', 'designation']),
        ]
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
    
    def get_full_name(self):
        return self.user.get_full_name()
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def total_subjects(self):
        """Get total number of subjects assigned"""
        return self.subjects.count()
    
    @property
    def total_students(self):
        """Get total number of students taught"""
        from students.models import Student
        student_count = 0
        for subject in self.subjects.all():
            student_count += Student.objects.filter(
                program=subject.program,
                current_semester=subject.semester,
                is_active=True
            ).count()
        return student_count
    
    def get_current_workload(self):
        """Calculate current teaching workload (credits)"""
        return sum(subject.credits for subject in self.subjects.filter(is_active=True))


class TeacherAttendance(models.Model):
    """Track teacher attendance"""
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=(
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('leave', 'On Leave'),
            ('half_day', 'Half Day'),
        ),
        default='present'
    )
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'teacher_attendance'
        unique_together = ['teacher', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.teacher.employee_id} - {self.date} - {self.status}"


class TeacherLeave(models.Model):
    """Teacher leave management"""
    LEAVE_TYPES = (
        ('casual', 'Casual Leave'),
        ('sick', 'Sick Leave'),
        ('earned', 'Earned Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid', 'Unpaid Leave'),
    )
    
    LEAVE_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE, 
        related_name='leave_applications'
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20, 
        choices=LEAVE_STATUS, 
        default='pending'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_leaves'
    )
    approval_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)
    applied_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'teacher_leaves'
        ordering = ['-applied_date']
    
    def __str__(self):
        return f"{self.teacher.employee_id} - {self.leave_type} ({self.start_date} to {self.end_date})"
    
    def save(self, *args, **kwargs):
        # Calculate total days
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)


class TeacherDocument(models.Model):
    """Additional documents for teachers"""
    DOCUMENT_TYPES = (
        ('certificate', 'Certificate'),
        ('degree', 'Degree'),
        ('experience_letter', 'Experience Letter'),
        ('publication', 'Publication'),
        ('award', 'Award'),
        ('other', 'Other'),
    )
    
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=200)
    document_file = models.FileField(upload_to='teacher_documents/')
    uploaded_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'teacher_documents'
        ordering = ['-uploaded_date']
    
    def __str__(self):
        return f"{self.teacher.employee_id} - {self.document_name}"


class TeacherTimeTable(models.Model):
    """Teacher timetable/schedule"""
    DAYS = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    )
    
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE, 
        related_name='timetable'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    day = models.CharField(max_length=20, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=50, blank=True)
    academic_year = models.CharField(max_length=20)
    semester = models.IntegerField()
    
    class Meta:
        db_table = 'teacher_timetable'
        ordering = ['day', 'start_time']
        unique_together = ['teacher', 'day', 'start_time', 'academic_year']
    
    def __str__(self):
        return f"{self.teacher.employee_id} - {self.subject.code} - {self.day} {self.start_time}"