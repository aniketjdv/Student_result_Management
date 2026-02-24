from django.db import models
from students.models import Student
from courses.models import Subject
from teachers.models import Teacher
from django.core.validators import MinValueValidator, MaxValueValidator


class SemesterResult(models.Model):
    """Store semester-wise results for students"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_results')
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    total_credits = models.IntegerField(default=0)
    credits_earned = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    academic_year = models.CharField(max_length=20)  # e.g., "2023-24"
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'semester_results'
        unique_together = ['student', 'semester', 'academic_year']
        ordering = ['student', 'semester']
        verbose_name = 'Semester Result'
        verbose_name_plural = 'Semester Results'
    
    def __str__(self):
        return f"{self.student.enrollment_number} - Semester {self.semester} ({self.academic_year})"
    
    @property
    def total_subjects(self):
        return self.subject_marks.count()
    
    @property
    def passed_subjects(self):
        return self.subject_marks.filter(is_passed=True).count()
    
    @property
    def failed_subjects(self):
        return self.subject_marks.filter(is_passed=False).count()
    
    @property
    def percentage(self):
        marks = self.subject_marks.all()
        if not marks.exists():
            return 0
        
        total_max = sum(mark.subject.max_marks for mark in marks)
        total_obtained = sum(mark.total_marks for mark in marks)
        
        if total_max == 0:
            return 0
        
        return round((total_obtained / total_max) * 100, 2)


class SubjectMarks(models.Model):
    """Store subject-wise marks"""
    GRADE_CHOICES = (
        ('O', 'O (Outstanding)'),
        ('A+', 'A+ (Excellent)'),
        ('A', 'A (Very Good)'),
        ('B+', 'B+ (Good)'),
        ('B', 'B (Above Average)'),
        ('C', 'C (Average)'),
        ('P', 'P (Pass)'),
        ('F', 'F (Fail)'),
    )
    
    semester_result = models.ForeignKey(SemesterResult, on_delete=models.CASCADE, related_name='subject_marks')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Marks breakdown
    internal_marks = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    external_marks = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_marks = models.IntegerField(default=0)
    
    # Grade and performance
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    is_passed = models.BooleanField(default=False)
    
    # Additional info
    remarks = models.TextField(blank=True)
    entry_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subject_marks'
        unique_together = ['semester_result', 'subject']
        ordering = ['semester_result', 'subject__code']
        verbose_name = 'Subject Mark'
        verbose_name_plural = 'Subject Marks'
    
    def __str__(self):
        return f"{self.semester_result.student.enrollment_number} - {self.subject.code}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate total marks, grade, and pass status"""
        self.total_marks = self.internal_marks + self.external_marks
        self.grade, self.grade_point = self.calculate_grade()
        self.is_passed = self.total_marks >= self.subject.passing_marks
        super().save(*args, **kwargs)
    
    def calculate_grade(self):
        """Calculate grade and grade point based on percentage"""
        if self.subject.max_marks == 0:
            return 'F', 0.0
        
        percentage = (self.total_marks / self.subject.max_marks) * 100
        
        if percentage >= 90:
            return 'O', 10.0
        elif percentage >= 80:
            return 'A+', 9.0
        elif percentage >= 70:
            return 'A', 8.0
        elif percentage >= 60:
            return 'B+', 7.0
        elif percentage >= 50:
            return 'B', 6.0
        elif percentage >= 45:
            return 'C', 5.0
        elif percentage >= 40:
            return 'P', 4.0
        else:
            return 'F', 0.0
    
    @property
    def percentage(self):
        """Calculate percentage for this subject"""
        if self.subject.max_marks == 0:
            return 0
        return round((self.total_marks / self.subject.max_marks) * 100, 2)


class Attendance(models.Model):
    """Track student attendance"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    academic_year = models.CharField(max_length=20)
    total_classes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    attended_classes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['student', 'subject', 'semester', 'academic_year']
        ordering = ['student', 'subject']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.student.enrollment_number} - {self.subject.code} ({self.percentage}%)"
    
    def save(self, *args, **kwargs):
        """Auto-calculate attendance percentage"""
        if self.total_classes > 0:
            self.percentage = round((self.attended_classes / self.total_classes) * 100, 2)
        else:
            self.percentage = 0
        super().save(*args, **kwargs)
    
    @property
    def status(self):
        """Return attendance status"""
        if self.percentage >= 75:
            return 'Good'
        elif self.percentage >= 60:
            return 'Average'
        else:
            return 'Poor'


class ResultPublication(models.Model):
    """Track result publication history"""
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=20)
    program = models.ForeignKey('courses.Program', on_delete=models.CASCADE, null=True, blank=True)
    published_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    published_date = models.DateTimeField(auto_now_add=True)
    total_students = models.IntegerField(default=0)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'result_publications'
        ordering = ['-published_date']
        verbose_name = 'Result Publication'
        verbose_name_plural = 'Result Publications'
    
    def __str__(self):
        return f"Semester {self.semester} - {self.academic_year}"