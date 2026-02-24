from django import forms
from .models import Program, Subject

class ProgramForm(forms.ModelForm):
    """Form for creating and editing programs"""
    
    class Meta:
        model = Program
        fields = ['name', 'duration_years', 'total_semesters', 'description', 'is_active']
        widgets = {
            'name': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'duration_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'required': True
            }),
            'total_semesters': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter program description...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Program Name',
            'duration_years': 'Duration (Years)',
            'total_semesters': 'Total Semesters',
            'description': 'Description',
            'is_active': 'Active',
        }
    
    def clean_total_semesters(self):
        """Validate that total semesters matches duration"""
        duration_years = self.cleaned_data.get('duration_years')
        total_semesters = self.cleaned_data.get('total_semesters')
        
        if duration_years and total_semesters:
            if total_semesters != duration_years * 2:
                raise forms.ValidationError(
                    f'Total semesters should be {duration_years * 2} for {duration_years} year(s) program.'
                )
        
        return total_semesters


class SubjectForm(forms.ModelForm):
    """Form for creating and editing subjects"""
    
    class Meta:
        model = Subject
        fields = [
            'program', 'code', 'name', 'semester', 'credits',
            'max_marks', 'passing_marks', 'is_active'
        ]
        widgets = {
            'program': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CS501',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Advanced Database Management',
                'required': True
            }),
            'semester': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'required': True
            }),
            'credits': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'required': True
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 100,
                'required': True
            }),
            'passing_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 40,
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'program': 'Program',
            'code': 'Subject Code',
            'name': 'Subject Name',
            'semester': 'Semester',
            'credits': 'Credits',
            'max_marks': 'Maximum Marks',
            'passing_marks': 'Passing Marks',
            'is_active': 'Active',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active programs in dropdown
        self.fields['program'].queryset = Program.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        program = cleaned_data.get('program')
        semester = cleaned_data.get('semester')
        max_marks = cleaned_data.get('max_marks')
        passing_marks = cleaned_data.get('passing_marks')
        
        # Validate semester is within program's total semesters
        if program and semester:
            if semester > program.total_semesters:
                raise forms.ValidationError(
                    f'Semester cannot exceed {program.total_semesters} for {program.name} program.'
                )
        
        # Validate passing marks is less than max marks
        if max_marks and passing_marks:
            if passing_marks >= max_marks:
                raise forms.ValidationError(
                    'Passing marks must be less than maximum marks.'
                )
        
        return cleaned_data
    
    def clean_code(self):
        """Ensure subject code is unique"""
        code = self.cleaned_data.get('code')
        
        if code:
            code = code.upper()  # Convert to uppercase
            
            # Check if code already exists (excluding current instance if editing)
            qs = Subject.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError('Subject with this code already exists.')
        
        return code