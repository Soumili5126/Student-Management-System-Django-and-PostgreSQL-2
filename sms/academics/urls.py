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
    path('faculty/timetable/', views.faculty_timetable, name='faculty_timetable'),
    path('admin/timetable/', views.admin_timetable, name='admin_timetable'),
    path('admin/timetable/<int:pk>/edit/', views.edit_timetable, name='edit_timetable'),
    path('admin/timetable/<int:pk>/delete/', views.delete_timetable, name='delete_timetable'),
    path(
    'admin/course/<int:course_id>/attendance/',
    views.admin_attendance_management,
    name='admin_attendance_management'),
    path('admin/exams/', views.admin_exam_list, name='admin_exam_list'),
    path('admin/exams/add/', views.add_exam, name='add_exam'),
    path('admin/exams/<int:exam_id>/edit/', views.edit_exam, name='edit_exam'),
    path('admin/exams/<int:exam_id>/delete/', views.delete_exam, name='delete_exam'),
    path(
    'admin/exam/<int:exam_id>/grades/',
    views.admin_manage_grades,
    name='admin_manage_grades'),




]

