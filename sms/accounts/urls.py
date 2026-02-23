from django.urls import path
from . import views
from academics.views import edit_batch
urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('faculty-dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/edit/', views.edit_student_profile, name='edit_student_profile'),
    path('faculty-permissions/', views.faculty_permission_list, name='faculty_permission_list'),
    path('faculty-permissions/<int:user_id>/', views.assign_faculty_permissions, name='assign_faculty_permissions'),
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
   
    
    path(
    'admin/students/',
    views.admin_student_management,
    name='admin_student_management'),
    path('admin/students/add/', views.add_student, name='add_student'),
    path(
    'admin/student/<int:student_id>/edit/',
    views.edit_student,
    name='edit_student'),
    path(
    'admin/student/<int:student_id>/delete/',
    views.delete_student,
    name='delete_student'),
    path(
    'admin/faculty/',
    views.admin_faculty_management,
    name='admin_faculty_management'),
    path('admin/faculty/add/', views.add_faculty, name='add_faculty'),
    path(
    'admin/faculty/<int:faculty_id>/edit/',
    views.edit_faculty,
    name='edit_faculty'),
    path(
    'admin/faculty/<int:faculty_id>/delete/',
    views.delete_faculty,
    name='delete_faculty'),
    path(
    'admin/faculty/<int:faculty_id>/assign-course/',
    views.assign_course_to_faculty,
    name='assign_course_to_faculty'),
    path(
    'admin/faculty/course/<int:course_id>/remove/',
    views.remove_course_from_faculty,
    name='remove_course_from_faculty'),
    path('admin/courses/', views.course_management, name='course_management'),
    path('admin/courses/add/', views.add_course, name='add_course'),
    path('admin/course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('admin/course/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path(
    'admin/batch/student/<int:student_id>/remove/',
    views.remove_student_from_batch,
    name='remove_student_from_batch'),
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
    'faculty/quiz/question/<int:question_id>/edit/',
    views.edit_quiz_question,
    name='edit_quiz_question'),
    path(
    'faculty/quiz/question/<int:question_id>/delete/',
    views.delete_quiz_question,
    name='delete_quiz_question'),
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
