from django.urls import path
from . import views

urlpatterns = [
    path('student/courses/', views.student_courses, name='student_courses'),
    path('admin/batches/', views.batch_list, name='batch_list'),
    path('admin/batches/create/', views.create_batch, name='create_batch'),
    path('admin/batches/assign/<int:student_id>/', views.assign_batch, name='assign_batch'),
    path('admin/departments/', views.department_list, name='department_list'),
    path('admin/departments/create/', views.create_department, name='create_department'),
    path('admin/departments/<int:pk>/edit/', views.edit_department, name='edit_department'),
    path('admin/departments/<int:pk>/delete/', views.delete_department, name='delete_department'),
]

