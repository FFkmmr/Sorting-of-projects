from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from .models import Project, MySets
from django import forms

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    placeholders = {
        'username': 'Username..',
        'email': 'Email..',
        'password1': 'Enter password...',
        'password2': 'Re-enter Password...'
    }

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        for field_name, placeholder in self.placeholders.items():
            self.fields[field_name].widget.attrs.update({'placeholder': placeholder})

class CreateProjectForm(ModelForm):
    new_technologies = forms.CharField(required=False)
    new_industries = forms.CharField(required=False)
    class Meta:
        model = Project
        fields = ['title', 'url', 'technologies', 'description', 'industries','sets','is_private']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter project title...'}),
            'url': forms.URLInput(attrs={'placeholder': 'Enter project link...'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter project description...', 'rows': 4}),
            'technologies': forms.CheckboxSelectMultiple(),
            'industries': forms.CheckboxSelectMultiple(),
            'new_technologies': forms.TextInput(attrs={'placeholder': 'Enter new technologies, separated by commas...',
            'class': 'wide-input'}),
            'new_idustries': forms.TextInput(attrs={'placeholder': 'Enter new industries, separated by commas...',
            'class': 'wide-input'}),
            'sets': forms.CheckboxSelectMultiple(),
        }
     
class CreateProjectSet(ModelForm):
    class Meta:
        model = MySets
        fields = ['name','is_private']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter set name...'}),
        }
        
        
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email")


class SetPasswordForm(DjangoSetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']


class UsernameChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']