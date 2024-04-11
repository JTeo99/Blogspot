from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Comment, Report
from .forms import CommentForm, PostForm, SignupForm, LoginForm
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Create your views here.

def custom_login(request):
    return render(request, 'user/login.html')

class PostListView(ListView):
    model = Post
    queryset = Post.objects.filter(status=1).order_by('-created_on')
    context_object_name = 'posts'
    template_name = 'core/index.html'
    paginate_by = 10

# Retrieve published post by slug
class PostDetailView(DetailView):
    model = Post
    template_name = 'core/post_details.html' 
    context_object_name = 'post'

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to login page after successful signup
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

# Bind the POST data to the form
# Create a new comment object but don't save it to the database yet
# Redirect to the post detail page after adding comment
# Create a new blank form
@login_required
def add_comment_to_post(request, slug):
    post = get_object_or_404(Post, slug=slug, status=1)
    if request.method == 'POST':
        form = CommentForm(request.POST)  
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.save()
            return redirect('post_details', slug=post.slug)
    else:
        form = CommentForm()  
    return render(request, 'core/add_comment_to_post.html', {'post': post, 'form': form})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.user:
        comment.delete()
    return redirect('post_details', slug=comment.post.slug)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_details', slug=post.slug)
    else:
        form = PostForm()
    return render(request, 'core/create_post.html', {'form': form})

@login_required
@require_POST
def like_post(request, slug):
    post = Post.objects.get(slug=slug)
    post.likes.add(request.user)
    return JsonResponse({'message': 'Post liked successfully.'})

@login_required
@require_POST
def dislike_post(request, slug):
    post = Post.objects.get(slug=slug)
    post.dislikes.add(request.user)
    return JsonResponse({'message': 'Post disliked successfully.'})

@login_required
@require_POST
def report_post(request, slug):
    post = Post.objects.get(slug=slug)
    Report.objects.create(reporter=request.user, reported_item=post, report_type=Report.POST)
    return JsonResponse({'message': 'Post reported successfully.'})

# Perform the search query
# Search in title
# Search in content
# Search in keywords field (if available)
# Ensure distinct results
def search(request):
    query = request.GET.get('q')
    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) |  
            Q(content__icontains=query) |  
            Q(keywords__icontains=query)
        ).distinct()
    else:
        results = None
    return render(request, 'core/search_results.html', {'query': query, 'results': results})
