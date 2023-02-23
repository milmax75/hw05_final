from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Post text',
                  'group': 'Group',
                  'image': 'Image'}
        help_texts = {'text': 'Write your post here',
                      'group': 'Choose a group. Optional',
                      'image': 'Add an image'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Comment text'}
        help_texts = {'text': 'Please comment the post'}
