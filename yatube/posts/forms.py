from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования постов."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = 'Группа не выбрана'

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст', 'group': 'Группа'}
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }


class CommentForm(forms.ModelForm):
    """Форма для добавления комментариев постов."""
    class Meta:
        model = Comment
        fields = ('text',)
