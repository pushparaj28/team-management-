from django.contrib import admin

from .models import (
    Resource,
    Bookmark,
    Comment,
)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'category',
        'uploaded_by',
        'views',
        'downloads',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'category',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'uploaded_by__username',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        'resource',
        'user',
        'created_at',
    )

    search_fields = (
        'text',
        'resource__title',
        'user__username',
    )


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'resource',
        'created_at',
    )