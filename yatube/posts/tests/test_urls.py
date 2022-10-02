from django.test import Client, TestCase

from posts.models import Group, Post, User

OK = 200
REDIRECT = 302
NOTFOUND = 404


class StaticURLTests(TestCase):
    def test_homepage(self):
        # Создаем экземпляр клиента
        guest_client = Client()
        # Делаем запрос к главной странице и проверяем статус
        response = guest_client.get('/')
        # Утверждаем, что для прохождения теста код должен быть равен 200
        self.assertEqual(response.status_code, OK)


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            # id=cls.id,
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
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

    """адреса  с ответами, темплейтами и редиректами для всех тестов
    маска  = адрес:[темплейт, ответ гостю, ответ авторизованному]"""
    ADDRESSES = {
        '/': ['posts/index.html', OK, OK],
        '/group/test-slug/': ['posts/group_list.html', OK, OK],
        '/profile/auth/': ['posts/profile.html', OK, OK],
        '/posts/1/': ['posts/post_detail.html', OK, OK],
        '/create/': ['posts/create_post.html', REDIRECT, OK],
        '/posts/1/edit/': ['posts/create_post.html', REDIRECT, REDIRECT],
        '/unexisting-page/': ['core/404.html', NOTFOUND, NOTFOUND]
    }

    def destinations(self):
        for address, meaning in TaskURLTests.ADDRESSES.items():
            response1 = self.guest_client.get(address)
            response2 = self.authorized_client.get(address)
            with self.subTest(meaning=meaning):
                self.assertEqual(response1.status_code, meaning[1])
                self.assertEqual(response2.status_code, meaning[2])

    def author_destination(self):
        address = '/posts/1/edit/'
        if self.authorized_client == 'auth':
            response = self.author.get(address)
            self.assertEqual(response.status_code, OK)
        response = self.authorized_client.get(address)
        self.assertEqual(response.status_code, REDIRECT)

    def guest_redirect(self):
        redirections = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': '/posts/1/'
        }
        for address, redirection in redirections.items():
            response = self.guest_client.get(address, follow=True)
            with self.subTest(redirection=redirection):
                self.assertRedirects(response, (redirection))

    def template_usage_check(self):

        for address, meaning in TaskURLTests.ADDRESSES.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, meaning[0])
