from django.urls import path
from . import views

urlpatterns = [
    path('student/courses/', views.student_courses, name='student_courses'),
]
