from django.urls import path
from . import views

urlpatterns = [
    # Admin - Student Management
    path('list/', views.student_list, name='student_list'),
    path('add/', views.student_add, name='student_add'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('<int:pk>/toggle-status/', views.student_toggle_status, name='student_toggle_status'),
    path('<int:pk>/promote/', views.student_promote, name='student_promote'),
    path('bulk-upload/', views.student_bulk_upload, name='student_bulk_upload'),
    
    # Document Management
    path('<int:student_id>/documents/', views.student_documents, name='student_documents'),
    path('document/<int:pk>/delete/', views.student_document_delete, name='student_document_delete'),
    
    # Fee Management
    path('<int:student_id>/fees/', views.student_fees, name='student_fees'),
    path('fee/<int:pk>/payment/', views.student_fee_payment, name='student_fee_payment'),
    
    # Student Dashboard & Profile
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('profile/edit/', views.student_profile_edit, name='student_profile_edit'),
    path('my-documents/', views.student_documents_view, name='student_documents_view'),
    path('my-fees/', views.student_fees_view, name='student_fees_view'),
    
    # Reports & Analytics
    path('statistics/', views.student_statistics, name='student_statistics'),
    
    # API
    path('api/<int:student_id>/', views.get_student_data_api, name='student_data_api'),
]