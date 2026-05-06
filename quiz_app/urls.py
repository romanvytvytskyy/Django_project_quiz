from django.urls import path
from . import views
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views


urlpatterns = [
    path('', views.QuizListView.as_view(), name='quiz_list'),
    path('quiz/create/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('quiz/<int:pk>/update/', views.QuizUpdateView.as_view(), name='quiz_update'),
    path('quiz/<int:pk>/delete/', views.QuizDeleteView.as_view(), name='quiz_delete'),
    path('quiz/<int:pk>/questions/', views.QuizQuestionsUpdateView.as_view(), name='quiz_questions'),
    
    
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='quiz_list'), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    path('quiz/<int:pk>/start/', views.start_quiz_session, name='start_quiz_session'),
    path('quiz/join/', views.join_quiz, name='join_quiz'),
    path('room/host/<str:join_code>/', views.quiz_host_room, name='quiz_host_room'),
    path('room/player/<str:join_code>/', views.quiz_player_room, name='quiz_player_room'),
    path('question/<int:pk>/answers/', views.QuestionAnswersUpdateView.as_view(), name='question_answers'),
    
    
]
