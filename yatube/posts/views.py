from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required


from .models import Follow, Group, Post, User
from .forms import PostForm, CommentForm
from core.paginator_custome import paginator_for_posts
from yatube.settings import NUM_POSTS_PER_PAGE


def index(request):
    """Вывод последних 10 публикаций на главную страницу."""
    post_list = Post.objects.all().select_related('group')
    page_obj = paginator_for_posts(
        request,
        post_list,
        NUM_POSTS_PER_PAGE
    )
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Вывод последних 10 публикаций сообщества."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator_for_posts(
        request,
        post_list,
        NUM_POSTS_PER_PAGE
    )
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Страница профиля автора."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator_for_posts(
        request,
        post_list,
        NUM_POSTS_PER_PAGE
    )
    template = 'posts/profile.html'
    context = {
        'page_obj': page_obj,
        'author': author,
    }
    if request.user.is_authenticated and request.user != username:
        following = author.following.filter(user=request.user)
        context['following'] = following
        return render(request, template, context)
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница деталей поста."""
    post_user = get_object_or_404(Post, id=post_id)
    total_posts = post_user.author.posts.count()
    form = CommentForm()
    comments = post_user.comments.all()
    template = 'posts/post_detail.html'
    context = {
        'post_user': post_user,
        'total_posts': total_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Страница для создания поста."""
    author = request.user
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = author
        post.save()
        return redirect('posts:profile', author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница для редактирования поста."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': True}
    )


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    """Страница авторов,
    на которых подписан пользователь.
    """
    post_list = Post.objects.filter(
        author__following__user=request.user).select_related('group')
    page_obj = paginator_for_posts(
        request,
        post_list,
        NUM_POSTS_PER_PAGE
    )
    context = {
        'page_obj': page_obj,
    }
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    follower = get_object_or_404(User, username=request.user)
    following = get_object_or_404(User, username=username)
    if following != request.user:
        Follow.objects.create(user=follower, author=following)
        return redirect('posts:follow_index')
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""
    follower = get_object_or_404(User, username=request.user)
    following = get_object_or_404(User, username=username)
    author = Follow.objects.get(user=follower, author=following)
    author.delete()
    return redirect('posts:profile', username)
