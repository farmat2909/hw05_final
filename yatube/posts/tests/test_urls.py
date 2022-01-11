from http import HTTPStatus
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.guest_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author}/', 'posts/profile.html'),
            (f'/posts/{cls.post.pk}/', 'posts/post_detail.html'),
        )
        cls.author_urls = (
            f'/posts/{cls.post.pk}/edit/', 'posts/create_post.html'
        )
        cls.authorized_urls = (
            ('/create/', 'posts/create_post.html'),
            ('/follow/', 'posts/follow.html')
        )
        cls.unexisting_urls = ('/unexisting_page/',)
        cls.redirects_urls = (
            ('/create/', '/auth/login/?next=/create/'),
            ('/follow/', '/auth/login/?next=/follow/'),
            (f'/posts/{cls.post.pk}/edit/',
             f'/auth/login/?next=/posts/{cls.post.pk}/edit/')
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_exists_and_uses_correct_template_for_guest(self):
        """Страницы доступны гостю,
        используется правильный шаблон.
        """
        urls_templates_guest = (*PostsURLTests.guest_urls,)
        for url, template in urls_templates_guest:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_and_uses_correct_template_for_author(self):
        """Страницы доступны автору,
        используется правильный шаблон.
        """
        urls_templates_author = (
            *PostsURLTests.guest_urls,
            PostsURLTests.author_urls,
            *PostsURLTests.authorized_urls
        )
        for url, template in urls_templates_author:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_and_uses_correct_template_for_authorized(self):
        """Страницы доступны авторизованному пользователю,
        используется правильный шаблон.
        """
        urls_templates_authorized = (
            *PostsURLTests.guest_urls,
            *PostsURLTests.authorized_urls
        )
        for url, template in urls_templates_authorized:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_guest_on_login(self):
        """Страницы перенаправят анонимного пользователя
        на страницу login.
        """
        urls_redirects = (*PostsURLTests.redirects_urls,)
        for url, redirect_url in urls_redirects:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)
