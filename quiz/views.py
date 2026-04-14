"""Quiz view helpers and request handlers."""

import csv
import os
import random
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect

QUESTIONS_FILE = os.path.join(settings.BASE_DIR, 'questions.csv')
RESULTS_FILE = os.path.join(settings.BASE_DIR, 'results.csv')


def _build_answers_from_post(request):
    """Build a list of cleaned answers from a POST request."""
    answers = []
    for answer_number in range(1, 7):
        answer_text = request.POST.get(f'answer{answer_number}')
        if answer_text is None:
            continue
        answer_text = answer_text.strip()
        if answer_text:
            answers.append(answer_text)
    return answers


def _build_answers_from_question(question):
    """Build a list of cleaned answers from a question row."""
    answers = []
    for answer_number in range(1, 7):
        answer_text = question.get(f'answer{answer_number}')
        if answer_text is None:
            continue
        answer_text = answer_text.strip()
        if answer_text:
            answers.append(answer_text)
    return answers


def _load_questions():
    """Load quiz questions from the CSV file."""
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, 'r', encoding='utf-8-sig') as file_handle:
            return list(csv.DictReader(file_handle))
    return []


def index(request):
    """Render the home page."""
    return render(request, 'quiz/index.html')


def questions_list(request):
    """Render the questions list page."""
    questions = _load_questions()
    return render(request, 'quiz/questions_list.html', {'questions': questions})


def add_question(request):
    """Handle adding a new quiz question."""
    if request.method == 'POST':
        question = request.POST.get('question')
        correct_answer_number = request.POST.get('correct_answer_number')
        answers = _build_answers_from_post(request)
        if not question or not correct_answer_number or len(answers) < 2:
            messages.error(
                request,
                'Заполните вопрос, номер правильного ответа и минимум 2 варианта ответа.'
            )
            return redirect('add_question')
        try:
            correct_index = int(correct_answer_number)
            if correct_index < 1 or correct_index > len(answers):
                messages.error(
                    request,
                    'Номер правильного ответа должен быть между 1 и количеством вариантов.'
                )
                return redirect('add_question')
        except ValueError:
            messages.error(request, 'Неверный номер правильного ответа.')
            return redirect('add_question')
        with open(QUESTIONS_FILE, 'a', newline='', encoding='utf-8') as file_handle:
            writer = csv.writer(file_handle)
            row = [question, str(correct_index)] + answers
            row.extend([''] * (6 - len(answers)))
            writer.writerow(row)
        messages.success(request, 'Вопрос добавлен.')
        return redirect('questions_list')
    return render(request, 'quiz/add_question.html')


def _process_test_end(request):
    """Handle ending the quiz and saving the result."""
    score = request.session.get('quiz_score', 0)
    name = request.session.get('user_name')
    email = request.session.get('user_email')
    attempt = get_attempt(email) + 1
    save_result(name, email, attempt, score)
    total = int(request.POST.get('quiz_total', 0))
    request.session.flush()
    return render(
        request,
        'quiz/test_done.html',
        {'score': score, 'total': total}
    )


def _process_test_start(request):
    """Start the quiz and initialize session state."""
    name = request.POST.get('name')
    email = request.POST.get('email')
    if not name or not email:
        messages.error(request, 'Введите имя и email.')
        return redirect('take_test')
    questions = _load_questions()
    if not questions:
        messages.error(request, 'Нет вопросов для теста.')
        return redirect('take_test')
    random.shuffle(questions)
    request.session['quiz_questions'] = questions
    request.session['quiz_index'] = 0
    request.session['quiz_score'] = 0
    request.session['user_name'] = name
    request.session['user_email'] = email
    return redirect('take_test')


def _process_test_submission(request):
    """Process an answer submission during the quiz."""
    questions = request.session.get('quiz_questions', [])
    question_index = request.session.get('quiz_index', 0)
    score = request.session.get('quiz_score', 0)
    selected = request.POST.get('answer')
    answers = _build_answers_from_question(questions[question_index])
    correct_index = int(questions[question_index]['correct_answer'].strip())
    correct_answer_text = answers[correct_index - 1]
    if selected == correct_answer_text:
        score += 1
    question_index += 1
    if question_index >= len(questions):
        name = request.session.get('user_name')
        email = request.session.get('user_email')
        attempt = get_attempt(email) + 1
        save_result(name, email, attempt, score)
        request.session.flush()
        return render(
            request,
            'quiz/test_done.html',
            {'score': score, 'total': len(questions)}
        )
    request.session['quiz_index'] = question_index
    request.session['quiz_score'] = score
    return redirect('take_test')


def take_test(request):
    """Render or process the quiz session."""
    if request.method == 'POST':
        if 'start' in request.POST:
            return _process_test_start(request)
        if 'submit_answer' in request.POST:
            return _process_test_submission(request)
        if 'end' in request.POST:
            return _process_test_end(request)
    questions = request.session.get('quiz_questions')
    question_index = request.session.get('quiz_index', 0)
    if questions and question_index < len(questions):
        question = questions[question_index]
        answers = _build_answers_from_question(question)
        total = len(questions)
        return render(
            request,
            'quiz/take_test.html',
            {
                'question': question,
                'answers': answers,
                'index': question_index + 1,
                'total': total,
            },
        )
    return render(request, 'quiz/take_test.html')


def get_attempt(email):
    """Return the latest attempt count for the given email."""
    attempts = 0
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8-sig') as file_handle:
            reader = csv.DictReader(file_handle)
            for row in reader:
                if row['user_email'] == email:
                    attempts = max(attempts, int(row['attempt']))
    return attempts


def save_result(name, email, attempt, score):
    """Append a quiz result row to the CSV results file."""
    with open(RESULTS_FILE, 'a', newline='', encoding='utf-8-sig') as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow([name, email, attempt, score])


def scores(request):
    """Render the latest score for each unique email."""
    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8-sig') as file_handle:
            reader = csv.DictReader(file_handle)
            all_results = list(reader)
        latest_results = {}
        for row in all_results:
            email = row['user_email']
            attempt = int(row['attempt'])
            if email not in latest_results or attempt > int(latest_results[email]['attempt']):
                latest_results[email] = row
        results = list(latest_results.values())
    return render(request, 'quiz/scores.html', {'results': results})
