import csv
import os
import random
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages

QUESTIONS_FILE = os.path.join(settings.BASE_DIR, 'questions.csv')
RESULTS_FILE = os.path.join(settings.BASE_DIR, 'results.csv')

def index(request):
    return render(request, 'quiz/index.html')

def questions_list(request):
    questions = []
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                questions.append(row)
    return render(request, 'quiz/questions_list.html', {'questions': questions})

def add_question(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        correct_answer_number = request.POST.get('correct_answer_number')
        answers = [request.POST.get(f'answer{i}').strip() for i in range(1,7) if request.POST.get(f'answer{i}').strip()]
        if not question or not correct_answer_number or len(answers) < 2:
            messages.error(request, 'Заполните вопрос, номер правильного ответа и минимум 2 варианта ответа.')
            return redirect('add_question')
        try:
            correct_index = int(correct_answer_number)
            if correct_index < 1 or correct_index > len(answers):
                messages.error(request, 'Номер правильного ответа должен быть между 1 и количеством вариантов.')
                return redirect('add_question')
        except ValueError:
            messages.error(request, 'Неверный номер правильного ответа.')
            return redirect('add_question')
        # Save to CSV
        with open(QUESTIONS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            row = [question, str(correct_index)] + answers + [''] * (6 - len(answers))
            writer.writerow(row)
        messages.success(request, 'Вопрос добавлен.')
        return redirect('questions_list')
    return render(request, 'quiz/add_question.html')

def take_test(request):
    if request.method == 'POST':
        if 'start' in request.POST:
            name = request.POST.get('name')
            email = request.POST.get('email')
            if not name or not email:
                messages.error(request, 'Введите имя и email.')
                return redirect('take_test')
            # Load questions
            questions = []
            if os.path.exists(QUESTIONS_FILE):
                with open(QUESTIONS_FILE, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    questions = list(reader)
            if not questions:
                messages.error(request, 'Нет вопросов для теста.')
                return redirect('take_test')
            # Shuffle questions
            random.shuffle(questions)
            request.session['quiz_questions'] = questions
            request.session['quiz_index'] = 0
            request.session['quiz_score'] = 0
            request.session['user_name'] = name
            request.session['user_email'] = email
            return redirect('take_test')
        elif 'submit_answer' in request.POST:
            questions = request.session.get('quiz_questions', [])
            index = request.session.get('quiz_index', 0)
            score = request.session.get('quiz_score', 0)
            selected = request.POST.get('answer').strip()
            answers = [questions[index].get(f'answer{i}').strip() for i in range(1,7) if questions[index].get(f'answer{i}').strip()]
            correct_index = int(questions[index]['correct_answer'].strip())
            correct_answer_text = answers[correct_index - 1]
            if selected == correct_answer_text:
                score += 1
            index += 1
            if index >= len(questions):
                # End test
                name = request.session.get('user_name')
                email = request.session.get('user_email')
                attempt = get_attempt(email) + 1
                save_result(name, email, attempt, score)
                request.session.flush()
                return render(request, 'quiz/test_done.html', {'score': score, 'total': len(questions)})
            request.session['quiz_index'] = index
            request.session['quiz_score'] = score
            return redirect('take_test')
        elif 'end' in request.POST:
            score = request.session.get('quiz_score', 0)
            name = request.session.get('user_name')
            email = request.session.get('user_email')
            attempt = get_attempt(email) + 1
            save_result(name, email, attempt, score)
            total = int(request.POST.get('quiz_total', 0))
            request.session.flush()
            return render(request, 'quiz/test_done.html', {'score': score, 'total': total})
    # Show current question or form
    questions = request.session.get('quiz_questions')
    index = request.session.get('quiz_index', 0)
    if questions and index < len(questions):
        question = questions[index]
        answers = [question.get(f'answer{i}').strip() for i in range(1,7) if question.get(f'answer{i}') and question.get(f'answer{i}').strip()]
        total = len(questions)
        return render(request, 'quiz/take_test.html', {'question': question, 'answers': answers, 'index': index+1, 'total': total})
    return render(request, 'quiz/take_test.html')

def get_attempt(email):
    attempts = 0
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['user_email'] == email:
                    attempts = max(attempts, int(row['attempt']))
    return attempts

def save_result(name, email, attempt, score):
    with open(RESULTS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([name, email, attempt, score])

def scores(request):
    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            all_results = list(reader)
        # Group by email and keep only the latest attempt
        latest_results = {}
        for row in all_results:
            email = row['user_email']
            attempt = int(row['attempt'])
            if email not in latest_results or attempt > int(latest_results[email]['attempt']):
                latest_results[email] = row
        results = list(latest_results.values())
    return render(request, 'quiz/scores.html', {'results': results})
