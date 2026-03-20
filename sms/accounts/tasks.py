from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from accounts.models import User, StudentProfile
from academics.models import Attendance, Grade, QuizAttempt, Enrollment, Timetable


@shared_task
def send_exam_scheduled_email(student_user_id, course_code, course_name, exam_title, exam_date, total_marks):
    user = User.objects.get(id=student_user_id)

    subject = f"Exam Scheduled: {exam_title}"

    html_content = render_to_string(
        "emails/exam_scheduled_email.html",
        {
            "user": user,
            "course_code": course_code,
            "course_name": course_name,
            "exam_title": exam_title,
            "exam_date": exam_date,
            "total_marks": total_marks,
            "year": timezone.now().year,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    print(f"Sending exam email to {user.email}")
    email.send()
    print(f"Exam email sent to {user.email}")
    

@shared_task
def send_marks_uploaded_email(student_user_id, exam_title, course_code, course_name, marks_obtained, total_marks):
    user = User.objects.get(id=student_user_id)

    subject = f"Marks Uploaded: {exam_title}"

    html_content = render_to_string(
        "emails/marks_uploaded_email.html",
        {
            "user": user,
            "exam_title": exam_title,
            "course_code": course_code,
            "course_name": course_name,
            "marks_obtained": marks_obtained,
            "total_marks": total_marks,
            "year": timezone.now().year,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


@shared_task
def send_marks_updated_email(student_user_id, exam_title, course_code, course_name, old_marks, new_marks, total_marks):
    user = User.objects.get(id=student_user_id)

    subject = f"Marks Updated: {exam_title}"

    html_content = render_to_string(
        "emails/marks_updated_email.html",
        {
            "user": user,
            "exam_title": exam_title,
            "course_code": course_code,
            "course_name": course_name,
            "old_marks": old_marks,
            "new_marks": new_marks,
            "total_marks": total_marks,
            "year": timezone.now().year,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


@shared_task
def send_quiz_created_email(student_user_id, quiz_title, course_code, course_name, description):
    user = User.objects.get(id=student_user_id)

    subject = f"New Quiz Available: {quiz_title}"

    html_content = render_to_string(
        "emails/quiz_created_email.html",
        {
            "user": user,
            "quiz_title": quiz_title,
            "course_code": course_code,
            "course_name": course_name,
            "description": description,
            "year": timezone.now().year,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

@shared_task
def send_weekly_student_summary():
    students = StudentProfile.objects.select_related("user").all()

    for student in students:
        user = student.user

        if not user.email:
            continue

        enrollments = Enrollment.objects.filter(student=student)
        grades = Grade.objects.filter(student=student).select_related("exam", "exam__course")
        quiz_attempts = QuizAttempt.objects.filter(student=student).select_related("quiz", "quiz__course")
        attendance_records = Attendance.objects.filter(student=student).select_related("course")

        # Attendance summary
        attendance_summary = []
        for enrollment in enrollments:
            total = attendance_records.filter(course=enrollment.course).count()
            present = attendance_records.filter(course=enrollment.course, status='present').count()
            percentage = round((present / total) * 100, 2) if total > 0 else 0
            attendance_summary.append({
                "course": enrollment.course,
                "total_classes": total,
                "present_classes": present,
                "percentage": percentage,
            })

        # Exam summary
        exam_summary = []
        for grade in grades:
            exam_summary.append({
                "course": grade.exam.course,
                "exam_title": grade.exam.title,
                "marks": grade.marks_obtained,
                "total_marks": grade.exam.total_marks,
                "percentage": grade.percentage,
                "grade_letter": grade.grade_letter,
                "is_pass": grade.is_pass,
            })

        # Quiz summary
        quiz_summary = []
        for attempt in quiz_attempts:
            quiz_summary.append({
                "course": attempt.quiz.course,
                "quiz_title": attempt.quiz.title,
                "score": attempt.score,
                "total_questions": attempt.total_questions,
                "percentage": attempt.percentage,
                "attempted_at": attempt.attempted_at,
            })

        subject = "Weekly Academic Summary"

        html_content = render_to_string(
            "emails/weekly_student_summary.html",
            {
                "user": user,
                "student": student,
                "attendance_summary": attendance_summary,
                "exam_summary": exam_summary,
                "quiz_summary": quiz_summary,
                "year": timezone.now().year,
            }
        )
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        print(f"Sending weekly summary to {user.email}")
        email.send()
        print(f"Weekly summary sent to {user.email}")

@shared_task
def send_enrollment_confirmed_email(student_user_id, course_code, course_name):
    user = User.objects.get(id=student_user_id)

    subject = f"Enrollment Confirmed: {course_code}"

    html_content = render_to_string(
        "emails/enrollment_confirmed_email.html",
        {
            "user": user,
            "course_code": course_code,
            "course_name": course_name,
            "year": timezone.now().year,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    print(f"Sending enrollment email to {user.email}")
    email.send()
    print(f"Enrollment email sent to {user.email}")


@shared_task
def send_timetable_created_email(student_user_id, batch_name, course_code, course_name, day, start_time, end_time):
    user = User.objects.get(id=student_user_id)

    subject = f"Timetable Created: {course_code}"

    html_content = render_to_string(
        "emails/timetable_created_email.html",
        {
            "user": user,
            "batch_name": batch_name,
            "course_code": course_code,
            "course_name": course_name,
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "year": timezone.now().year,
        }
    )
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    print(f"Sending timetable email to {user.email}")
    email.send()
    print(f"Timetable email sent to {user.email}")

