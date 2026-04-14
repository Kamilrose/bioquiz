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