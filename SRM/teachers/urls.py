from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('marks-entry/', views.marks_entry_subject_list, name='marks_entry_subject_list'),
    path('marks-entry/<int:subject_id>/', views.marks_entry, name='marks_entry'),
]