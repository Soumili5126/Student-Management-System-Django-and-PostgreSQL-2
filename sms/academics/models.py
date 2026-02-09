from django.db import models
from accounts.models import StudentProfile
# Create your models here.
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    faculty = models.ForeignKey(
        'accounts.FacultyProfile',   
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses'
    )

    class Meta:
        db_table = 'academics_course'

    def __str__(self):
        return f"{self.code} - {self.name}"

class Batch(models.Model):
    name = models.CharField(max_length=100)  
    program = models.CharField(max_length=100)      
    academic_year = models.CharField(max_length=9)  
    section = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academics_batch'
        unique_together = ('name', 'academic_year')

    def __str__(self):
        return f"{self.program} | {self.name} | {self.academic_year}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        'accounts.StudentProfile',   
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    course = models.ForeignKey(
        'academics.Course',        
        on_delete=models.CASCADE
    )

    enrolled_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academics_enrollment'
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.user.username} → {self.course.code}"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
    )

    student = models.ForeignKey(
        'accounts.StudentProfile',     
        on_delete=models.CASCADE,
        related_name='attendance'
    )
    course = models.ForeignKey(
        'academics.Course',            
        on_delete=models.CASCADE,
        related_name='attendance'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'academics_attendance'
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        return f"{self.student.user.username} - {self.course.code} ({self.date})"

class Exam(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    title = models.CharField(max_length=100)   # Midterm, End Semester
    date = models.DateField()
    total_marks = models.PositiveIntegerField()

    class Meta:
        db_table = 'academics_exam'

    def __str__(self):
        return f"{self.course.code} - {self.title}"

class ExamResult(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='results'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='exam_results'
    )
    marks_obtained = models.FloatField()

    class Meta:
        db_table = 'academics_exam_result'
        unique_together = ('exam', 'student')

    def grade(self):
        percentage = (self.marks_obtained / self.exam.total_marks) * 100
        if percentage >= 90:
            return 'A'
        elif percentage >= 75:
            return 'B'
        elif percentage >= 60:
            return 'C'
        elif percentage >= 40:
            return 'D'
        else:
            return 'F'

class Grade(models.Model):
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.CASCADE,
        related_name='grades'
    )
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='grades'
    )
    marks_obtained = models.PositiveIntegerField()

    class Meta:
        unique_together = ('exam', 'student')
        db_table = 'academics_grade'
    
    @property
    def percentage(self):
        if self.exam.total_marks > 0:
            return round((self.marks_obtained / self.exam.total_marks) * 100, 2)
        return 0
    @property
    def is_pass(self):
        return self.percentage >= 40
    
    @property
    def grade_letter(self):
        p = self.percentage
        if p >= 80:
            return 'A'
        elif p >= 65:
            return 'B'
        elif p >= 50:
            return 'C'
        elif p >= 40:
            return 'D'
        else:
            return 'F'

   
    @property
    def is_pass(self):
        return self.percentage >= 40


    def __str__(self):
        return f"{self.student.user.username} - {self.exam.title}"

class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    total_questions = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academics_quiz'

    def __str__(self):
        return f"{self.course.code} - {self.title}"

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question_text = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_option = models.CharField(
        max_length=1,
        choices=(
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        )
    )

    class Meta:
        db_table = 'academics_quiz_question'

    def __str__(self):
        return self.question_text[:50]

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )

    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField()
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academics_quiz_attempt'

    def __str__(self):
        return f"{self.student.user.username} - {self.quiz.title}"
    
    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 2)
    
class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE
    )
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = 'academics_quiz_answer'
        unique_together = ('attempt', 'question')
    
    def __str__(self):
        return f"{self.question.text[:30]} - {self.selected_option}"