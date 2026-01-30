from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from .models import User, StudentProfile
from django import forms
class UserRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']

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
    address = forms.CharField(required=False, widget=forms.Textarea)
    admission_year = forms.IntegerField(required=False)

    # -------- Faculty-only fields --------
    department = forms.CharField(required=False)
    designation = forms.CharField(required=False)
# ==========================
# LOGIN FORM (ADD THIS PART)
# ==========================
class LoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)