import shutil
import tempfile

from http import HTTPStatus
from django import forms
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from posts.models import Comment, Group, Post, Follow

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='noname')
        cls.user_2 = User.objects.create_user(username='noname_2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostsPagesTests.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(PostsPagesTests.user_2)
        self.index_page = (
            'posts/index.html',
            'posts:index',
            None
        )
        self.follow_page = (
            'posts/follow.html',
            'posts:follow_index',
            None
        )
        self.profile_follow = (
            'posts:profile_follow',
            PostsPagesTests.author
        )
        self.profile_unfollow = (
            'posts:profile_unfollow',
            PostsPagesTests.author
        )
        self.group_page = (
            'posts/group_list.html',
            'posts:group_list',
            PostsPagesTests.group.slug
        )
        self.profile_page = (
            'posts/profile.html',
            'posts:profile',
            PostsPagesTests.author
        )
        self.post_detail_page = (
            'posts/post_detail.html',
            'posts:post_detail',
            PostsPagesTests.post.pk
        )
        self.create_page = (
            'posts/create_post.html',
            'posts:post_create',
            None
        )
        self.edit_page = (
            'posts/create_post.html',
            'posts:post_edit',
            PostsPagesTests.post.pk
        )
        self.add_comment_page = (
            'posts:add_comment',
            PostsPagesTests.post.pk
        )
        self.urls_for_all_users = (
            self.index_page,
            self.group_page,
            self.profile_page,
            self.post_detail_page
        )

    def test_pages_uses_correct_template_guest(self):
        """URL-адрес использует соответствующий шаблон для гостей."""
        templates_pages_names = (
            *self.urls_for_all_users,
        )
        for template, view, args in templates_pages_names:
            with self.subTest(view=view):
                if args:
                    response = self.guest_client.get(
                        reverse(view, args=[args])
                    )
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.guest_client.get(reverse(view))
                    self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон
        для авторизованных.
        """
        templates_pages_names = (
            *self.urls_for_all_users,
            self.create_page,
            self.follow_page
        )
        for template, view, args in templates_pages_names:
            with self.subTest(view=view):
                if args:
                    response = self.authorized_client.get(
                        reverse(view, args=[args])
                    )
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.authorized_client.get(reverse(view))
                    self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_author(self):
        """URL-адрес использует соответствующий шаблон
        для автора.
        """
        templates_pages_names = (
            *self.urls_for_all_users,
            self.create_page,
            self.edit_page,
            self.follow_page
        )
        for template, view, args in templates_pages_names:
            with self.subTest(view=view):
                if args:
                    response = self.author_client.get(
                        reverse(view, args=[args])
                    )
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.author_client.get(reverse(view))
                    self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.index_page[1])
        )
        context_page = response.context.get('page_obj').object_list
        post = context_page[0]
        self.assertEqual(*context_page, PostsPagesTests.post)
        self.assertEqual(post.author, PostsPagesTests.author)
        self.assertEqual(post.group, PostsPagesTests.group)
        self.assertEqual(
            post.pub_date, PostsPagesTests.post.pub_date
        )
        self.assertEqual(post.text, PostsPagesTests.post.text)

    def test_cache_index_page(self):
        """Кеш сохраняется при удаление поста
        и удаляется после принудительной чистки кеша.
        """
        post = Post.objects.get(id=PostsPagesTests.post.id)
        post.delete()
        response = self.authorized_client.get(
            reverse(self.index_page[1])
        )
        self.assertIn(
            PostsPagesTests.post.text, response.content.decode('utf-8')
        )
        key = make_template_fragment_key('index_page')
        cache.delete(key)
        response = self.authorized_client.get(
            reverse(self.index_page[1])
        )
        self.assertNotIn(
            PostsPagesTests.post.text, response.content.decode('utf-8')
        )

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.group_page[1], args=[self.group_page[2]])
        )
        context_page = response.context.get('page_obj').object_list[0]
        group = response.context.get('group')
        self.assertEqual(context_page.group.slug, PostsPagesTests.group.slug)
        self.assertEqual(group, PostsPagesTests.group)
        self.assertEqual(context_page.author, PostsPagesTests.author)
        self.assertEqual(
            context_page.pub_date, PostsPagesTests.post.pub_date
        )
        self.assertEqual(context_page.text, PostsPagesTests.post.text)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.profile_page[1], args=[self.profile_page[2]])
        )
        context_page = response.context.get('page_obj').object_list[0]
        author = response.context.get('author')
        self.assertEqual(context_page.author, PostsPagesTests.author)
        self.assertEqual(author, PostsPagesTests.author)
        self.assertEqual(
            context_page.pub_date, PostsPagesTests.post.pub_date
        )
        self.assertEqual(context_page.text, PostsPagesTests.post.text)
        self.assertEqual(context_page.group, PostsPagesTests.group)
        self.assertTrue(response.context.get('following'))

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.post_detail_page[1], args=[self.post_detail_page[2]])
        )
        form_fields = {
            'text': forms.fields.CharField,
        }
        form_field = response.context.get('form').fields.get('text')
        context_page = response.context.get('post_user')
        author_count_posts = response.context.get('total_posts')
        comments = response.context.get('comments')[0]
        self.assertIsInstance(form_field, form_fields['text'])
        self.assertEqual(context_page.id, PostsPagesTests.post.id)
        self.assertEqual(
            author_count_posts, PostsPagesTests.author.posts.count()
        )
        self.assertEqual(context_page.author, PostsPagesTests.author)
        self.assertEqual(
            context_page.pub_date, PostsPagesTests.post.pub_date
        )
        self.assertEqual(context_page.text, PostsPagesTests.post.text)
        self.assertEqual(context_page.group, PostsPagesTests.group)
        self.assertEqual(comments.text, PostsPagesTests.comment.text)
        self.assertEqual(comments.author, PostsPagesTests.author)

    def test_add_comment_page_authorized_client(self):
        """Комментировать посты может авторизованный пользователь."""
        response = self.authorized_client.get(
            reverse(
                self.add_comment_page[0], args=[self.add_comment_page[1]]
            )
        )
        self.assertRedirects(
            response,
            reverse(
                self.post_detail_page[1], args=[self.post_detail_page[2]]
            )
        )

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.create_page[1])
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(self.edit_page[1], args=[self.edit_page[2]])
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))

    def test_follow_page_show_correct_context_follower(self):
        """Запись появляется в ленте тех, кто подписан на автора."""
        user = User.objects.create_user(username='follower')
        author = User.objects.create_user(username='following')
        Follow.objects.create(user=user, author=author)
        post_author = Post.objects.create(
            author=author,
            text='Пост автора',
            group=PostsPagesTests.group
        )
        self.authorized_client.force_login(user)
        response = self.authorized_client.get(
            reverse(self.follow_page[1])
        )
        context_page = response.context.get('page_obj').object_list
        post_context = context_page[0]
        self.assertEqual(post_context.author, author)
        self.assertEqual(post_context.group, post_author.group)
        self.assertEqual(
            post_context.pub_date, post_author.pub_date
        )
        self.assertEqual(post_context.text, post_author.text)

    def test_follow_page_show_correct_context_unfollower(self):
        """Запись не появляется в ленте тех, кто не подписан на автора."""
        user = User.objects.create_user(username='follower')
        author = User.objects.create_user(username='following')
        Follow.objects.create(user=user, author=PostsPagesTests.author)
        post_author = Post.objects.create(
            author=author,
            text='Пост автора',
            group=PostsPagesTests.group
        )
        self.authorized_client.force_login(user)
        response = self.authorized_client.get(
            reverse(self.follow_page[1])
        )
        context_page = response.context.get('page_obj').object_list
        post_context = context_page[0]
        self.assertNotEqual(post_context.text, post_author.text)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей.
        """
        count_follow = Follow.objects.count()
        response = self.authorized_client_2.get(
            reverse(self.profile_follow[0], args=[self.profile_follow[1]]),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertRedirects(
            response,
            reverse(self.follow_page[1])
        )

    def test_profile_unfollow(self):
        """Авторизованный пользователь может удалять из подписок
        других пользователей.
        """
        count_follow = Follow.objects.count()
        response = self.authorized_client.get(
            reverse(self.profile_unfollow[0], args=[self.profile_unfollow[1]]),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Follow.objects.count(), count_follow - 1)
        self.assertRedirects(
            response,
            reverse(self.profile_page[1], args=[self.profile_page[2]])
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='noname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = [
            Post(
                author=cls.author,
                text=f'Тестовый пост {num}',
                group=cls.group,
            ) for num in range(1, 13)
        ]
        Post.objects.bulk_create(cls.posts)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        self.index_page = (
            'posts:index',
            None
        )
        self.group_page = (
            'posts:group_list',
            (PaginatorViewsTest.group.slug,)
        )
        self.profile_page = (
            'posts:profile',
            (PaginatorViewsTest.author,)
        )
        self.urls_pages = (
            self.index_page,
            self.group_page,
            self.profile_page,
        )
        self.posts_count = Post.objects.count()
        self.first_page_posts = 10
        self.next_page_posts = (
            self.posts_count - (2 - 1) * self.first_page_posts
        )
        self.pages = [
            (1, self.first_page_posts),
            (2, self.next_page_posts),
        ]
        cache.clear()

    def test_pages_paginate(self):
        """Проверка количество постов на страницах"""
        for name, args in self.urls_pages:
            for page, count in self.pages:
                with self.subTest(name=name):
                    response = self.authorized_client.get(
                        reverse(name, args=args), {'page': page}
                    )
                    self.assertEqual(
                        len(response.context.get('page_obj').object_list),
                        count
                    )


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug',
            description='Тестовое описание 1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 1',
            group=cls.group,
            image=cls.uploaded_image
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        cache.clear()
        self.guest_client = Client()
        self.index_page = (
            'posts:index',
            None
        )
        self.group_page = (
            'posts:group_list',
            (PostImageTests.group.slug,)
        )
        self.profile_page = (
            'posts:profile',
            (PostImageTests.user,)
        )
        self.post_detail_page = (
            'posts:post_detail',
            (PostImageTests.post.pk,)
        )
        self.urls = (
            self.index_page,
            self.group_page,
            self.profile_page,
            self.post_detail_page
        )

    def test_pages_with_image_show_correct_context(self):
        """В шаблон index, group, profile, post_detail
        передается изображение.
        """
        for page, args in self.urls:
            with self.subTest(page=page):
                if page != self.post_detail_page[0]:
                    response = self.guest_client.get(
                        reverse(page, args=args)
                    )
                    context_page = (
                        response.context.get('page_obj').object_list[0]
                    )
                    self.assertEqual(
                        context_page.image, PostImageTests.post.image
                    )
                else:
                    response = self.guest_client.get(
                        reverse(page, args=args)
                    )
                    context_page = response.context.get('post_user')
                    self.assertEqual(
                        context_page.image, PostImageTests.post.image
                    )
