import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author = Client()
        self.user2 = User.objects.get(username='auth')
        self.author.force_login(self.user2)

    def test_сreate_post(self):
        post_count = Post.objects.count()
        url = reverse('posts:post_create')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'новый проверочный пост',
            'group': 1,
            'image': uploaded,
        }
        response = self.author.post(url, data=form_data, follow=True)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(
            Post.objects.get(id=2).text,
            'новый проверочный пост'
        )
        self.assertEqual(Post.objects.get(id=2).group.id, 1)
        self.assertEqual(Post.objects.get(id=2).author.username, 'auth')
        self.assertEqual(Post.objects.get(id=2).image, 'posts/small.gif')
        self.assertTrue(
            Post.objects.filter(
                text='новый проверочный пост',
                group=1,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        post_count = Post.objects.count()
        url = reverse('posts:post_edit', kwargs={'post_id': '1'})
        self.author.get(url)
        response = self.author.post(
            url,
            {'text': 'Изменяем тестовый текст', 'group': 1}
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(
            Post.objects.get(id=1).text,
            'Изменяем тестовый текст'
        )
        self.assertEqual(Post.objects.get(id=1).group.title, 'Тестовая группа')
        self.assertEqual(Post.objects.get(id=1).author.username, 'auth')
