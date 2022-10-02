from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст поста',
                  'group': 'Группа',
                  'image': 'Изображение'}
        help_texts = {'text': 'Напишите что-нибудь',
                      'group': 'Выберите группу, если хотите',
                      'image': 'Добавьте картинку'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст коммента'}
        help_texts = {'text': 'Оставьте комментарий'}
