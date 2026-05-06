import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import QuizSession, Question, Participant, Answer, ParticipantAnswer

class QuizConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.join_code = self.scope['url_route']['kwargs']['join_code']
        self.room_group_name = f'quiz_{self.join_code}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.broadcast_players()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    async def broadcast_players(self):
        players = await self.get_current_players()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'quiz_message',
                'message': {'players': players},
                'event': 'update_players' 
            }
        )

    @database_sync_to_async
    def get_current_players(self):
        session = QuizSession.objects.get(join_code=self.join_code)
        return list(session.participants.values_list('nickname', flat=True))
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'submit_answer':
            nickname = text_data_json.get('nickname')
            question_id = text_data_json.get('question_id')
            answer_id = text_data_json.get('answer_id')
            
            await self.save_user_answer(nickname, question_id, answer_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'quiz_message',
                    'message': {'nickname': nickname},
                    'event': 'player_answered'
                }
            )

        elif action == 'next_question':
            question_data = await self.get_next_question()
            
            if question_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'quiz_message',
                        'message': question_data,
                        'event': 'new_question'
                    }
                )
            else:
                leaderboard = await self.get_leaderboard()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'quiz_message',
                        'message': {'text': 'Вікторину завершено!', 'leaderboard': leaderboard},
                        'event': 'quiz_ended'
                    }
                )

    @database_sync_to_async
    def save_user_answer(self, nickname, question_id, answer_id):
        try:
            session = QuizSession.objects.get(join_code=self.join_code)
            participant = Participant.objects.filter(session=session, nickname=nickname).first()
            question = Question.objects.get(id=question_id)
            answer = Answer.objects.get(id=answer_id)
            
            if participant and question and answer:
                obj, created = ParticipantAnswer.objects.get_or_create(
                    participant=participant,
                    question=question,
                    defaults={'selected_answer': answer, 'is_correct': answer.is_correct}
                )
                if created and answer.is_correct:
                    participant.score += 10 
                    participant.save()
        except Exception as e:
            print("Помилка збереження:", e)

    @database_sync_to_async
    def get_next_question(self):
        try:
            session = QuizSession.objects.get(join_code=self.join_code)
            quiz = session.quiz
            questions = list(quiz.questions.all().order_by('order', 'id'))
            
            if session.current_question_index < len(questions):
                current_q = questions[session.current_question_index]
                answers = list(current_q.answers.all().values('id', 'text'))
                
                media_url = current_q.media_file.url if current_q.media_file else None
                
                data = {
                    'id': current_q.id,
                    'text': current_q.text,
                    'time_limit': current_q.time_limit,
                    'answers': answers,
                    'media_url': media_url 
                }
                session.current_question_index += 1
                session.save()
                return data
            return None
        except QuizSession.DoesNotExist:
            return None

    @database_sync_to_async
    def get_leaderboard(self):
        session = QuizSession.objects.get(join_code=self.join_code)
        participants = Participant.objects.filter(session=session).order_by('-score')
        return [{'name': p.nickname, 'score': p.score} for p in participants]

    async def quiz_message(self, event):
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'message': event['message']
        }))