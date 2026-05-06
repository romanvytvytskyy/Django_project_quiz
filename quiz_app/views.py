from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Quiz, QuizSession, Participant, Question, User
from .forms import QuizForm,CustomUserCreationForm,QuestionFormSet, AnswerFormSet, UserProfileForm
from django.contrib.auth import login
import uuid
from django.contrib import messages

# Create your views here.





class RegisterUserView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('quiz_list') 

    def form_valid(self, form):
       
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz/quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        return Quiz.objects.filter(is_active=True).order_by('-created_at')

class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'
    success_url = reverse_lazy('quiz_list') 

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class QuizUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'
    success_url = reverse_lazy('quiz_list')

    def test_func(self):
        quiz = self.get_object()
        return self.request.user == quiz.creator or self.request.user.is_admin

class QuizDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Quiz
    template_name = 'quiz/quiz_confirm_delete.html'
    success_url = reverse_lazy('quiz_list')

    def test_func(self):
        quiz = self.get_object()
        return self.request.user == quiz.creator or self.request.user.is_admin
    
    
class QuizQuestionsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Quiz
    template_name = 'quiz/quiz_questions_form.html'
    fields = [] 

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['questions'] = QuestionFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            data['questions'] = QuestionFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context['questions']
        if questions.is_valid():
            self.object = form.save()
            questions.instance = self.object
            questions.save()
            return redirect('quiz_list')
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def test_func(self):
        quiz = self.get_object()
        return self.request.user == quiz.creator or self.request.user.is_admin
    

class QuestionAnswersUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Question
    template_name = 'quiz/question_answers_form.html'
    fields = []

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['answers'] = AnswerFormSet(self.request.POST, instance=self.object)
        else:
            data['answers'] = AnswerFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        answers = context['answers']
        if answers.is_valid():
            answers.save()
            return redirect('quiz_questions', pk=self.object.quiz.pk)
        return self.render_to_response(self.get_context_data(form=form))

    def test_func(self):
        question = self.get_object()
        return self.request.user == question.quiz.creator or getattr(self.request.user, 'is_admin', False)


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'registration/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        history = Participant.objects.filter(user=self.request.user).select_related('session__quiz').order_by('-joined_at')
        
        context['history'] = history
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Ваш профіль успішно оновлено!')
        return super().form_valid(form)


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'registration/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        history = Participant.objects.filter(user=self.request.user).select_related('session__quiz').order_by('-joined_at')
        context['history'] = history
        hosted_sessions = QuizSession.objects.filter(host=self.request.user).select_related('quiz').prefetch_related('participants').order_by('-created_at')
        context['hosted_sessions'] = hosted_sessions
        
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Ваш профіль успішно оновлено!')
        return super().form_valid(form)

def start_quiz_session(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.user != quiz.creator and not getattr(request.user, 'is_admin', False):
        messages.error(request, "У вас немає прав для запуску цієї вікторини.")
        return redirect('quiz_list')
    session = QuizSession.objects.create(quiz=quiz, host=request.user)
    return redirect('quiz_host_room', join_code=session.join_code)
def join_quiz(request):
    join_code = request.GET.get('join_code', '').upper().strip()
    nickname = request.GET.get('nickname', '').strip() 
    
    if join_code and nickname:
        try:
            session = QuizSession.objects.get(join_code=join_code)
            
            request.session['quiz_nickname'] = nickname 
            
            user_obj = request.user if request.user.is_authenticated else None
            
            Participant.objects.get_or_create(
                session=session, 
                nickname=nickname, 
                defaults={'user': user_obj}
            )
            
            return redirect('quiz_player_room', join_code=join_code)
            
        except QuizSession.DoesNotExist:
            messages.error(request, "Сесію не знайдено. Перевірте код!")
            
    return redirect('quiz_list')

def quiz_host_room(request, join_code):
    session = get_object_or_404(QuizSession, join_code=join_code)
    return render(request, 'quiz/host_room.html', {'session': session})

def quiz_player_room(request, join_code):
    session = get_object_or_404(QuizSession, join_code=join_code)
    nickname = request.session.get('quiz_nickname', request.user.username if request.user.is_authenticated else "Гість")
    return render(request, 'quiz/player_room.html', {'session': session, 'nickname': nickname})