import shutil
import tempfile

from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='noname')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small1.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.image_2 = SimpleUploadedFile(
            name='small2.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост!',
            group=cls.group,
            image=cls.image_2,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostsFormTests.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsFormTests.user)
        self.create_page = (
            'posts:post_create',
            None
        )
        self.edit_page = (
            'posts:post_edit',
            PostsFormTests.post.id
        )
        self.profile_page = (
            'posts:profile',
            PostsFormTests.user
        )
        self.post_detail_page = (
            'posts:post_detail',
            PostsFormTests.post.id
        )
        self.add_comment_page = (
            'posts:add_comment',
            PostsFormTests.post.id
        )
        self.redirect_url = (
            reverse('users:login'),
            reverse('posts:post_create')
        )
        self.redirect_url_comment = (
            reverse('users:login'),
            reverse(
                'posts:add_comment',
                args=[PostsFormTests.post.id]
            )
        )

    def test_create_post(self):
        """Если форма валидна, создается новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostsFormTests.group.id,
            'image': PostsFormTests.image,
        }
        response = self.authorized_client.post(
            reverse(self.create_page[0]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(self.profile_page[0], args=[self.profile_page[1]])
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.get(
            author=PostsFormTests.user,
            text=form_data['text'],
            image=response.context.get('page_obj').object_list[0].image
        )
        self.assertEqual(new_post.author, PostsFormTests.user)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertTrue(new_post.image)

    def test_post_edit(self):
        """Если форма валидна, изменяется id поста."""
        post_edit = Post.objects.get(id=PostsFormTests.post.id)
        form_data = {
            'text': 'Тестовый пост 3',
            'group': PostsFormTests.group.id,
            'image': post_edit.image,
        }
        response = self.author_client.post(
            reverse(self.edit_page[0], args=[self.edit_page[1]]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(self.post_detail_page[0], args=[self.post_detail_page[1]])
        )
        new_post = Post.objects.get(
            id=self.edit_page[1],
            text=form_data['text'],
            image=response.context.get('post_user').image
        )
        self.assertNotEqual(post_edit.text, new_post.text)
        self.assertEqual(new_post.author, PostsFormTests.author)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertTrue(new_post.image)

    def test_guest_client_not_create_new_post(self):
        """Неавторизованный пользователь не может создать пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 4',
            'group': PostsFormTests.group.id
        }
        response = self.guest_client.post(
            reverse(self.create_page[0]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'{self.redirect_url[0]}?next={self.redirect_url[1]}'
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comment(self):
        """Комментарий создается авторизованным пользователем."""
        posts_comments = Post.objects.get(id=PostsFormTests.post.id)
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                self.add_comment_page[0], args=[self.add_comment_page[1]]
            ),
            data=form_data,
            follow=True
        )
        comment = posts_comments.comments.first()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(self.post_detail_page[0], args=[self.post_detail_page[1]])
        )
        self.assertEqual(comment.text, form_data['text'])

    def test_not_add_comment_guest(self):
        """Комментарий не создается неавторизованным пользователем."""
        posts_comments = Post.objects.get(id=PostsFormTests.post.id)
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.guest_client.post(
            reverse(self.add_comment_page[0], args=[self.add_comment_page[1]]),
            data=form_data,
            follow=True
        )
        comment = posts_comments.comments.first()
        self.assertFalse(comment, False)
        self.assertRedirects(
            response,
            f'{self.redirect_url_comment[0]}'
            f'?next={self.redirect_url_comment[1]}'
        )
