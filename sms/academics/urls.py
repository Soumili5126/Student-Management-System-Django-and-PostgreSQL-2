from django.urls import path
from . import views

urlpatterns = [
    path('student/courses/', views.student_courses, name='student_courses'),
    path('admin/batches/', views.batch_list, name='batch_list'),
    path('admin/batches/create/', views.create_batch, name='create_batch'),
    path('admin/batches/assign/<int:student_id>/', views.assign_batch, name='assign_batch'),
]
