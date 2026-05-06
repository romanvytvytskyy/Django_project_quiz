from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory  
from .models import User, Quiz, Question, Answer

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email') 

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть назву вікторини'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'media_file', 'time_limit', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
QuestionFormSet = inlineformset_factory(
    Quiz, 
    Question, 
    form=QuestionForm,
    extra=1, 
    can_delete=True 
)

AnswerFormSet = inlineformset_factory(
    Question, 
    Answer, 
    fields=['text', 'is_correct'],
    extra=4, 
    can_delete=True
)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }