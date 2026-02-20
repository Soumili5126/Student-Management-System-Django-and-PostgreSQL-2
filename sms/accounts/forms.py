from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from .models import User, StudentProfile,FacultyProfile,Role,User
from django import forms
from academics.models import Enrollment,Course,Batch

class UserRegisterForm(UserCreationForm):

    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),   # ✅ include Admin too
        empty_label="Select Role"
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
            'role',   # ✅ MUST be included
        ]

    # -------- Student-only fields --------
    phone = forms.CharField(required=False)

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    gender = forms.ChoiceField(
        choices=StudentProfile.GENDER_CHOICES,
        required=False
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    admission_year = forms.IntegerField(required=False)

    # -------- Faculty-only fields --------
    department = forms.CharField(required=False)
    designation = forms.CharField(required=False)
# LOGIN FORM 
class LoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class EnrollmentEditForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['course']

class AssignBatchForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=StudentProfile.objects.select_related('user'),
        label="Select Student"
    )
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all(),
        label="Select Batch"
    )

class CourseForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(
        queryset=FacultyProfile.objects.select_related('user'),
        required=False,
        empty_label="Select Faculty"
    )

    class Meta:
        model = Course
        fields = ['code', 'name', 'department', 'faculty']