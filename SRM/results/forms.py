from django import forms
from .models import SubjectMarks, Attendance, SemesterResult
from courses.models import Program


class MarksEntryForm(forms.ModelForm):
    """Form for entering subject marks"""
    class Meta:
        model = SubjectMarks
        fields = ['internal_marks', 'external_marks', 'remarks']
        widgets = {
            'internal_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Internal marks'
            }),
            'external_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'External marks'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional remarks'
            }),
        }


class AttendanceForm(forms.ModelForm):
    """Form for entering attendance"""
    class Meta:
        model = Attendance
        fields = ['total_classes', 'attended_classes']
        widgets = {
            'total_classes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Total classes'
            }),
            'attended_classes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Attended classes'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_classes')
        attended = cleaned_data.get('attended_classes')
        
        if total and attended and attended > total:
            raise forms.ValidationError('Attended classes cannot exceed total classes.')
        
        return cleaned_data


class ResultPublishForm(forms.Form):
    """Form for publishing results"""
    semester = forms.IntegerField(
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Semester number'
        })
    )
    academic_year = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2024-25'
        })
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(is_active=True),
        required=False,
        empty_label='All Programs',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional remarks about this publication'
        })
    )