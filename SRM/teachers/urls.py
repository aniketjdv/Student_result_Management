from django.urls import path
from . import views

urlpatterns = [
    # Admin - Teacher Management
    path('list/', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_add, name='teacher_add'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('<int:pk>/toggle-status/', views.teacher_toggle_status, name='teacher_toggle_status'),
    path('<int:pk>/assign-subjects/', views.teacher_assign_subjects, name='teacher_assign_subjects'),
    
    # Leave Management (Admin)
    path('leaves/', views.teacher_leave_list, name='teacher_leave_list'),
    path('leave/<int:pk>/approve/', views.teacher_leave_approve, name='teacher_leave_approve'),
    path('leave/<int:pk>/reject/', views.teacher_leave_reject, name='teacher_leave_reject'),
    
    # Document Management
    path('<int:teacher_id>/documents/', views.teacher_documents, name='teacher_documents'),
    path('document/<int:pk>/delete/', views.teacher_document_delete, name='teacher_document_delete'),
    
    # Teacher Dashboard & Profile
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('profile/', views.teacher_profile, name='teacher_profile'),
    path('profile/edit/', views.teacher_profile_edit, name='teacher_profile_edit'),
    
    # Teacher - My Section
    path('my-subjects/', views.teacher_my_subjects, name='teacher_my_subjects'),
    path('my-students/<int:subject_id>/', views.teacher_my_students, name='teacher_my_students'),
    path('leave/apply/', views.teacher_leave_apply, name='teacher_leave_apply'),
    path('my-leaves/', views.teacher_my_leaves, name='teacher_my_leaves'),
    path('my-timetable/', views.teacher_my_timetable, name='teacher_my_timetable'),
    
    # Reports & Analytics
    path('statistics/', views.teacher_statistics, name='teacher_statistics'),
    
    # API
    path('api/<int:teacher_id>/', views.get_teacher_data_api, name='teacher_data_api'),
]
