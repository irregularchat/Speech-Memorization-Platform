from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Text, UserTextProgress
from .forms import TextForm, TextFileUploadForm, TextSearchForm
import json


def text_list(request):
    """Display list of texts with search and filter capabilities"""
    form = TextSearchForm(request.GET)
    
    # Base queryset for public texts
    public_texts = Text.objects.filter(is_public=True).order_by('-created_at')
    
    # User's texts if authenticated
    user_texts = []
    if request.user.is_authenticated:
        user_texts = Text.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Apply search filters if form is valid
    if form.is_valid():
        search_query = form.cleaned_data.get('search')
        difficulty = form.cleaned_data.get('difficulty')
        tag = form.cleaned_data.get('tag')
        my_texts_only = form.cleaned_data.get('my_texts_only')
        
        if search_query:
            # Search in title, description, and content
            search_filter = Q(title__icontains=search_query) | \
                          Q(description__icontains=search_query) | \
                          Q(tags__icontains=search_query)
            public_texts = public_texts.filter(search_filter)
            user_texts = user_texts.filter(search_filter) if user_texts else []
        
        if difficulty:
            public_texts = public_texts.filter(difficulty=difficulty)
            user_texts = user_texts.filter(difficulty=difficulty) if user_texts else []
        
        if tag:
            public_texts = public_texts.filter(tags__icontains=tag)
            user_texts = user_texts.filter(tags__icontains=tag) if user_texts else []
        
        if my_texts_only and request.user.is_authenticated:
            public_texts = Text.objects.none()  # Hide public texts
    
    # Pagination for public texts
    paginator = Paginator(public_texts, 12)
    page_number = request.GET.get('page')
    public_texts = paginator.get_page(page_number)
    
    context = {
        'public_texts': public_texts,
        'user_texts': user_texts[:12],  # Limit user texts to 12
        'search_form': form,
    }
    
    return render(request, 'core/text_list.html', context)


@login_required
def create_text(request):
    """Create a new text"""
    if request.method == 'POST':
        form = TextForm(request.POST)
        if form.is_valid():
            text = form.save(commit=False)
            text.created_by = request.user
            text.save()
            messages.success(request, f'Text "{text.title}" created successfully!')
            return redirect('practice_text', text_id=text.id)
    else:
        form = TextForm()
    
    context = {
        'form': form,
        'title': 'Create New Text',
        'submit_text': 'Create Text'
    }
    return render(request, 'memorization/text_form.html', context)


@login_required
def edit_text(request, text_id):
    """Edit an existing text"""
    text = get_object_or_404(Text, id=text_id, created_by=request.user)
    
    if request.method == 'POST':
        form = TextForm(request.POST, instance=text)
        if form.is_valid():
            form.save()
            messages.success(request, f'Text "{text.title}" updated successfully!')
            return redirect('practice_text', text_id=text.id)
    else:
        form = TextForm(instance=text)
    
    context = {
        'form': form,
        'text': text,
        'title': f'Edit "{text.title}"',
        'submit_text': 'Update Text'
    }
    return render(request, 'memorization/text_form.html', context)


@login_required
def delete_text(request, text_id):
    """Delete a text"""
    text = get_object_or_404(Text, id=text_id, created_by=request.user)
    
    if request.method == 'POST':
        title = text.title
        text.delete()
        messages.success(request, f'Text "{title}" deleted successfully!')
        return redirect('text_list')
    
    context = {
        'text': text,
        'title': f'Delete "{text.title}"'
    }
    return render(request, 'memorization/text_confirm_delete.html', context)


@login_required
def upload_text_file(request):
    """Upload a text file and create a new text"""
    if request.method == 'POST':
        form = TextFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Read file content
            uploaded_file = form.cleaned_data['file']
            try:
                content = uploaded_file.read().decode('utf-8')
            except UnicodeDecodeError:
                messages.error(request, 'Invalid file format. Please upload a UTF-8 text file.')
                return render(request, 'memorization/upload_form.html', {'form': form})
            
            # Create text object
            title = form.cleaned_data.get('title') or uploaded_file.name.replace('.txt', '')
            
            text = Text.objects.create(
                title=title,
                content=content.strip(),
                description=form.cleaned_data.get('description', ''),
                difficulty=form.cleaned_data.get('difficulty', 'beginner'),
                tags=form.cleaned_data.get('tags', ''),
                time_limit=form.cleaned_data.get('time_limit'),
                is_public=form.cleaned_data.get('is_public', False),
                created_by=request.user
            )
            
            messages.success(request, f'Text "{text.title}" uploaded successfully!')
            return redirect('practice_text', text_id=text.id)
    else:
        form = TextFileUploadForm()
    
    context = {
        'form': form,
        'title': 'Upload Text File',
        'submit_text': 'Upload and Create Text'
    }
    return render(request, 'memorization/upload_form.html', context)


@login_required
@require_http_methods(["POST"])
def create_text_ajax(request):
    """AJAX endpoint for creating texts"""
    try:
        data = json.loads(request.body)
        
        # Create form with AJAX data
        form_data = {
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'description': data.get('description', ''),
            'difficulty': data.get('difficulty', 'beginner'),
            'tags': data.get('tags', ''),
            'time_limit': data.get('time_limit'),
            'is_public': data.get('is_public', False)
        }
        
        form = TextForm(form_data)
        if form.is_valid():
            text = form.save(commit=False)
            text.created_by = request.user
            text.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Text "{text.title}" created successfully!',
                'text_id': text.id,
                'redirect_url': f'/practice/{text.id}/'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def toggle_text_visibility(request, text_id):
    """Toggle text public/private status"""
    text = get_object_or_404(Text, id=text_id, created_by=request.user)
    
    text.is_public = not text.is_public
    text.save()
    
    status = "public" if text.is_public else "private"
    messages.success(request, f'Text "{text.title}" is now {status}.')
    
    return redirect('text_list')


def text_detail(request, text_id):
    """Display text details"""
    text = get_object_or_404(Text, id=text_id)
    
    # Check if user can view this text
    if not text.is_public and text.created_by != request.user:
        messages.error(request, 'You do not have permission to view this text.')
        return redirect('text_list')
    
    # Get user's progress if authenticated
    user_progress = None
    if request.user.is_authenticated:
        user_progress, created = UserTextProgress.objects.get_or_create(
            user=request.user,
            text=text
        )
    
    context = {
        'text': text,
        'user_progress': user_progress,
        'can_edit': request.user.is_authenticated and text.created_by == request.user
    }
    
    return render(request, 'memorization/text_detail.html', context)


@login_required
def duplicate_text(request, text_id):
    """Create a copy of an existing text"""
    original_text = get_object_or_404(Text, id=text_id)
    
    # Check if user can access this text
    if not original_text.is_public and original_text.created_by != request.user:
        messages.error(request, 'You do not have permission to duplicate this text.')
        return redirect('text_list')
    
    # Create duplicate
    duplicate = Text.objects.create(
        title=f"Copy of {original_text.title}",
        content=original_text.content,
        description=original_text.description,
        difficulty=original_text.difficulty,
        tags=original_text.tags,
        time_limit=original_text.time_limit,
        is_public=False,  # Always make duplicates private by default
        created_by=request.user
    )
    
    messages.success(request, f'Text duplicated as "{duplicate.title}". You can now edit it.')
    return redirect('edit_text', text_id=duplicate.id)


def practice_modes(request, text_id):
    """Practice with all modes: Speech, Typing, Karaoke, Enhanced"""
    text = get_object_or_404(Text, id=text_id)
    
    # Check if user can access this text
    if not text.is_public and text.created_by != request.user:
        messages.error(request, 'You do not have permission to practice this text.')
        return redirect('text_list')
    
    # Get or create user progress
    user_progress = None
    if request.user.is_authenticated:
        user_progress, created = UserTextProgress.objects.get_or_create(
            user=request.user,
            text=text
        )
    
    context = {
        'text': text,
        'user_progress': user_progress,
        'word_count': len(text.content.split()),
        'can_edit': request.user.is_authenticated and text.created_by == request.user
    }
    
    return render(request, 'memorization/practice_modes.html', context)