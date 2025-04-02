from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms import inlineformset_factory
from django.db import transaction
from .models import Exam, Question, Choice
from .forms import ExamForm, QuestionForm, ChoiceFormSet
from django.shortcuts import render, get_object_or_404, redirect
from .models import Question
from .forms import QuestionForm
#actualizar 
def exam_update(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            return redirect('exam_detail', exam_id=exam.id)
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'quiz/exam_form.html', {'form': form, 'exam': exam})
#fin actualizar


#eliminar
def exam_delete(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam.delete()
    messages.success(request, 'Examen eliminado correctamente.')
    return redirect('exam_list')
#fin eliminar
def exam_list(request):
    """Vista para listar todos los exámenes"""
    exams = Exam.objects.all().order_by('-created_date')
    return render(request, 'quiz/exam_list.html', {'exams': exams})

def exam_detail(request, exam_id):
    """Vista para mostrar el detalle de un examen con sus preguntas"""
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all().prefetch_related('choices')
    return render(request, 'quiz/exam_detail.html', {'exam': exam, 'questions': questions})

def exam_create(request):
    """Vista para crear un nuevo examen"""
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
    """Vista para añadir preguntas a un examen"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        
        if question_form.is_valid():
            with transaction.atomic():
                # Guardar la pregunta
                question = question_form.save(commit=False)
                question.exam = exam
                question.save()
                
                # Procesar el formset para las opciones
                formset = ChoiceFormSet(request.POST, instance=question)
                if formset.is_valid():
                    formset.save()
                    
                    # Verificar que solo una opción sea marcada como correcta
                    correct_count = question.choices.filter(is_correct=True).count()
                    if correct_count != 1:
                        messages.warning(request, 'Debe haber exactamente una respuesta correcta.')
                    else:
                        messages.success(request, 'Pregunta añadida correctamente.')
                        
                    # Decidir a dónde redirigir
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

def play_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_choices = request.POST.getlist(f'question_{question.id}')
            correct_choices = question.choices.filter(is_correct=True).values_list('id', flat=True)

            # Asegurarse de comparar las respuestas seleccionadas con las correctas
            if set(map(int, selected_choices)) == set(correct_choices):
                score += 1

        return render(request, 'quiz/exam_result.html', {'exam': exam, 'score': score, 'total': len(questions)})

    return render(request, 'quiz/play_exam.html', {'exam': exam, 'questions': questions})

def question_edit(request, question_id):
    # Obtener la pregunta que queremos editar
    question = get_object_or_404(Question, id=question_id)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('exam_detail', exam_id=question.exam.id)  # Redirige a la vista del examen
    else:
        form = QuestionForm(instance=question)  # Si es GET, muestra el formulario con los datos existentes

    return render(request, 'quiz/question_form.html', {'form': form, 'question': question})

def question_edit(request, question_id):
    # Obtener la pregunta que queremos editar
    question = get_object_or_404(Question, id=question_id)
    exam = question.exam  # Obtener el examen relacionado

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()  # Guardar las opciones
            return redirect('exam_detail', exam_id=exam.id)  # Redirige a la vista del examen
    else:
        form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)  # Mostrar las opciones de respuesta existentes

    return render(request, 'quiz/question_form.html', {'form': form, 'formset': formset, 'question': question, 'exam': exam})
