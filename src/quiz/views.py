from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms import inlineformset_factory
from django.db import transaction
from .models import Exam, Question, Choice
from .forms import ExamForm, QuestionForm, ChoiceFormSet

def exam_list(request):
    exams = Exam.objects.all().order_by('-created_date')
    return render(request, 'quiz/exam_list.html', {'exams': exams})

def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all().prefetch_related('choices')
    return render(request, 'quiz/exam_detail.html', {'exam': exam, 'questions': questions})

def exam_create(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            messages.success(request, 'Examen creado correctamente.')
            return redirect('question_create', exam_id=exam.id)
    else:
        form = ExamForm()
    
    return render(request, 'quiz/exam_form.html', {'form': form})

def question_create(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        
        if question_form.is_valid():
            with transaction.atomic():
                question = question_form.save(commit=False)
                question.exam = exam
                question.save()
                
                formset = ChoiceFormSet(request.POST, instance=question)
                if formset.is_valid():
                    formset.save()
                    correct_count = question.choices.filter(is_correct=True).count()
                    if correct_count != 1:
                        messages.warning(request, 'Debe haber exactamente una respuesta correcta.')
                    else:
                        messages.success(request, 'Pregunta añadida correctamente.')
                    
                    if 'add_another' in request.POST:
                        return redirect('question_create', exam_id=exam.id)
                    else:
                        return redirect('exam_detail', exam_id=exam.id)
    else:
        question_form = QuestionForm()
        formset = ChoiceFormSet()
    
    return render(request, 'quiz/question_form.html', {
        'exam': exam,
        'question_form': question_form,
        'formset': formset,
    })

# ------------------------------ 
# NUEVAS FUNCIONALIDADES: EDITAR Y ELIMINAR PREGUNTAS
# ------------------------------ 

def question_edit(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    exam = question.exam
    
    if request.method == "POST":
        question_form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        
        if question_form.is_valid() and formset.is_valid():
            question_form.save()
            formset.save()
            messages.success(request, 'Pregunta editada correctamente.')
            return redirect('exam_detail', exam_id=exam.id)
    else:
        question_form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)
    
    return render(request, 'quiz/question_form.html', {
        'exam': exam,
        'question_form': question_form,
        'formset': formset,
    })

def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    exam_id = question.exam.id
    
    if request.method == "POST":
        question.delete()
        messages.success(request, 'Pregunta eliminada correctamente.')
        return redirect('exam_detail', exam_id=exam_id)
    
    return render(request, 'quiz/question_confirm_delete.html', {'question': question})

# ------------------------------
# FUNCIONALIDAD PARA JUGAR EL EXAMEN
# ------------------------------

def exam_play(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all().prefetch_related('choices')
    
    # Preparamos los datos para las preguntas con sus respuestas
    question_data = []
    
    if request.method == "POST":
        for question in questions:
            question_info = {
                'question': question,
                'has_response': False
            }
            
            selected_choice_id = request.POST.get(f"question_{question.id}")
            if selected_choice_id:
                selected_choice = get_object_or_404(Choice, id=selected_choice_id)
                question_info['has_response'] = True
                question_info['selected_choice'] = selected_choice
                question_info['is_correct'] = selected_choice.is_correct
            
            question_data.append(question_info)
        
        return render(request, 'quiz/exam_play.html', {
            'exam': exam,
            'question_data': question_data
        })
    
    return render(request, 'quiz/exam_play.html', {'exam': exam, 'questions': questions})
