from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'id': 'reg_full_name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'id': 'reg_email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control border-start-0 border-end-0',
            'placeholder': 'Create a password (min. 6 characters)',
            'id': 'reg_password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control border-start-0 border-end-0',
            'placeholder': 'Re-enter your password',
            'id': 'reg_confirm_password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a unique username',
                'id': 'reg_username'
            })
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        if password and len(password) < 6:
            self.add_error('password', "Password must be at least 6 characters long.")
            
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        
        full_name = self.cleaned_data.get('full_name', '').strip()
        names = full_name.split(' ', 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ''
        
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'id': 'login_username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control border-start-0 border-end-0',
            'placeholder': 'Enter your password',
            'id': 'login_password'
        })
    )


class UserProfileUpdateForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'profile_full_name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'profile_email'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write something about yourself...', 'id': 'profile_bio'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'id': 'profile_picture_input'})
    )
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'profile_email_notifications'}),
        label='Receive email notifications when offline'
    )

    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'email_notifications']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['full_name'].initial = self.user.profile.full_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.email = self.cleaned_data.get('email', self.user.email)
            full_name = self.cleaned_data.get('full_name', '').strip()
            names = full_name.split(' ', 1)
            self.user.first_name = names[0]
            self.user.last_name = names[1] if len(names) > 1 else ''
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile
