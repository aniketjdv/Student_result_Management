from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.courses_dashboard, name='courses_dashboard'),
    
    # Program URLs
    path('programs/', views.program_list, name='program_list'),
    path('programs/add/', views.program_add, name='program_add'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
    path('programs/<int:pk>/edit/', views.program_edit, name='program_edit'),
    path('programs/<int:pk>/delete/', views.program_delete, name='program_delete'),
    path('programs/<int:pk>/toggle-status/', views.program_toggle_status, name='program_toggle_status'),
    
    # Subject URLs
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('subjects/<int:pk>/toggle-status/', views.subject_toggle_status, name='subject_toggle_status'),
    path('subjects/bulk-add/<int:program_id>/', views.subject_bulk_add, name='subject_bulk_add'),
]