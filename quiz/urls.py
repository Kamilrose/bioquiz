"""URL routes for the quiz application."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('questions/', views.questions_list, name='questions_list'),
    path('add_question/', views.add_question, name='add_question'),
    path('take_test/', views.take_test, name='take_test'),
    path('scores/', views.scores, name='scores'),
]
