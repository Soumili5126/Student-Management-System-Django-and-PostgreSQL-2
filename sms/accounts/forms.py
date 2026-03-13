from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from .models import User, StudentProfile,FacultyProfile,Role,User
from django import forms
from academics.models import Enrollment,Course,Batch
import re
from django.core.validators import RegexValidator

# Validator for alphabets only
alpha_validator = RegexValidator(
    regex=r'^[A-Za-z]+$',
    message="Only alphabets (A-Z) are allowed."
)


class UserRegisterForm(UserCreationForm):

    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        empty_label="Select Role",
        widget=forms.Select(attrs={
            "placeholder": "Select role"
        })
    )

    first_name = forms.CharField(
        validators=[alpha_validator],
        widget=forms.TextInput(attrs={
            "placeholder": "Enter first name"
        })
    )

    last_name = forms.CharField(
        validators=[alpha_validator],
        widget=forms.TextInput(attrs={
            "placeholder": "Enter last name"
        })
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
            'role',
        ]

        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Enter username'
            }),

            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter email address'
            }),
        }

    # -------- Student-only fields --------

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter phone number'
        })
    )

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'Select date of birth'
        })
    )

    gender = forms.ChoiceField(
        choices=StudentProfile.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'placeholder': 'Select gender'
        })
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter address',
            'rows': 3
        })
    )

    admission_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter admission year'
        })
    )

    # -------- Faculty-only fields --------

    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter department'
        })
    )

    designation = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter designation'
        })
    )

    # Add placeholders for password fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Enter password'
        })

        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm password'
        })
     # -------- UNIQUE EMAIL VALIDATION --------
    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email
    # -------- PASSWORD VALIDATION --------
    def clean_password1(self):
        password = self.cleaned_data.get('password1')

        first_name = self.cleaned_data.get('first_name', '').lower()
        last_name = self.cleaned_data.get('last_name', '').lower()
        username = self.cleaned_data.get('username', '').lower()
        email = self.cleaned_data.get('email', '').lower()

        if len(password) < 8:
            raise forms.ValidationError(
                "Password must be at least 8 characters long."
            )

        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r'[0-9]', password):
            raise forms.ValidationError(
                "Password must contain at least one number."
            )

        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            raise forms.ValidationError(
                "Password must contain at least one special symbol."
            )

        # Check similarity with personal information
        personal_info = [first_name, last_name, username, email]

        for info in personal_info:
            if info and info in password.lower():
                raise forms.ValidationError(
                    "Password cannot contain personal information."
                )

        return password
    


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Enter username",
            "class": "form-control"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter password",
            "class": "form-control"
        })
    )

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