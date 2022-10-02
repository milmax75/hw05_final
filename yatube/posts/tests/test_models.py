# from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name2 = group.title
        self.assertEqual(expected_object_name2, str(group))
        post = PostModelTest.post
        expected_object_name1 = post.text
        self.assertEqual(expected_object_name1, str(post))

    def test_verbose_names(self):
        """проверяем корректность вербоуз имен"""
        field_verboses = {
            'author': 'автор поста',
            'text': 'текст поста',
            'pub_date': 'Дата создания',
            'group': 'Группа'
        }
        for field_name, expected_value in field_verboses.items():
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    Post._meta.get_field(field_name).verbose_name,
                    expected_value
                )
