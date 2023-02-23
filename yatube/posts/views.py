from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


POST_NUMBER = 10


def do_pagination(request, posts):
    paginator = Paginator(posts, POST_NUMBER)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    posts = Post.objects.all()
    page_obj = do_pagination(request, posts)
    template = 'posts/index.html'
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).select_related('group').all()
    template = 'posts/group_list.html'
    page_obj = do_pagination(request, posts)
    context = {'group': group,
               'page_obj': page_obj, }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = do_pagination(request, posts)
    template = 'posts/profile.html'
    following = (request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists())

    context = {'page_obj': page_obj,
               'author': author,
               'following': following}
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post_id=post_id)
    template = 'posts/post_detail.html'
    context = {'post': post,
               'form': form,
               'comments': comments}
    if form.is_valid():

        form_to_comment = form.save(commit=False)
        form_to_comment.post = post
        form_to_comment.save()

        return redirect('posts:post_detail', post_id=post_id)

    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)

    template = 'posts/create_post.html'
    context = {'form': form}
    if form.is_valid():

        form_to_post = form.save(commit=False)
        form_to_post.author = request.user
        form_to_post.save()

        return redirect('posts:profile', request.user.username)

    return render(request, template, context)


def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    template = 'posts/create_post.html'
    context = {'form': form, 'post': post, 'is_edit': True}
    if form.is_valid():
        form.save()

        return redirect('posts:post_detail', post.id)

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = do_pagination(request, posts)
    template = 'posts/follow.html'
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    '''Follow the author.'''
    if request.user.get_username() != username:
        Follow.objects.get_or_create(
            author=User.objects.get(username=username),
            user=request.user,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    '''Unfollow the author.'''
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
