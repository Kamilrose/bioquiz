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