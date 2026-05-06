from django.db import models
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Quiz(models.Model):
    title = models.CharField(max_length=255, verbose_name="Назва вікторини")
    description = models.TextField(blank=True, verbose_name="Опис")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = (
        ('text', 'Текст'),
        ('image', 'Зображення'),
        ('video', 'Відео'),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Текст запитання")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='text')
    media_file = models.FileField(upload_to='question_media/', blank=True, null=True, verbose_name="Медіафайл")
    time_limit = models.IntegerField(default=30, verbose_name="Час на відповідь (сек)")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок запитання")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:20]}"

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255, verbose_name="Варіант відповіді")
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizSession(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    join_code = models.CharField(max_length=10, unique=True, blank=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_sessions')
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    current_question_index = models.IntegerField(default=0)
    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session {self.join_code} - {self.quiz.title}"
    
    def get_winner(self):
        winner = self.participants.order_by('-score').first()
        if winner and winner.score > 0:
            return f"{winner.nickname} ({winner.score} б.)"
        return "Немає результатів"

class Participant(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    nickname = models.CharField(max_length=50) 
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nickname} - {self.session.join_code}"

class ParticipantAnswer(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='given_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
    
