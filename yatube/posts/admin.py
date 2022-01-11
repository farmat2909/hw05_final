from django.contrib import admin

from .models import Comment, Follow, Group, Post


class BaseAdminSettings(admin.ModelAdmin):
    """Базовая кастомизация админ панели."""
    empty_value_display = '-пусто-'


class PostAdmin(BaseAdminSettings):
    """Кастомизация admin панели (управление постами)."""
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = (
        'pub_date',
        ('author', admin.RelatedOnlyFieldListFilter)
    )
    list_editable = ('group',)


class GroupAdmin(BaseAdminSettings):
    """Кастомизация admin панели (управление группами)."""
    list_display = ('title', 'description', 'slug')
    search_fields = ('title',)
    prepopulated_fields = {"slug": ("title",)}


class CommentAdmin(BaseAdminSettings):
    """Кастомизация admin панели (управление комментариями)."""
    list_display = ('post', 'author', 'text', 'created')
    search_fields = ('text',)
    list_filter = ('author',)


class FollowAdmin(BaseAdminSettings):
    """Кастомизация admin панели (управление подписчиками)."""
    list_display = ('user', 'author')
    search_fields = ('author',)
    list_filter = ('author',)


admin.site.register(Post, PostAdmin)

admin.site.register(Group, GroupAdmin)

admin.site.register(Comment, CommentAdmin)

admin.site.register(Follow, FollowAdmin)
