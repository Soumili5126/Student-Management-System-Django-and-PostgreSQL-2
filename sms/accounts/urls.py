from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('faculty-dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path(
    'faculty/attendance/<int:course_id>/',
    views.mark_attendance,
    name='mark_attendance'),
    path(
    'admin/assign-faculty/<int:course_id>/',
    views.assign_faculty,
    name='assign_faculty'),
    path(
    'admin/enroll-students/<int:course_id>/',
    views.enroll_students,
    name='enroll_students'),
    path(
    'admin/enrollment/edit/<int:enrollment_id>/',
    views.edit_enrollment,
    name='edit_enrollment'),
    path(
    'admin/enrollment/delete/<int:enrollment_id>/',
    views.delete_enrollment,
    name='delete_enrollment'),
    path(
    'faculty/course/<int:course_id>/attendance/export/',
    views.export_attendance_csv,
    name='export_attendance'),
    path(
    'admin/student/<int:student_id>/assign-batch/',
    views.assign_batch,
    name='assign_batch'),
    path('admin/batches/create/', views.create_batch, name='create_batch'),
    path('admin/batches/assign/', views.assign_batch, name='assign_batch'),
    path(
    'faculty/course/<int:course_id>/exam/create/',
    views.create_exam,
    name='create_exam'),
    path(
    'faculty/exam/<int:exam_id>/grades/',
    views.enter_grades,
    name='enter_grades'),
    path(
    'student/exam-results/pdf/',
    views.export_exam_results_pdf,
    name='export_exam_results_pdf'),
    path(
    'faculty/course/<int:course_id>/quiz/create/',
    views.create_quiz,
    name='create_quiz'),
    path(
    'faculty/quiz/<int:quiz_id>/add-question/',
    views.add_quiz_question,
    name='add_quiz_question'),
    path(
    'student/quiz/<int:quiz_id>/attempt/',
    views.attempt_quiz,
    name='attempt_quiz'),
    path('student/quiz/attempt/<int:attempt_id>/result/',
    views.quiz_result,
    name='quiz_result'),
    path(
    'faculty/quiz/<int:quiz_id>/analytics/',
    views.faculty_quiz_analytics,
    name='faculty_quiz_analytics'),



]
