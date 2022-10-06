import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group1 = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Пустая группа',
            slug='empty-slug',
            description='Группа создана для доп проверки'
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        test_posts = [(
            Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group1,
                image=SimpleUploadedFile(
                    name=f'small{i}.gif',
                    content=small_gif,
                    content_type='image/gif'
                )
            )
        ) for i in range(12)]

        cache.clear()
        cls.post = Post.objects.bulk_create(test_posts)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

        self.author = Client()
        self.user2 = User.objects.get(username='auth')
        self.author.force_login(self.user2)

    def test_pages_uses_correct_template(self):
        pages_to_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/create_post.html',
        }
        cache.clear()
        for page, template in pages_to_templates.items():
            with self.subTest(address=page):
                response = self.author.get(page)
                self.assertTemplateUsed(response, template)

    def test_homepage_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertQuerysetEqual(response.context['page_obj'],
                                 [repr(r) for r in Post.objects.all()[:10]])
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'Тестовый пост 11')
        self.assertEqual(first_object.author.username, 'auth')
        self.assertEqual(first_object.image, 'posts/small11.gif')

    def test_profile_page_context(self):
        response = (
            self.authorized_client.get(reverse('posts:profile',
                                       kwargs={'username': 'auth'}))
        )
        self.assertEqual(response.context.get('post').author.username, 'auth')
        self.assertQuerysetEqual(
            response.context['page_obj'],
            [repr(r) for r in Post.objects.select_related('author').all()[:10]]
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'Тестовый пост 11')
        self.assertEqual(first_object.author.username, 'auth')
        self.assertEqual(first_object.image, 'posts/small11.gif')

    def test_group_page_context(self):
        response = (
            self.authorized_client.get(reverse('posts:group',
                                       kwargs={'slug': 'test-slug'}))
        )
        self.assertEqual(
            response.context.get('post').group.title,
            'Тестовая группа'
        )
        self.assertQuerysetEqual(
            response.context['page_obj'],
            [repr(r) for r in Post.objects.select_related('group').all()[:10]]
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'Тестовый пост 11')
        self.assertEqual(first_object.author.username, 'auth')
        self.assertEqual(first_object.image, 'posts/small11.gif')

    def test_create_page_field_types(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_field_types(self):
        response = self.author.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_post_number(self):
        response = self.author.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        self.assertEqual(response.context['post'].id, 1)

    def test_detail_page_context(self):
        response = self.author.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        post_cntxt = response.context['post']
        post_fields = {
            post_cntxt.id: 1,
            post_cntxt.text: 'Тестовый пост 0',
            post_cntxt.author.username: 'auth',
            post_cntxt.group.title: 'Тестовая группа',
            post_cntxt.image: 'posts/small0.gif'
        }
        for post_field, meaning in post_fields.items():
            with self.subTest(post_field=post_field):
                self.assertEqual(post_field, meaning)

    def test_first_page_paginators(self):
        cache.clear()
        pages = [
            reverse('posts:index'),
            reverse('posts:group', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_paginators(self):
        cache.clear()
        pages = [
            reverse('posts:index') + '?page=2',
            reverse('posts:group', kwargs={'slug': 'test-slug'}) + '?page=2',
            reverse('posts:profile', kwargs={'username': 'auth'}) + '?page=2'
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context['page_obj']), 2)

    def test_post_creation(self):
        cache.clear()
        url = reverse('posts:post_create')
        self.author.post(url, {'text': 'новый проверочный пост', 'group': 2})
        pages = [
            reverse('posts:index'),
            reverse('posts:group', kwargs={'slug': 'empty-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.author.get(page)
                self.assertIn(Post.objects.get(id=13),
                              response.context['page_obj'])

        response2 = self.author.get(
            reverse('posts:group', kwargs={'slug': 'test-slug'})
        )
        self.assertNotIn(
            Post.objects.get(id=13),
            response2.context['page_obj']
        )

    def test_comment_creation(self):
        url = reverse('posts:add_comment', kwargs={'post_id': '1'})
        self.authorized_client.post(url, {
                                    'text': 'проверочный коммент', })
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(
            Comment.objects.get(id=1).text, 'проверочный коммент'
        )
        self.assertIn(Comment.objects.get(id=1), response.context['comments'])

    def test_guest_comment(self):
        url = reverse('posts:add_comment', kwargs={'post_id': '1'})
        self.guest_client.post(url, {'text': 'коммент гостя', })
        self.assertEqual(Comment.objects.count(), 0)

    def test_cache(self):
        url = reverse('posts:post_create')
        self.author.post(url, {'text': 'пост проверки кэша', 'group': 2})
        cache.clear()
        page = reverse('posts:index')
        response1 = self.authorized_client.get(page)
        Post.objects.get(text='пост проверки кэша').delete()
        response2 = self.authorized_client.get(page)
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(page)
        self.assertNotEqual(response1.content, response3.content)


class FollowViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='HasNoName')
        cls.user2 = User.objects.create_user(username='auth')
        cls.following = Follow.objects.create(user=cls.user1,
                                              author=cls.user2)

    def setUp(self):
        self.author = Client()
        self.user3 = User.objects.get(username='auth')
        self.author.force_login(self.user3)
        self.follower = Client()
        self.user4 = User.objects.get(username='HasNoName')
        self.follower.force_login(self.user4)

    def test_follow_unfollow(self):
        self.assertTrue(Follow.objects.filter(user=self.user1,
                                              author=self.user2).exists())
        page = reverse('posts:profile_unfollow', kwargs={'username': 'auth'})
        self.follower.get(page)
        self.assertFalse(Follow.objects.filter(user=self.user1,
                                               author=self.user2).exists())

    def test_message_show(self):
        url = reverse('posts:post_create')
        self.author.post(url, {'text': 'проверка подписки', })
        page = reverse('posts:follow_index')
        non_follower_resp = self.author.get(page)
        follower_resp = self.follower.get(page)
        self.assertIn(Post.objects.get(text='проверка подписки'),
                      follower_resp.context['page_obj'])
        self.assertNotIn(Post.objects.get(text='проверка подписки'),
                         non_follower_resp.context['page_obj'])

    def test_unique_follow(self):
        try:
            Follow.objects.create(user=self.user1, author=self.user2)
        except IntegrityError:
            print('second record not created')
