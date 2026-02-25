from django import forms
from django.contrib.auth import get_user_model
from .models import Teacher, TeacherLeave, TeacherDocument
from courses.models import Subject
from datetime import date

User = get_user_model()


class TeacherForm(forms.ModelForm):
    """Form for creating new teacher"""
    # User fields
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='This will be used for login'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Default password for the teacher'
    )
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'department', 'designation', 'qualification',
            'specialization', 'experience_years', 'previous_institution',
            'office_phone', 'personal_phone', 'personal_email',
            'address', 'city', 'state', 'pincode',
            'joining_date', 'employment_type', 'salary',
            'date_of_birth', 'gender', 'blood_group', 'nationality',
            'photo', 'resume', 'research_interests', 'publications_count',
            'google_scholar_url', 'linkedin_url',
            'is_hod', 'can_approve_results'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'previous_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'office_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'research_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publications_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'google_scholar_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_hod': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_approve_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if Teacher.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError('This employee ID already exists.')
        return employee_id
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username already exists.')
        return username
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        # Create user
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role='teacher'
        )
        
        teacher.user = user
        
        if commit:
            teacher.save()
        
        return teacher


class TeacherEditForm(forms.ModelForm):
    """Form for editing existing teacher"""
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'department', 'designation', 'qualification',
            'specialization', 'experience_years', 'previous_institution',
            'office_phone', 'personal_phone', 'personal_email',
            'address', 'city', 'state', 'pincode',
            'joining_date', 'employment_type', 'salary',
            'date_of_birth', 'gender', 'blood_group', 'nationality',
            'photo', 'resume', 'research_interests', 'publications_count',
            'google_scholar_url', 'linkedin_url',
            'is_active', 'is_hod', 'can_approve_results'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'previous_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'office_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'research_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publications_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'google_scholar_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_hod': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_approve_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        # Update user
        user = teacher.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        
        if commit:
            teacher.save()
        
        return teacher


class SubjectAssignmentForm(forms.ModelForm):
    """Form for assigning subjects to teacher"""
    class Meta:
        model = Teacher
        fields = ['subjects']
        widgets = {
            'subjects': forms.CheckboxSelectMultiple()
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subjects'].queryset = Subject.objects.filter(is_active=True).select_related('program')


class TeacherLeaveForm(forms.ModelForm):
    """Form for applying leave"""
    class Meta:
        model = TeacherLeave
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError('End date must be after start date.')
            
            if start_date < date.today():
                raise forms.ValidationError('Start date cannot be in the past.')
        
        return cleaned_data


class TeacherDocumentForm(forms.ModelForm):
    """Form for uploading teacher documents"""
    class Meta:
        model = TeacherDocument
        fields = ['document_type', 'document_name', 'document_file', 'remarks']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_name': forms.TextInput(attrs={'class': 'form-control'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }