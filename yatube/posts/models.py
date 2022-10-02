from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='название',
        max_length=200,
        help_text='назовите группу'
    )
    slug = models.SlugField(unique=True)
    description = models.TextField(
        verbose_name='описание',
        help_text='напишите, о чем группа'
    )

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='текст поста',
        help_text='напечататйте свой пост здесь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date', '-id')
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='исходный пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор коммента'
    )
    text = models.TextField(
        verbose_name='текст коммента',
        help_text='напечататйте свой коммент здесь'
    )

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='юзер'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='автор поста'
    )

    class Meta:
        constraints = (models.UniqueConstraint(fields=['user_id',
                                                       'author_id'],
                                               name='unique_following'),)

    def __str__(self):
        return self.user
