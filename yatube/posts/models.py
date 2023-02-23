from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Group name',
        max_length=200,
        help_text='Name the group'
    )
    slug = models.SlugField(unique=True)
    description = models.TextField(
        verbose_name='description',
        help_text='What is this group about'
    )

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Post text',
        help_text='Write your post here'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Post author'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Group',
        help_text='Choose a group for the post'
    )
    image = models.ImageField(
        'Image',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date', '-id')
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Initial post'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Comment author'
    )
    text = models.TextField(
        verbose_name='Comment text',
        help_text='Write your comment here'
    )

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='User'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Post author'
    )

    class Meta:
        constraints = (models.UniqueConstraint(fields=('user_id',
                                                       'author_id'),
                                               name='unique_following'),)

    def __str__(self):
        return self.user
