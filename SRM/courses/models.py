# Create your models here.
from django.db import models

class Program(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    duration_years = models.IntegerField(default=2)
    total_semesters = models.IntegerField(default=4)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'programs'


class Subject(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='subjects')
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    semester = models.IntegerField()
    credits = models.IntegerField()
    max_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        db_table = 'subjects'
        ordering = ['semester', 'code']