from django import forms
from django.contrib.auth import get_user_model
from .models import Student, StudentDocument, StudentFee
from courses.models import Program
from datetime import date

User = get_user_model()


class StudentForm(forms.ModelForm):
    """Form for creating new student"""
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
        help_text='Default password for the student'
    )
    
    class Meta:
        model = Student
        fields = [
            'enrollment_number', 'program', 'batch_year', 'current_semester',
            'date_of_birth', 'gender', 'blood_group', 'nationality', 'category',
            'personal_phone', 'personal_email', 'address', 'city', 'state', 'pincode',
            'guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email',
            'guardian_occupation', 'admission_date', 'admission_type',
            'previous_institution', 'previous_degree', 'previous_percentage',
            'previous_passing_year', 'photo', 'is_hostel_resident', 'is_scholarship_holder'
        ]
        widgets = {
            'enrollment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'batch_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_semester': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relation': forms.Select(attrs={'class': 'form-select'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'guardian_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'admission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'admission_type': forms.Select(attrs={'class': 'form-select'}),
            'previous_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'previous_degree': forms.TextInput(attrs={'class': 'form-control'}),
            'previous_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'previous_passing_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_hostel_resident': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_scholarship_holder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['program'].queryset = Program.objects.filter(is_active=True)
        self.fields['batch_year'].initial = date.today().year
    
    def clean_enrollment_number(self):
        enrollment = self.cleaned_data.get('enrollment_number')
        if Student.objects.filter(enrollment_number=enrollment).exists():
            raise forms.ValidationError('This enrollment number already exists.')
        return enrollment
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username already exists.')
        return username
    
    def save(self, commit=True):
        student = super().save(commit=False)
        
        # Create user
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role='student'
        )
        
        student.user = user
        
        if commit:
            student.save()
        
        return student


class StudentEditForm(forms.ModelForm):
    """Form for editing existing student"""
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
        model = Student
        fields = [
            'enrollment_number', 'program', 'batch_year', 'current_semester',
            'date_of_birth', 'gender', 'blood_group', 'nationality', 'category',
            'personal_phone', 'personal_email', 'address', 'city', 'state', 'pincode',
            'guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email',
            'guardian_occupation', 'admission_date', 'admission_type',
            'previous_institution', 'previous_degree', 'previous_percentage',
            'previous_passing_year', 'photo', 'is_active', 'is_hostel_resident',
            'is_scholarship_holder'
        ]
        widgets = {
            'enrollment_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'batch_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_semester': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relation': forms.Select(attrs={'class': 'form-select'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'guardian_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'admission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'admission_type': forms.Select(attrs={'class': 'form-select'}),
            'previous_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'previous_degree': forms.TextInput(attrs={'class': 'form-control'}),
            'previous_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'previous_passing_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_hostel_resident': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_scholarship_holder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        student = super().save(commit=False)
        
        # Update user
        user = student.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        
        if commit:
            student.save()
        
        return student


class StudentDocumentForm(forms.ModelForm):
    """Form for uploading student documents"""
    class Meta:
        model = StudentDocument
        fields = ['document_type', 'document_name', 'document_file', 'remarks']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_name': forms.TextInput(attrs={'class': 'form-control'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StudentFeeForm(forms.ModelForm):
    """Form for creating fee records"""
    class Meta:
        model = StudentFee
        fields = [
            'semester', 'academic_year', 'fee_type', 'total_amount',
            'due_date', 'remarks'
        ]
        widgets = {
            'semester': forms.NumberInput(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2024-25'}),
            'fee_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Tuition Fee'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
