from django.urls import path
from . import views

urlpatterns = [
    # Admin URLs
    path('dashboard/', views.results_dashboard, name='results_dashboard'),
    path('publish/', views.publish_results, name='publish_results'),
    path('unpublish/<int:semester>/<str:academic_year>/', views.unpublish_results, name='unpublish_results'),
    path('list/', views.result_list, name='result_list'),
    path('detail/<int:pk>/', views.result_detail, name='result_detail'),
    
    # Teacher URLs
    path('teacher/subjects/', views.teacher_marks_entry_subjects, name='teacher_marks_entry_subjects'),
    path('teacher/marks-entry/<int:subject_id>/', views.teacher_marks_entry, name='teacher_marks_entry'),
    path('teacher/attendance/<int:subject_id>/', views.teacher_attendance_entry, name='teacher_attendance_entry'),
    path('teacher/view-results/<int:subject_id>/', views.teacher_view_results, name='teacher_view_results'),
    
    # Student URLs
    path('student/results/', views.student_view_results, name='student_results'),
    path('student/semester/<int:semester>/', views.student_semester_detail, name='student_semester_detail'),
    path('student/performance/', views.student_performance_analytics, name='student_performance'),
    path('student/attendance/', views.student_attendance_view, name='student_attendance'),
    
    # API
    path('api/performance/<int:student_id>/', views.get_performance_data_api, name='performance_data_api'),
]